"""Tier 2 providers: NEEDLE text-search engines as document/source baselines.

Each adapter maps one provider response to EvidenceResult rows that carry a
single Bundle(source=document_url): no visual, no location, no dataset. That is
intentional; the gap between document recall and Full Support@K is the point of
Tier 2. Normalization reuses vessel.adapters.web.documents via the canonical()
helper so every adapter keeps the same strictness: a missing result array or a
row without a URL raises ValueError, which the transport layer records as an
error rather than silently dropping.

Request shapes are pinned per engine (see docs/providers/<name>.md).
"""

from vessel.adapters.base import HTTPProvider
from vessel.adapters.web import documents
from vessel.models import SearchResponse


def _first_present(row: dict, keys: tuple) -> str | None:
    for key in keys:
        value = row.get(key)
        if value:
            if isinstance(value, list):
                value = "\n".join(str(part) for part in value if part) or None
            return value
    return None


def canonical(rows: list, k: int, position: bool = False) -> SearchResponse:
    """Map provider-specific row shapes onto the documents() contract.

    Snippet and publication fields differ per provider; URL keys are the only
    hard requirement. Rows without a URL fail inside documents().
    """
    canon = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("document result must be an object")
        canon.append(
            {
                "url": _first_present(row, ("url", "link")),
                "title": _first_present(row, ("title", "name")) or "",
                "snippet": _first_present(
                    row,
                    (
                        "snippet",
                        "description",
                        "content",
                        "text",
                        "highlight",
                        "highlights",
                        "excerpts",
                        "snippets",
                    ),
                ),
                "published_at": _first_present(
                    row,
                    (
                        "published_at",
                        "publishedDate",
                        "published",
                        "date",
                        "page_age",
                        "time_published",
                    ),
                ),
            }
        )
    return documents({"results": canon}, "results", k, position=position)


def _result_array(raw: dict, field: str) -> list:
    rows = raw.get(field)
    if not isinstance(rows, list):
        raise ValueError(f"missing {field} array")
    return rows


class Brave(HTTPProvider):
    name = "brave"
    key_env = "BRAVE_API_KEY"
    base_env = "BRAVE_BASE_URL"
    default_base = "https://api.search.brave.com"
    path = "/res/v1/web/search"
    header = "X-Subscription-Token"
    method = "GET"

    def params(self, query, k):
        return {
            "q": query,
            "count": min(k, 20),
            "country": self.config.country.upper(),
            "search_lang": self.config.language,
        }

    def normalize(self, raw, k):
        web = raw.get("web")
        rows = web.get("results") if isinstance(web, dict) else None
        if not isinstance(rows, list):
            raise ValueError("missing web.results array")
        return canonical(rows, k)


class BraveLLMContext(HTTPProvider):
    name = "brave-llmcontext"
    key_env = "BRAVE_API_KEY"
    base_env = "BRAVE_BASE_URL"
    default_base = "https://api.search.brave.com"
    path = "/res/v1/llm/context"
    header = "X-Subscription-Token"

    def payload(self, query, k):
        return {"q": query, "count": min(k, 50), "maximum_number_of_urls": min(k, 50)}

    def normalize(self, raw, k):
        grounding = raw.get("grounding")
        rows = grounding.get("generic") if isinstance(grounding, dict) else None
        if not isinstance(rows, list):
            raise ValueError("missing grounding.generic array")
        return canonical(rows, k)


class You(HTTPProvider):
    name = "you"
    key_env = "YDC_API_KEY"
    base_env = "YOU_BASE_URL"
    default_base = "https://ydc-index.io"
    path = "/v1/search"
    header = "X-API-Key"

    def payload(self, query, k):
        return {"query": query, "count": k}

    def normalize(self, raw, k):
        results = raw.get("results")
        rows = results.get("web") if isinstance(results, dict) else None
        if not isinstance(rows, list):
            raise ValueError("missing results.web array")
        return canonical(rows, k)


class Tavily(HTTPProvider):
    name = "tavily"
    key_env = "TAVILY_API_KEY"
    base_env = "TAVILY_BASE_URL"
    default_base = "https://api.tavily.com"
    path = "/search"
    header = "Authorization"

    def header_value(self):
        return f"Bearer {self.key}"

    def payload(self, query, k):
        return {
            "query": query,
            "max_results": k,
            "search_depth": "basic",
            "include_answer": False,
        }

    def normalize(self, raw, k):
        return canonical(_result_array(raw, "results"), k)


class Perplexity(HTTPProvider):
    name = "perplexity"
    key_env = "PERPLEXITY_API_KEY"
    base_env = "PERPLEXITY_BASE_URL"
    default_base = "https://api.perplexity.ai"
    path = "/search"
    header = "Authorization"

    def header_value(self):
        return f"Bearer {self.key}"

    def payload(self, query, k):
        return {"query": query, "max_results": k}

    def normalize(self, raw, k):
        return documents(raw, "results", k)


class PerplexityFast(Perplexity):
    """Reduced-token-cost variant of the same Search API.

    Perplexity documents no separate "fast" search type; VESSEL pins a
    max_tokens_per_page of 512 as the cost/latency tradeoff point.
    """

    name = "perplexity-fast"

    def payload(self, query, k):
        return {"query": query, "max_results": k, "max_tokens_per_page": 512}


class Kagi(HTTPProvider):
    name = "kagi"
    key_env = "KAGI_API_KEY"
    base_env = "KAGI_BASE_URL"
    default_base = "https://kagi.com"
    path = "/api/v0/search"
    header = "Authorization"
    method = "GET"

    def header_value(self):
        return f"Bot {self.key}"

    def params(self, query, k):
        return {"q": query, "limit": k}

    def normalize(self, raw, k):
        rows = _result_array(raw, "data")
        # t=0 is a web result; other types are related searches and feature blocks.
        return canonical([row for row in rows if row.get("t") == 0], k)


class Linkup(HTTPProvider):
    name = "linkup"
    key_env = "LINKUP_API_KEY"
    base_env = "LINKUP_BASE_URL"
    default_base = "https://api.linkup.so"
    path = "/v1/search"
    header = "Authorization"

    def header_value(self):
        return f"Bearer {self.key}"

    def payload(self, query, k):
        return {"q": query, "depth": "standard", "outputType": "searchResults"}

    def normalize(self, raw, k):
        return canonical(_result_array(raw, "results"), k)


class Firecrawl(HTTPProvider):
    name = "firecrawl"
    key_env = "FIRECRAWL_API_KEY"
    base_env = "FIRECRAWL_BASE_URL"
    default_base = "https://api.firecrawl.dev"
    path = "/v2/search"
    header = "Authorization"

    def header_value(self):
        return f"Bearer {self.key}"

    def payload(self, query, k):
        return {"query": query, "limit": k, "sources": ["web"]}

    def normalize(self, raw, k):
        data = raw.get("data")
        if isinstance(data, dict):
            rows = data.get("web")
        elif isinstance(data, list):
            rows = data
        else:
            rows = None
        if not isinstance(rows, list):
            raise ValueError("missing data.web array")
        return canonical(rows, k, position=True)


class Parallel(HTTPProvider):
    name = "parallel"
    key_env = "PARALLEL_API_KEY"
    base_env = "PARALLEL_BASE_URL"
    default_base = "https://api.parallel.ai"
    path = "/v1/search"
    header = "x-api-key"
    mode = "basic"

    def payload(self, query, k):
        return {
            "objective": query,
            "search_queries": [query],
            "mode": self.mode,
            "advanced_settings": {
                "max_results": k,
                "excerpt_settings": {"max_chars_per_result": 500},
            },
        }

    def normalize(self, raw, k):
        return canonical(_result_array(raw, "results"), k)


class ParallelTurbo(Parallel):
    name = "parallel-turbo"
    mode = "turbo"


class BingSearchApi(HTTPProvider):
    name = "bing-searchapi"
    key_env = "SEARCHAPI_API_KEY"
    base_env = "SEARCHAPI_BASE_URL"
    default_base = "https://www.searchapi.io"
    path = "/api/v1/search"
    header = "Authorization"
    method = "GET"

    def header_value(self):
        return f"Bearer {self.key}"

    def params(self, query, k):
        return {"engine": "bing", "q": query, "num": min(k, 50)}

    def normalize(self, raw, k):
        return documents(raw, "organic_results", k, position=True)


class Jina(HTTPProvider):
    name = "jina"
    key_env = "JINA_API_KEY"
    base_env = "JINA_BASE_URL"
    default_base = "https://s.jina.ai"
    path = "/"
    header = "Authorization"

    def header_value(self):
        return f"Bearer {self.key}"

    def extra_headers(self):
        return {"Accept": "application/json"}

    def payload(self, query, k):
        return {"q": query, "num": k}

    def normalize(self, raw, k):
        if raw.get("code") not in (None, 200):
            raise ValueError(f"jina search failed with code {raw.get('code')}")
        return documents(raw, "data", k)


class ContextDev(HTTPProvider):
    name = "context-dev"
    key_env = "CONTEXT_DEV_API_KEY"
    base_env = "CONTEXT_DEV_BASE_URL"
    default_base = "https://api.context.dev"
    path = "/v1/web/search"
    header = "Authorization"

    def header_value(self):
        return f"Bearer {self.key}"

    def payload(self, query, k):
        # The OpenAPI schema requires numResults between 10 and 100; slice to k locally.
        return {"query": query, "numResults": max(k, 10)}

    def normalize(self, raw, k):
        return documents(raw, "results", k)


class Octen(HTTPProvider):
    name = "octen"
    key_env = "OCTEN_API_KEY"
    base_env = "OCTEN_BASE_URL"
    default_base = "https://api.octen.ai"
    path = "/search"
    header = "X-Api-Key"

    def payload(self, query, k):
        return {
            "query": query,
            "count": min(k, 20),
            "highlight": {"enable": True, "max_tokens": 300},
        }

    def normalize(self, raw, k):
        if raw.get("code") != 0:
            raise ValueError(f"octen search failed with code {raw.get('code')}")
        data = raw.get("data")
        rows = data.get("results") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ValueError("missing data.results array")
        return canonical(rows, k)


class Tinyfish(HTTPProvider):
    name = "tinyfish"
    key_env = "TINYFISH_API_KEY"
    base_env = "TINYFISH_BASE_URL"
    default_base = "https://api.search.tinyfish.ai"
    path = ""
    header = "X-API-Key"
    method = "GET"

    def params(self, query, k):
        return {"query": query}

    def normalize(self, raw, k):
        return documents(raw, "results", k, position=True)


__all__ = [
    "BingSearchApi",
    "Brave",
    "BraveLLMContext",
    "ContextDev",
    "Firecrawl",
    "Jina",
    "Kagi",
    "Linkup",
    "Octen",
    "Parallel",
    "ParallelTurbo",
    "Perplexity",
    "PerplexityFast",
    "Tavily",
    "Tinyfish",
    "You",
]
