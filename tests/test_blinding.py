import json

from vessel.blinding import blind_run
from vessel.models import (
    Asset,
    Bundle,
    EvidenceResult,
    SearchResponse,
    Source,
    digest,
)
from vessel.runner import receipt_path


def _receipt(provider: str, query_id: str, n_bundles: int) -> dict:
    bundles = [
        Bundle(
            source=Source(document_url=f"https://example.com/doc-{i}"),
            visual=Asset(url=f"https://example.com/vis-{i}.png"),
        )
        for i in range(n_bundles)
    ]
    response = SearchResponse(
        status="ok",
        results=[
            EvidenceResult(
                rank=1,
                provider_id=f"{provider}-result-1",
                title="t",
                url="https://example.com/doc-0",
                bundles=bundles,
            )
        ],
    )
    receipt = {
        "provider": provider,
        "query_id": query_id,
        "response": response.model_dump(mode="json"),
        "cumulative_requests": 1,
        "cumulative_reserved_usd": 0.01,
    }
    receipt["sha256"] = digest({k: v for k, v in receipt.items()})
    return receipt


def _run_dir(tmp_path) -> object:
    run_dir = tmp_path / "run"
    (run_dir / "responses").mkdir(parents=True)
    manifest = {
        "config": {
            "providers": [{"name": "exa"}, {"name": "serper"}],
        }
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    dataset = [
        {
            "query_id": "q1",
            "query": "unemployment chart",
            "alternatives": [{"evidence_id": "e1"}],
        }
    ]
    (run_dir / "dataset.json").write_text(json.dumps(dataset))
    for provider in ("exa", "serper"):
        receipt = _receipt(provider, "q1", 2)
        (receipt_path(run_dir, provider, "q1")).write_text(json.dumps(receipt))
    return run_dir


def test_blind_run_seals_engine_identities(tmp_path):
    run_dir = _run_dir(tmp_path)
    out = tmp_path / "blind"
    summary = blind_run(run_dir, out)

    assert summary == {"providers": 2, "queries": 1, "packets": 4}

    packets = [
        json.loads(line) for line in (out / "packets.jsonl").read_text().splitlines()
    ]
    assert len(packets) == 4
    blind_ids = {p["engine_blind"] for p in packets}
    assert len(blind_ids) == 2  # one blind id per engine, consistent within engine

    raw = (out / "packets.jsonl").read_text()
    assert "exa" not in raw.replace("example.com", "")
    assert "serper" not in raw

    for packet in packets:
        # Engine-identifying fields are stripped; provenance is preserved.
        assert "provider_id" not in json.dumps(packet["result_context"])
        assert "rank" not in packet["result_context"]
        assert packet["bundle"]["source"]["document_url"].startswith("https://example.com/")
        assert packet["bundle"]["visual"]["url"].startswith("https://example.com/")
        # The packet key matches the scorer's bundle digest.
        bundle = Bundle.model_validate(packet["bundle"])
        assert packet["bundle_sha256"] == digest(bundle)

    mapping = json.loads((out / "sealed" / "mapping.json").read_text())
    assert set(mapping.values()) == {"exa", "serper"}
    assert set(mapping) == blind_ids
    assert (out / "sealed" / "README.md").read_text().startswith("# Sealed engine mapping")


def test_blind_ids_are_random_per_run(tmp_path):
    run_dir = _run_dir(tmp_path)
    first = blind_run(run_dir, tmp_path / "a")
    second = blind_run(run_dir, tmp_path / "b")
    assert first["packets"] == second["packets"] == 4
    map_a = json.loads((tmp_path / "a" / "sealed" / "mapping.json").read_text())
    map_b = json.loads((tmp_path / "b" / "sealed" / "mapping.json").read_text())
    # Random per invocation: re-running must not reproduce the same blind ids.
    assert set(map_a) != set(map_b)
