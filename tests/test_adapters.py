import json

import httpx
import pytest

from vessel.adapters.base import BudgetExceeded, ReplayProvider
from vessel.adapters.evidence8 import Evidence8
from vessel.adapters.hybrid import KeenableEvidence8
from vessel.adapters.web import Exa, Keenable, Serper
from vessel.models import ProviderConfig


@pytest.mark.parametrize(
    "cls,key,expected",
    [
        (Keenable, "KEENABLE_API_KEY", {"query": "q", "max_results": 10, "mode": "pro"}),
        (Exa, "EXA_API_KEY", {"query": "q", "numResults": 10, "type": "auto"}),
        (Serper, "SERPER_API_KEY", {"q": "q", "num": 10, "gl": "us", "hl": "en"}),
        (Evidence8, "EVIDENCE8_API_KEY", {"query": "q", "corpus": "all", "candidateLimit": 10}),
    ],
)
def test_wire_contract(cls, key, expected, context, monkeypatch):
    monkeypatch.setenv(key, "test-key")
    if cls is Evidence8:
        monkeypatch.setenv("EVIDENCE8_BASE_URL", "http://127.0.0.1:8787")

    def handler(request):
        assert json.loads(request.content) == expected
        raw = {"organic": []} if cls is Serper else {"status": "ok", "results": []}
        return httpx.Response(200, json=raw)

    context.client = httpx.Client(transport=httpx.MockTransport(handler))
    result = cls(ProviderConfig(name=cls.name, request_cost_ceiling_usd=0.01)).search(
        "q", 10, context
    )
    assert result.status == "no_match"
    assert result.requests == 1
    assert context.budget.reserved_usd == 0.01


def test_missing_key_skips(context, monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    result = Exa(ProviderConfig(name="exa", request_cost_ceiling_usd=0.01)).search("q", 10, context)
    assert result.status == "skipped"
    assert context.budget.requests == 0


def test_no_ceiling_skips(context, monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "test")
    assert Exa(ProviderConfig(name="exa")).search("q", 10, context).status == "skipped"


def test_rate_limit_no_unbudgeted_retry(context, monkeypatch):
    monkeypatch.setenv("KEENABLE_API_KEY", "test")
    context.client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(429)))
    result = Keenable(ProviderConfig(name="keenable", request_cost_ceiling_usd=0.1)).search(
        "q", 10, context
    )
    assert result.reason == "HTTP 429"
    assert result.requests == 1


def test_response_secret_redaction(context, monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "secret-value")
    context.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"results": [], "apiKey": "secret-value", "echo": "secret-value"}
            )
        )
    )
    result = Exa(ProviderConfig(name="exa", request_cost_ceiling_usd=0)).search("q", 10, context)
    content = context.artifacts.read(result.observations[0].artifact_sha256)
    assert b"secret-value" not in content


def test_actual_result_count_and_order():
    result = Keenable(ProviderConfig(name="keenable")).normalize(
        {
            "results": [
                {"title": "first", "url": "https://example.org/a"},
                {"title": "second", "url": "https://example.org/b"},
            ]
        },
        10,
    )
    assert [(r.rank, r.title) for r in result.results] == [(1, "first"), (2, "second")]
    assert all(r.bundles[0].visual is None for r in result.results)


def test_no_fabricated_evidence8_provenance():
    result = Evidence8(ProviderConfig(name="evidence8")).normalize(
        {
            "status": "ok",
            "selected": {
                "assetId": "ev1",
                "title": "chart",
                "sourceUrl": "https://example.org/report",
                "imageUrl": "https://example.org/chart.png",
                "page": 7,
                "sha256": "a" * 64,
                "primarySource": True,
            },
        },
        10,
    )
    bundle = result.results[0].bundles[0]
    assert bundle.location is None  # ambiguous page convention not silently interpreted
    assert bundle.visual.sha256 is None
    assert bundle.visual.rendition == "unknown"


def test_metadata_envelope():
    row = {
        "asset": {
            "assetId": "a1",
            "metadata": {
                "identity": {"rendition": "publisher"},
                "provenance": {
                    "canonicalSourceUrl": "https://example.org/report",
                    "pageIndex": 0,
                    "figureNumber": "1",
                    "publisher": {"name": "Org"},
                },
                "delivery": {
                    "assetUrl": "https://example.org/chart.png",
                    "dataUrl": "https://example.org/data.csv",
                },
            },
        }
    }
    result = Evidence8(ProviderConfig(name="evidence8")).normalize(
        {"status": "ok", "results": [row]}, 10
    )
    b = result.results[0].bundles[0]
    assert b.location.page_index == 0
    assert b.source.publisher == "Org"
    assert len(b.datasets) == 1


def test_malformed_response_is_error(context, monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "test")
    context.client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))
    )
    assert (
        Exa(ProviderConfig(name="exa", request_cost_ceiling_usd=0)).search("q", 10, context).status
        == "error"
    )


def test_budget_not_transmitted(context, monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "test")
    context.budget.max_usd = 0
    result = Exa(ProviderConfig(name="exa", request_cost_ceiling_usd=0.1)).search("q", 10, context)
    assert result.status == "budget_exhausted"
    assert context.budget.requests == 0


def test_budget_request_limit(context):
    context.budget.max_requests = 1
    context.budget.reserve(0)
    with pytest.raises(BudgetExceeded):
        context.budget.reserve(0)


def test_replay_fixture_requires_label(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{}")
    with pytest.raises(ValueError):
        ReplayProvider("exa", path)


def test_hybrid_only_attaches_same_document(context, monkeypatch):
    monkeypatch.setenv("KEENABLE_API_KEY", "test")
    monkeypatch.setenv("EVIDENCE8_BASE_URL", "http://127.0.0.1:8787")

    def handler(request):
        if request.url.host == "api.keenable.ai":
            return httpx.Response(
                200, json={"results": [{"title": "doc", "url": "https://example.org/a"}]}
            )
        assert "Source document: https://example.org/a" in json.loads(request.content)["query"]
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "results": [
                    {
                        "sourceUrl": "https://example.org/b",
                        "imageUrl": "https://example.org/chart.png",
                    },
                    {
                        "sourceUrl": "https://example.org/a",
                        "imageUrl": "https://example.org/correct.png",
                    },
                ],
            },
        )

    context.client = httpx.Client(transport=httpx.MockTransport(handler))
    hybrid = KeenableEvidence8(
        ProviderConfig(name="keenable", request_cost_ceiling_usd=0.01),
        ProviderConfig(name="evidence8", request_cost_ceiling_usd=0.01),
    )
    result = hybrid.search("q", 10, context)
    assert result.requests == 2
    assert len(result.results[0].bundles) == 2
    assert str(result.results[0].bundles[1].visual.url) == "https://example.org/correct.png"
