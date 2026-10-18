"""Blinded adjudication packets.

Human adjudication of ambiguous visual equivalence must not know which
engine produced a bundle. Receipts store the engine name in plaintext, so
adjudicators work from blinded packets instead of raw receipts:

- every engine gets a random blind ID; the blind-ID -> engine mapping is
  sealed until adjudications are recorded;
- packets carry the full bundle content (source provenance preserved:
  document URLs, publishers, visual URLs, locations, datasets, rights)
  plus the query and gold alternatives;
- stripped from packets: engine name, provider result IDs, rank/position,
  latency, cost;
- each packet is keyed by the opaque ``bundle_sha256`` the scorer uses,
  so recorded adjudications join back without revealing the engine.
"""

import json
import secrets
from pathlib import Path

from vessel.models import SearchResponse, digest
from vessel.runner import read_receipt, receipt_path

SEALED_README = """# Sealed engine mapping

Do not open until adjudications are recorded.

This directory maps blind engine IDs (as seen in packets.jsonl) to the
real engine names. Opening it before adjudication is complete breaks the
blinding and invalidates the adjudication round: any decisions recorded
after exposure must be discarded and the round repeated with fresh blind
IDs.

Procedure:
1. Adjudicators record decisions keyed by bundle_sha256 only.
2. When every assigned packet has a recorded decision, open mapping.json.
3. Attribute decisions to engines for reporting.
"""


def _blind_id(existing: set[str]) -> str:
    while True:
        candidate = "engine-" + secrets.token_hex(3)
        if candidate not in existing:
            return candidate


def blind_run(run_dir: Path, output_dir: Path) -> dict:
    """Export blinded adjudication packets for a completed run directory."""
    run_dir = Path(run_dir)
    output_dir = Path(output_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    records = {
        r["query_id"]: r for r in json.loads((run_dir / "dataset.json").read_text())
    }
    provider_names = [p["name"] for p in manifest["config"]["providers"]]

    blind_ids: dict[str, str] = {}
    for name in provider_names:
        blind_ids[name] = _blind_id(set(blind_ids.values()))

    packets: list[dict] = []
    for provider_name in provider_names:
        engine_blind = blind_ids[provider_name]
        for query_id, record in records.items():
            path = receipt_path(run_dir, provider_name, query_id)
            if not path.exists():
                continue
            receipt = read_receipt(path)
            response = SearchResponse.model_validate(receipt["response"])
            if response.status != "ok":
                continue
            for result in response.results or []:
                for bundle in result.bundles or []:
                    packets.append(
                        {
                            "packet_id": f"pkt-{len(packets):05d}",
                            "query_id": query_id,
                            "engine_blind": engine_blind,
                            "bundle_sha256": digest(bundle),
                            "result_context": {
                                "title": result.title,
                                "url": str(result.url)
                                if result.url is not None
                                else None,
                                "snippet": result.snippet,
                            },
                            "bundle": bundle.model_dump(mode="json"),
                        }
                    )

    queries = {
        query_id: {
            "query": record["query"],
            "alternatives": record["alternatives"],
        }
        for query_id, record in records.items()
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    sealed = output_dir / "sealed"
    sealed.mkdir(exist_ok=True)
    (output_dir / "packets.jsonl").write_text(
        "".join(json.dumps(p, sort_keys=True) + "\n" for p in packets)
    )
    (output_dir / "queries.json").write_text(
        json.dumps(queries, indent=2, sort_keys=True)
    )
    (sealed / "mapping.json").write_text(
        json.dumps(
            {blind: name for name, blind in blind_ids.items()},
            indent=2,
            sort_keys=True,
        )
    )
    (sealed / "README.md").write_text(SEALED_README)
    summary = {
        "providers": len(provider_names),
        "queries": len(records),
        "packets": len(packets),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary
