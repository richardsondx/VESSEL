import json

import httpx
import pytest

from vessel.adapters.base import BudgetExceeded, ReplayProvider
from vessel.adapters.evidence8 import Evidence8
from vessel.adapters.hybrid import ExaEvidence8, KeenableEvidence8, SerperEvidence8
from vessel.adapters.tier2 import (
    BingSearchApi,
    Brave,
    BraveLLMContext,
    ContextDev,
    Firecrawl,
    Jina,
    Kagi,
    Linkup,
    Octen,
    Parallel,
    ParallelTurbo,
    Perplexity,
    PerplexityFast,
    Tavily,
    Tinyfish,
    You,
)
from vessel.adapters.web import Exa, Keenable, Serper
from vessel.models import Protocol, ProviderConfig, RunConfig


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


def test_local_evidence8_asset_and_generated_rendition(monkeypatch):
    monkeypatch.setenv("EVIDENCE8_BASE_URL", "http://127.0.0.1:8787")
    row = {
        "id": "asset/chart",
        "sourceUrl": "https://example.org/chart-page",
        "assetMode": "derived-from-source-data",
        "rendition": "publisher",
        "renderingMethod": "SVG rendered from source CSV",
        "metadata": {
            "provenance": {"document": "Publisher report", "page": 7},
            "delivery": {
                "assetUrl": "/evidence/chart.svg",
                "dataPath": "/data/raw/chart.csv",
                "rights": {"label": "Attribution required"},
            },
        },
    }
    bundle = (
        Evidence8(ProviderConfig(name="evidence8"))
        .normalize({"status": "ok", "results": [row]}, 10)
        .results[0]
        .bundles[0]
    )
    assert str(bundle.visual.url) == "http://127.0.0.1:8787/v1/assets/asset%2Fchart/content"
    assert bundle.visual.rendition == "generated"
    assert bundle.derivation == "SVG rendered from source CSV"
    assert bundle.source.document_title == "Publisher report"
    assert bundle.rights == "Attribution required"
    assert bundle.location is None
    assert bundle.datasets == []  # A local file path is not a documented fetch URL.


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

_TIER2_POST_WIRE = [
    (
        Tavily,
        "TAVILY_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"query": "q", "max_results": 10, "search_depth": "basic", "include_answer": False},
        {"results": []},
    ),
    (
        Perplexity,
        "PERPLEXITY_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"query": "q", "max_results": 10},
        {"results": []},
    ),
    (
        PerplexityFast,
        "PERPLEXITY_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"query": "q", "max_results": 10, "max_tokens_per_page": 512},
        {"results": []},
    ),
    (
        You,
        "YDC_API_KEY",
        "X-API-Key",
        "test-key",
        {"query": "q", "count": 10},
        {"results": {"web": []}},
    ),
    (
        Linkup,
        "LINKUP_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"q": "q", "depth": "standard", "outputType": "searchResults"},
        {"results": []},
    ),
    (
        Firecrawl,
        "FIRECRAWL_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"query": "q", "limit": 10, "sources": ["web"]},
        {"data": {"web": []}},
    ),
    (
        Parallel,
        "PARALLEL_API_KEY",
        "x-api-key",
        "test-key",
        {
            "objective": "q",
            "search_queries": ["q"],
            "mode": "basic",
            "advanced_settings": {
                "max_results": 10,
                "excerpt_settings": {"max_chars_per_result": 500},
            },
        },
        {"results": []},
    ),
    (
        ParallelTurbo,
        "PARALLEL_API_KEY",
        "x-api-key",
        "test-key",
        {
            "objective": "q",
            "search_queries": ["q"],
            "mode": "turbo",
            "advanced_settings": {
                "max_results": 10,
                "excerpt_settings": {"max_chars_per_result": 500},
            },
        },
        {"results": []},
    ),
    (
        Jina,
        "JINA_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"q": "q", "num": 10},
        {"data": []},
    ),
    (
        ContextDev,
        "CONTEXT_DEV_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"query": "q", "numResults": 10},
        {"results": []},
    ),
    (
        Octen,
        "OCTEN_API_KEY",
        "X-Api-Key",
        "test-key",
        {"query": "q", "count": 10, "highlight": {"enable": True, "max_tokens": 300}},
        {"code": 0, "data": {"results": []}},
    ),
    (
        BraveLLMContext,
        "BRAVE_API_KEY",
        "X-Subscription-Token",
        "test-key",
        {"q": "q", "count": 10, "maximum_number_of_urls": 10},
        {"grounding": {"generic": []}},
    ),
]


@pytest.mark.parametrize("cls,key,header,header_value,expected,empty", _TIER2_POST_WIRE)
def test_tier2_post_wire_contract(cls, key, header, header_value, expected, empty, context, monkeypatch):
    monkeypatch.setenv(key, "test-key")

    def handler(request):
        assert request.method == "POST"
        assert request.headers[header] == header_value
        assert json.loads(request.content) == expected
        return httpx.Response(200, json=empty)

    context.client = httpx.Client(transport=httpx.MockTransport(handler))
    result = cls(ProviderConfig(name=cls.name, request_cost_ceiling_usd=0.01)).search(
        "q", 10, context
    )
    assert result.status == "no_match"
    assert result.requests == 1
    assert context.budget.reserved_usd == 0.01


_TIER2_GET_WIRE = [
    (
        Brave,
        "BRAVE_API_KEY",
        "X-Subscription-Token",
        "test-key",
        {"q": "q", "count": "10", "country": "US", "search_lang": "en"},
        {"web": {"results": []}},
    ),
    (
        Kagi,
        "KAGI_API_KEY",
        "Authorization",
        "Bot test-key",
        {"q": "q", "limit": "10"},
        {"data": []},
    ),
    (
        BingSearchApi,
        "SEARCHAPI_API_KEY",
        "Authorization",
        "Bearer test-key",
        {"engine": "bing", "q": "q", "num": "10"},
        {"organic_results": []},
    ),
    (
        Tinyfish,
        "TINYFISH_API_KEY",
        "X-API-Key",
        "test-key",
        {"query": "q"},
        {"results": []},
    ),
]


@pytest.mark.parametrize("cls,key,header,header_value,expected_params,empty", _TIER2_GET_WIRE)
def test_tier2_get_wire_contract(
    cls, key, header, header_value, expected_params, empty, context, monkeypatch
):
    monkeypatch.setenv(key, "test-key")

    def handler(request):
        assert request.method == "GET"
        assert request.headers[header] == header_value
        assert dict(request.url.params) == expected_params
        return httpx.Response(200, json=empty)

    context.client = httpx.Client(transport=httpx.MockTransport(handler))
    result = cls(ProviderConfig(name=cls.name, request_cost_ceiling_usd=0.01)).search(
        "q", 10, context
    )
    assert result.status == "no_match"
    assert result.requests == 1


_TIER2_FIXTURES = [
    (
        Brave,
        {"web": {"results": [{"title": "T", "url": "https://example.org/a", "description": "desc"}]}},
        ("T", "https://example.org/a", "desc"),
    ),
    (
        BraveLLMContext,
        {
            "grounding": {
                "generic": [
                    {"title": "T", "url": "https://example.org/a", "snippets": ["s1", "s2"]}
                ]
            }
        },
        ("T", "https://example.org/a", "s1\ns2"),
    ),
    (
        You,
        {
            "results": {
                "web": [{"title": "T", "url": "https://example.org/a", "description": "desc"}]
            }
        },
        ("T", "https://example.org/a", "desc"),
    ),
    (
        Tavily,
        {"results": [{"title": "T", "url": "https://example.org/a", "content": "body"}]},
        ("T", "https://example.org/a", "body"),
    ),
    (
        Perplexity,
        {"results": [{"title": "T", "url": "https://example.org/a", "snippet": "snip"}]},
        ("T", "https://example.org/a", "snip"),
    ),
    (
        PerplexityFast,
        {"results": [{"title": "T", "url": "https://example.org/a", "snippet": "snip"}]},
        ("T", "https://example.org/a", "snip"),
    ),
    (
        Kagi,
        {
            "data": [
                {"t": 0, "title": "T", "url": "https://example.org/a", "snippet": "snip"},
                {"t": 1, "list": ["related"]},
            ]
        },
        ("T", "https://example.org/a", "snip"),
    ),
    (
        Linkup,
        {"results": [{"name": "N", "url": "https://example.org/a", "snippet": "snip"}]},
        ("N", "https://example.org/a", "snip"),
    ),
    (
        Firecrawl,
        {
            "success": True,
            "data": {
                "web": [
                    {
                        "title": "T",
                        "url": "https://example.org/a",
                        "description": "desc",
                        "position": 1,
                    }
                ]
            },
        },
        ("T", "https://example.org/a", "desc"),
    ),
    (
        Firecrawl,
        {
            "success": True,
            "data": [{"title": "T", "url": "https://example.org/a", "description": "desc"}],
        },
        ("T", "https://example.org/a", "desc"),
    ),
    (
        Parallel,
        {"results": [{"title": "T", "url": "https://example.org/a", "excerpts": ["e1", "e2"]}]},
        ("T", "https://example.org/a", "e1\ne2"),
    ),
    (
        ParallelTurbo,
        {"results": [{"title": "T", "url": "https://example.org/a", "excerpts": ["e1"]}]},
        ("T", "https://example.org/a", "e1"),
    ),
    (
        BingSearchApi,
        {
            "organic_results": [
                {"position": 1, "title": "T", "link": "https://example.org/a", "snippet": "snip"}
            ]
        },
        ("T", "https://example.org/a", "snip"),
    ),
    (
        Jina,
        {
            "code": 200,
            "status": 20000,
            "data": [{"title": "T", "url": "https://example.org/a", "description": "desc"}],
        },
        ("T", "https://example.org/a", "desc"),
    ),
    (
        ContextDev,
        {
            "results": [
                {
                    "title": "T",
                    "url": "https://example.org/a",
                    "description": "desc",
                    "relevance": "high",
                }
            ]
        },
        ("T", "https://example.org/a", "desc"),
    ),
    (
        Octen,
        {
            "code": 0,
            "data": {
                "query": "q",
                "results": [{"title": "T", "url": "https://example.org/a", "highlight": "hl"}],
            },
        },
        ("T", "https://example.org/a", "hl"),
    ),
    (
        Tinyfish,
        {
            "query": "q",
            "results": [
                {"position": 1, "title": "T", "url": "https://example.org/a", "snippet": "snip"}
            ],
            "total_results": 1,
        },
        ("T", "https://example.org/a", "snip"),
    ),
]


@pytest.mark.parametrize("cls,raw,expected", _TIER2_FIXTURES)
def test_tier2_normalize_fixtures(cls, raw, expected):
    result = cls(ProviderConfig(name=cls.name)).normalize(raw, 10)
    assert result.status == "ok"
    assert len(result.results) == 1
    row = result.results[0]
    assert (row.title, str(row.url), row.snippet) == expected
    assert row.rank == 1
    # Tier 2 rows are document-only baselines: one bundle, source only.
    assert len(row.bundles) == 1
    bundle = row.bundles[0]
    assert str(bundle.source.document_url) == expected[1]
    assert bundle.visual is None
    assert bundle.location is None
    assert bundle.datasets == []


_TIER2_MALFORMED = [
    (Brave, "BRAVE_API_KEY", {}),
    (Brave, "BRAVE_API_KEY", {"web": {}}),
    (BraveLLMContext, "BRAVE_API_KEY", {}),
    (You, "YDC_API_KEY", {"results": {}}),
    (Tavily, "TAVILY_API_KEY", {"results": "x"}),
    (Perplexity, "PERPLEXITY_API_KEY", {}),
    (PerplexityFast, "PERPLEXITY_API_KEY", {"results": None}),
    (Kagi, "KAGI_API_KEY", {"data": "x"}),
    (Linkup, "LINKUP_API_KEY", {}),
    (Firecrawl, "FIRECRAWL_API_KEY", {"data": {"news": []}}),
    (Parallel, "PARALLEL_API_KEY", {"results": {}}),
    (ParallelTurbo, "PARALLEL_API_KEY", {}),
    (BingSearchApi, "SEARCHAPI_API_KEY", {}),
    (Jina, "JINA_API_KEY", {"code": 500, "data": []}),
    (ContextDev, "CONTEXT_DEV_API_KEY", {"results": "x"}),
    (Octen, "OCTEN_API_KEY", {"code": 3, "data": {"results": []}}),
    (Octen, "OCTEN_API_KEY", {"code": 0}),
    (Tinyfish, "TINYFISH_API_KEY", {}),
    (Brave, "BRAVE_API_KEY", {"web": {"results": [{"title": "no url"}]}}),
]


@pytest.mark.parametrize("cls,key,raw", _TIER2_MALFORMED)
def test_tier2_malformed_is_error(cls, key, raw, context, monkeypatch):
    monkeypatch.setenv(key, "test-key")
    context.client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=raw))
    )
    result = cls(ProviderConfig(name=cls.name, request_cost_ceiling_usd=0.01)).search(
        "q", 10, context
    )
    assert result.status == "error"


@pytest.mark.parametrize("cls,key", [(Brave, "BRAVE_API_KEY"), (Octen, "OCTEN_API_KEY")])
def test_tier2_missing_key_skips(cls, key, context, monkeypatch):
    monkeypatch.delenv(key, raising=False)
    result = cls(ProviderConfig(name=cls.name, request_cost_ceiling_usd=0.01)).search(
        "q", 10, context
    )
    assert result.status == "skipped"
    assert context.budget.requests == 0


@pytest.mark.parametrize(
    "cls,host,key,search_raw",
    [
        (
            ExaEvidence8,
            "api.exa.ai",
            "EXA_API_KEY",
            {"results": [{"title": "doc", "url": "https://example.org/a"}]},
        ),
        (
            SerperEvidence8,
            "google.serper.dev",
            "SERPER_API_KEY",
            {"organic": [{"title": "doc", "link": "https://example.org/a"}]},
        ),
    ],
)
def test_new_hybrids_attach_same_document(cls, host, key, search_raw, context, monkeypatch):
    monkeypatch.setenv(key, "test")
    monkeypatch.setenv("EVIDENCE8_BASE_URL", "http://127.0.0.1:8787")

    def handler(request):
        if request.url.host == host:
            return httpx.Response(200, json=search_raw)
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
    hybrid = cls(
        ProviderConfig(name=cls.name, request_cost_ceiling_usd=0.01),
        ProviderConfig(name="evidence8", request_cost_ceiling_usd=0.01),
    )
    result = hybrid.search("q", 10, context)
    assert result.requests == 2
    assert len(result.results[0].bundles) == 2
    assert str(result.results[0].bundles[1].visual.url) == "https://example.org/correct.png"


def test_hybrid_requires_search_and_evidence_entries():
    from vessel.runner import providers_for

    config = RunConfig(protocol=Protocol.EVIDENCE, providers=[ProviderConfig(name="exa_evidence8")])
    with pytest.raises(ValueError, match="hybrid requires"):
        providers_for(config, None)


def test_runner_registers_all_tier2_and_hybrids():
    from vessel.runner import HYBRID_SEARCH, TIER2, providers_for

    names = ["evidence8", "keenable", "exa", "serper", *TIER2, *HYBRID_SEARCH]
    config = RunConfig(
        protocol=Protocol.EVIDENCE,
        providers=[ProviderConfig(name=n, request_cost_ceiling_usd=0.01) for n in names],
    )
    providers = providers_for(config, None)
    assert set(providers) == set(names)
    for name, cls in TIER2.items():
        assert isinstance(providers[name], cls), name
    for name, (_, hybrid_cls) in HYBRID_SEARCH.items():
        assert isinstance(providers[name], hybrid_cls), name


def test_every_registered_provider_has_characterization_doc():
    from vessel.runner import HYBRID_SEARCH, ROOT, TIER2

    for name in ["evidence8", "keenable", "exa", "serper", *TIER2, *HYBRID_SEARCH]:
        assert (ROOT / "docs/providers" / f"{name}.md").exists(), name
