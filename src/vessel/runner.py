import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import yaml

from vessel.adapters.base import ArtifactStore, Budget, Context, ReplayProvider
from vessel.adapters.evidence8 import Evidence8
from vessel.adapters.hybrid import KeenableEvidence8
from vessel.adapters.web import Exa, Keenable, Serper
from vessel.artifacts import atomic_json
from vessel.datasets import dataset_digest, load_dataset, validate_dataset
from vessel.extraction import extract_document
from vessel.identity import canonical_url
from vessel.models import Protocol, RunConfig, RunManifest, SearchResponse, digest

ROOT = Path(__file__).resolve().parents[2]


def code_payload() -> dict:
    return {str(p.relative_to(ROOT)): p.read_text() for p in sorted((ROOT / "src").rglob("*.py"))}


def code_digest() -> str:
    return digest(code_payload())


def dependency_lock_digest() -> str | None:
    path = ROOT / "uv.lock"
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def load_config(path: Path) -> RunConfig:
    return RunConfig.model_validate(yaml.safe_load(path.read_text()))


def providers_for(config: RunConfig, fixture: Path | None):
    by_name = {p.name: p for p in config.providers}
    providers = {}
    for setting in config.providers:
        if fixture:
            provider = ReplayProvider(setting.name, fixture)
        elif setting.name == "keenable_evidence8":
            if "keenable" not in by_name or "evidence8" not in by_name:
                raise ValueError("hybrid requires keenable and evidence8 cost/config entries")
            if config.protocol != Protocol.EVIDENCE:
                raise ValueError(
                    "hybrid is only eligible for the separately reported evidence protocol"
                )
            provider = KeenableEvidence8(by_name["keenable"], by_name["evidence8"])
        else:
            provider = {"evidence8": Evidence8, "keenable": Keenable, "exa": Exa, "serper": Serper}[
                setting.name
            ](setting)
        profile_names = (
            ["keenable", "evidence8"] if setting.name == "keenable_evidence8" else [setting.name]
        )
        if not all((ROOT / "docs/providers" / f"{name}.md").exists() for name in profile_names):
            raise ValueError("provider characterization missing")
        providers[setting.name] = provider
    return providers


def receipt_path(root: Path, provider: str, query_id: str) -> Path:
    return root / "responses" / (digest([provider, query_id]) + ".json")


def read_receipt(path: Path) -> dict:
    receipt = json.loads(path.read_text())
    expected = receipt.pop("sha256")
    if digest(receipt) != expected:
        raise ValueError("response receipt integrity mismatch")
    SearchResponse.model_validate(receipt["response"])
    return receipt


def run(
    dataset_path: Path,
    config_path: Path,
    output: Path,
    fixture: Path | None = None,
    resume: bool = False,
    client: httpx.Client | None = None,
) -> RunManifest:
    records = load_dataset(dataset_path)
    issues = validate_dataset(records)
    if issues:
        raise ValueError("; ".join(issues))
    config = load_config(config_path)
    providers = providers_for(config, fixture)
    identity = {
        "dataset_sha256": dataset_digest(records),
        "config_sha256": digest(config),
        "code_sha256": code_digest(),
        "dependency_lock_sha256": dependency_lock_digest(),
        "mode": "replay" if fixture else "live",
    }
    path = output / "manifest.json"
    if path.exists():
        if not resume:
            raise ValueError("output already contains a run; use --resume or a fresh directory")
        manifest = RunManifest.model_validate_json(path.read_text())
        if any(getattr(manifest, key) != value for key, value in identity.items()):
            raise ValueError(
                "resume requires identical dataset, configuration, code, dependency lock and mode"
            )
    else:
        manifest = RunManifest(
            run_id=digest(identity)[:16],
            benchmark_version=config.benchmark_version,
            config=config,
            started_at=datetime.now(UTC),
            **identity,
            dataset_release_ready=not validate_dataset(records, release=True),
            freeze_attestations=[r.attestation for r in records],
        )
        manifest.code_artifact_sha256 = ArtifactStore(output / "objects").put_bytes(
            json.dumps(code_payload(), sort_keys=True, separators=(",", ":")).encode()
        )
        if (ROOT / "uv.lock").exists():
            manifest.dependency_lock_sha256 = ArtifactStore(output / "objects").put_bytes(
                (ROOT / "uv.lock").read_bytes()
            )
        atomic_json(path, manifest)
        atomic_json(output / "dataset.json", [r.model_dump(mode="json") for r in records])
    budget = Budget(
        config.max_cost_usd, config.max_requests, manifest.requests, manifest.reserved_cost_usd
    )
    store = ArtifactStore(output / "objects")
    owns_client = client is None
    client = client or httpx.Client(headers={"User-Agent": "VESSEL/0.1 research benchmark"})
    context = Context(budget, store, client)
    try:
        for provider_name, provider in providers.items():
            for record in records:
                cell_path = receipt_path(output, provider_name, record.query_id)
                if cell_path.exists():
                    receipt = read_receipt(cell_path)
                    budget.requests = max(budget.requests, receipt["cumulative_requests"])
                    budget.reserved_usd = max(
                        budget.reserved_usd, receipt["cumulative_reserved_usd"]
                    )
                    if any(
                        o["status"] == "ceiling_underestimated"
                        for o in receipt["response"]["observations"]
                    ):
                        budget.max_requests = budget.requests
                    continue
                # Persist before transmission so crashes cannot reset paid-call accounting.
                original_reserve = budget.reserve

                def persist_reservation(ceiling, reserve=original_reserve):
                    reserve(ceiling)
                    manifest.requests = budget.requests
                    manifest.reserved_cost_usd = budget.reserved_usd
                    atomic_json(path, manifest)

                budget.reserve = persist_reservation
                start = time.perf_counter()
                before_requests = budget.requests
                response = provider.search(record.query, config.k, context)
                if (
                    config.protocol == Protocol.SEARCH_FETCH
                    and response.status == "ok"
                    and not fixture
                ):
                    seen = set()
                    for result in response.results:
                        url = canonical_url(result.url)
                        if not url or url in seen:
                            continue
                        seen.add(url)
                        if len(seen) > config.fetch.max_documents:
                            break
                        bundles, observations = extract_document(url, context, config.fetch)
                        result.bundles.extend(bundles)
                        response.observations.extend(observations)
                    response.latency_ms = (time.perf_counter() - start) * 1000
                budget.reserve = original_reserve
                response.requests = budget.requests - before_requests
                receipt = {
                    "provider": provider_name,
                    "query_id": record.query_id,
                    "response": response.model_dump(mode="json"),
                    "cumulative_requests": budget.requests,
                    "cumulative_reserved_usd": budget.reserved_usd,
                }
                receipt["sha256"] = digest(receipt)
                atomic_json(cell_path, receipt)
                manifest.requests = budget.requests
                manifest.reserved_cost_usd = budget.reserved_usd
                atomic_json(path, manifest)
        cells = [
            read_receipt(receipt_path(output, p, r.query_id)) for p in providers for r in records
        ]
        complete = all(
            c["response"]["status"] in {"ok", "no_match"}
            and not any(
                o["status"] in {"incomplete", "ceiling_underestimated", "BudgetExceeded"}
                for o in c["response"]["observations"]
            )
            for c in cells
        )
        manifest.status = "complete" if complete else "incomplete"
        manifest.completed_at = datetime.now(UTC)
        # A complete run still needs a human audit before public release.
        manifest.publication_eligible = False
        atomic_json(path, manifest)
        return manifest
    finally:
        if owns_client:
            client.close()
