import json

from vessel.adapters.base import Budget, Context
from vessel.adapters.captured import CapturedResultsProvider
from vessel.artifacts import ArtifactStore
from vessel.models import ProviderConfig


def _context():
    import httpx
    import tempfile
    from pathlib import Path

    return Context(
        budget=Budget(max_usd=20.0, max_requests=100),
        artifacts=ArtifactStore(Path(tempfile.mkdtemp())),
        # trust_env=False: the sandbox's no_proxy contains bracketed IPv6
        # literals that httpx cannot parse.
        client=httpx.Client(trust_env=False),
    )


def test_captured_provider_replays_by_query_text(tmp_path, monkeypatch):
    capture = {
        "queries": [
            {
                "query_id": "q01",
                "query": "US unemployment rate chart",
                "captured_at": "2026-10-18T00:00:00Z",
                "results": [
                    {
                        "url": "https://fred.stlouisfed.org/series/UNRATE",
                        "title": "Unemployment Rate",
                        "snippet": "FRED series",
                    }
                ],
            }
        ]
    }
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(capture))
    monkeypatch.setenv("KEENABLE_BROWSER_CAPTURE", str(path))

    provider = CapturedResultsProvider(
        ProviderConfig(name="keenable-browser", request_cost_ceiling_usd=0.0)
    )
    assert provider.configured()
    response = provider.search("  us   UNEMPLOYMENT rate chart ", 10, _context())
    assert response.status == "ok"
    assert len(response.results) == 1
    assert (
        str(response.results[0].url) == "https://fred.stlouisfed.org/series/UNRATE"
    )
    assert (
        str(response.results[0].bundles[0].source.document_url)
        == "https://fred.stlouisfed.org/series/UNRATE"
    )


def test_captured_provider_skips_without_file(monkeypatch):
    monkeypatch.delenv("KEENABLE_BROWSER_CAPTURE", raising=False)
    provider = CapturedResultsProvider(
        ProviderConfig(name="keenable-browser", request_cost_ceiling_usd=0.0)
    )
    assert not provider.configured()
    response = provider.search("anything", 10, _context())
    assert response.status == "skipped"


def test_captured_provider_errors_on_unknown_query(tmp_path, monkeypatch):
    path = tmp_path / "capture.json"
    path.write_text(json.dumps({"queries": []}))
    monkeypatch.setenv("KEENABLE_BROWSER_CAPTURE", str(path))
    provider = CapturedResultsProvider(
        ProviderConfig(name="keenable-browser", request_cost_ceiling_usd=0.0)
    )
    response = provider.search("no such query", 10, _context())
    assert response.status == "error"
