from vessel.adapters.base import HTTPProvider
from vessel.models import Bundle, EvidenceResult, SearchResponse, Source


def documents(raw: dict, field: str, k: int, position: bool = False) -> SearchResponse:
    rows = raw.get(field)
    if not isinstance(rows, list):
        raise ValueError(f"missing {field} array")
    results = []
    for rank, row in enumerate(rows[:k], 1):
        if not isinstance(row, dict):
            raise ValueError("document result must be an object")
        url = row.get("url") or row.get("link")
        if not url:
            raise ValueError("document result has no URL")
        results.append(
            EvidenceResult(
                rank=rank,
                url=url,
                title=row.get("title") or "",
                provider_id=row.get("id"),
                snippet=row.get("snippet") or row.get("text") or row.get("description"),
                provider_position=row.get("position") if position else None,
                bundles=[
                    Bundle(
                        source=Source(
                            document_url=url,
                            published_at=row.get("published_at") or row.get("publishedDate"),
                        )
                    )
                ],
            )
        )
    cost = raw.get("costDollars", {})
    return SearchResponse(
        status="ok" if results else "no_match",
        results=results,
        request_id=raw.get("requestId"),
        reported_cost_usd=cost.get("total") if isinstance(cost, dict) else None,
    )


class Keenable(HTTPProvider):
    name = "keenable"
    key_env = "KEENABLE_API_KEY"
    base_env = "KEENABLE_BASE_URL"
    default_base = "https://api.keenable.ai"
    path = "/v1/search"

    def payload(self, query, k):
        return {"query": query, "max_results": k, "mode": self.config.mode or "pro"}

    def normalize(self, raw, k):
        return documents(raw, "results", k)


class Exa(HTTPProvider):
    name = "exa"
    key_env = "EXA_API_KEY"
    base_env = "EXA_BASE_URL"
    default_base = "https://api.exa.ai"
    path = "/search"
    header = "x-api-key"

    def payload(self, query, k):
        return {"query": query, "numResults": k, "type": self.config.mode or "auto"}

    def normalize(self, raw, k):
        return documents(raw, "results", k)


class Serper(HTTPProvider):
    name = "serper"
    key_env = "SERPER_API_KEY"
    base_env = "SERPER_BASE_URL"
    default_base = "https://google.serper.dev"
    path = "/search"
    header = "X-API-KEY"

    def payload(self, query, k):
        return {"q": query, "num": k, "gl": self.config.country, "hl": self.config.language}

    def normalize(self, raw, k):
        return documents(raw, "organic", k, position=True)
