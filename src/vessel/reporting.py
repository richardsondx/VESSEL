import json
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

from vessel.artifacts import ArtifactStore, atomic_json, sanitize
from vessel.models import Adjudication, GoldRecord, RunManifest, SearchResponse, digest
from vessel.runner import read_receipt, receipt_path
from vessel.scoring import COMPONENTS, score_query


def percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    at = (len(values) - 1) * p
    lo = int(at)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (at - lo)


def family_bootstrap(items: list[tuple[str, float]], seed=17, samples=1000) -> list[float] | None:
    groups = defaultdict(list)
    for family, value in items:
        groups[family].append(value)
    if len(groups) < 2:
        return None
    rng = random.Random(seed)
    families = sorted(groups)
    means = []
    for _ in range(samples):
        values = [v for f in rng.choices(families, k=len(families)) for v in groups[f]]
        means.append(sum(values) / len(values))
    return [percentile(means, 0.025), percentile(means, 0.975)]


def aggregate(cells: list[dict], k: int, seed: int):
    statuses = Counter(c["response"]["status"] for c in cells)
    # Errors remain failures; skips/budget exhaustion also prevent a complete comparison.
    n = len(cells)

    def metric(name):
        return sum(c["scores"][str(k)]["components"][name] for c in cells) / n if n else None

    data_cells = [
        c
        for c in cells
        if any(g["data_available"] and g["datasets"] for g in c["gold"]["alternatives"])
    ]
    full = [float(c["scores"][str(k)]["full_support"]) for c in cells]
    latencies = [
        c["response"]["latency_ms"]
        for c in cells
        if c["response"]["latency_ms"] is not None and not c["response"]["replay"]
    ]
    return {
        "queries": n,
        "statuses": dict(statuses),
        "full_support": sum(full) / n if n else None,
        "full_support_ci95": family_bootstrap(
            [(c["gold"]["family_id"], v) for c, v in zip(cells, full, strict=True)], seed
        ),
        "components": {name: metric(name) for name in COMPONENTS if name != "data"},
        "data_recall": sum(c["scores"][str(k)]["components"]["data"] for c in data_cells)
        / len(data_cells)
        if data_cells
        else None,
        "data_denominator": len(data_cells),
        "supplemental": {
            name: {
                "denominator": len(
                    eligible := [
                        c
                        for c in cells
                        if any(
                            g["accepted_rights"] if name == "rights" else g[name]["urls"]
                            for g in c["gold"]["alternatives"]
                        )
                    ]
                ),
                "recall": sum(c["scores"][str(k)]["components"][name] for c in eligible)
                / len(eligible)
                if eligible
                else None,
            }
            for name in ("rights", "methodology", "reproducibility")
        },
        "mrr": sum(c["scores"][str(k)]["reciprocal_rank"] for c in cells) / n if n else None,
        "median_latency_ms": percentile(latencies, 0.5) if latencies else None,
        "reserved_cost_usd": sum(c["response"]["reserved_cost_usd"] for c in cells),
        "reported_cost_usd": sum(c["response"]["reported_cost_usd"] for c in cells)
        if cells and all(c["response"]["reported_cost_usd"] is not None for c in cells)
        else None,
        "failures": dict(
            Counter(c["scores"][str(k)]["failure"] for c in cells if c["scores"][str(k)]["failure"])
        ),
    }


def generate_report(
    root: Path, output: Path | None = None, adjudications: list[Adjudication] | None = None
) -> dict:
    manifest = RunManifest.model_validate_json((root / "manifest.json").read_text())
    records = [
        GoldRecord.model_validate(r) for r in json.loads((root / "dataset.json").read_text())
    ]
    from vessel.auditing import audit_valid
    from vessel.datasets import dataset_digest, validate_dataset

    if digest(manifest.config) != manifest.config_sha256:
        raise ValueError("archived configuration digest mismatch")
    store = ArtifactStore(root / "objects")
    if manifest.code_artifact_sha256:
        archived_code = json.loads(store.read(manifest.code_artifact_sha256))
        if digest(archived_code) != manifest.code_sha256:
            raise ValueError("archived code digest mismatch")
    if manifest.dependency_lock_sha256:
        store.read(manifest.dependency_lock_sha256)
    if dataset_digest(records) != manifest.dataset_sha256:
        raise ValueError("archived dataset digest mismatch")
    manifest.publication_eligible = bool(
        manifest.mode == "live"
        and manifest.status == "complete"
        and not validate_dataset(records, release=True)
        and audit_valid(root, manifest, records)
        and not adjudications  # New semantic decisions require a new documented evaluation/audit.
    )
    cells = []
    ks = [k for k in (1, 5, 10) if k <= manifest.config.k]
    for setting in manifest.config.providers:
        for record in records:
            path = receipt_path(root, setting.name, record.query_id)
            raw = (
                read_receipt(path)["response"]
                if path.exists()
                else {"status": "error", "reason": "missing receipt"}
            )
            response = SearchResponse.model_validate(raw)
            cells.append(
                {
                    "provider": setting.name,
                    "query_id": record.query_id,
                    "gold": record.model_dump(mode="json"),
                    "response": response.model_dump(mode="json"),
                    "scores": {
                        str(k): score_query(record, response.results, k, adjudications) for k in ks
                    },
                }
            )
    summary = {}
    for setting in manifest.config.providers:
        selected = [c for c in cells if c["provider"] == setting.name]
        summary[setting.name] = {str(k): aggregate(selected, k, manifest.config.seed) for k in ks}
    breakdowns = {}
    for field in ("domain", "visual_type", "query_type", "split", "membership"):

        def group(cell, field=field):
            return (
                cell["gold"]["attestation"]["bucket"]
                if field == "membership"
                else cell["gold"][field]
            )

        breakdowns[field] = {
            value: {
                p: aggregate(
                    [c for c in cells if c["provider"] == p and group(c) == value],
                    ks[-1],
                    manifest.config.seed,
                )
                for p in summary
            }
            for value in sorted({group(c) for c in cells})
        }
    pairs = []
    names = list(summary)
    # Paired reports require every requested cell; no silently reduced query population.
    if manifest.status == "complete" and all(
        c["response"]["status"] in {"ok", "no_match"} for c in cells
    ):
        for i, first in enumerate(names):
            for second in names[i + 1 :]:
                for k in ks:
                    diffs = []
                    for record in records:
                        a = next(
                            c
                            for c in cells
                            if c["provider"] == first and c["query_id"] == record.query_id
                        )
                        b = next(
                            c
                            for c in cells
                            if c["provider"] == second and c["query_id"] == record.query_id
                        )
                        diffs.append(
                            (
                                record.family_id,
                                float(a["scores"][str(k)]["full_support"])
                                - float(b["scores"][str(k)]["full_support"]),
                            )
                        )
                    pairs.append(
                        {
                            "first": first,
                            "second": second,
                            "k": k,
                            "difference": sum(v for _, v in diffs) / len(diffs),
                            "ci95": family_bootstrap(diffs, manifest.config.seed),
                        }
                    )
    report = sanitize(
        {
            "schema_version": "vessel.report.v1",
            "manifest": manifest.model_dump(mode="json"),
            "notice": "SYNTHETIC SOFTWARE FIXTURE — NOT PROVIDER PERFORMANCE"
            if manifest.mode == "replay"
            else "DEVELOPMENT RUN — NOT VALIDATED CORE-100"
            if not manifest.publication_eligible
            else "Validated Core-100 run",
            "summary": summary,
            "breakdowns": breakdowns,
            "paired": pairs,
            "cells": cells,
            "adjudications": [a.model_dump(mode="json") for a in adjudications or []],
        },
        tuple(
            value
            for name, value in os.environ.items()
            if name
            in {
                "EVIDENCE8_API_KEY",
                "KEENABLE_API_KEY",
                "EXA_API_KEY",
                "SERPER_API_KEY",
                "EVIDENCE8_BASE_URL",
            }
            and value
        ),
    )
    atomic_json(output or root / "report.json", report)
    return report


def compare_reports(first: dict, second: dict) -> list[dict]:
    a, b = first["manifest"], second["manifest"]
    for key in ("benchmark_version", "dataset_sha256", "mode"):
        if a[key] != b[key]:
            raise ValueError(f"comparison mismatch: {key}")
    for key in ("protocol", "k", "fetch"):
        if a["config"][key] != b["config"][key]:
            raise ValueError(f"comparison mismatch: {key}")
    if any(m["status"] != "complete" for m in (a, b)):
        raise ValueError("incomplete runs cannot be compared")
    results = []
    for p in first["summary"]:
        for q in second["summary"]:
            for k in first["summary"][p]:
                ac = {c["query_id"]: c for c in first["cells"] if c["provider"] == p}
                bc = {c["query_id"]: c for c in second["cells"] if c["provider"] == q}
                if ac.keys() != bc.keys():
                    raise ValueError("query populations differ")
                if any(
                    c["response"]["status"] not in {"ok", "no_match"}
                    for c in [*ac.values(), *bc.values()]
                ):
                    raise ValueError("comparison includes failed or skipped cells")
                diffs = [
                    (
                        ac[id]["gold"]["family_id"],
                        float(ac[id]["scores"][k]["full_support"])
                        - float(bc[id]["scores"][k]["full_support"]),
                    )
                    for id in sorted(ac)
                ]
                results.append(
                    {
                        "first": p,
                        "second": q,
                        "k": int(k),
                        "difference": sum(v for _, v in diffs) / len(diffs),
                        "ci95": family_bootstrap(diffs, a["config"]["seed"]),
                    }
                )
    return results
