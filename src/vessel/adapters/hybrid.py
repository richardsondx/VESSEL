from vessel.adapters.base import Context
from vessel.adapters.evidence8 import Evidence8
from vessel.adapters.web import Keenable
from vessel.identity import canonical_url
from vessel.models import Observation, ProviderConfig, SearchResponse


class KeenableEvidence8:
    """Document-conditioned query search, not a claim of native document enrichment."""

    name = "keenable_evidence8"

    def __init__(self, search_config: ProviderConfig, evidence_config: ProviderConfig):
        self.search_provider = Keenable(search_config)
        self.evidence_provider = Evidence8(evidence_config)

    def search(self, query: str, k: int, context: Context) -> SearchResponse:
        if not self.search_provider.configured() or not self.evidence_provider.configured():
            return SearchResponse(
                status="skipped", reason="both hybrid providers must be configured"
            )
        result = self.search_provider.search(query, k, context)
        if result.status != "ok":
            return result
        seen = set()
        for document in result.results:
            url = canonical_url(document.url)
            if not url or url in seen:
                continue
            seen.add(url)
            if len(seen) > 5:
                break
            enriched = self.evidence_provider.search(f"{query}\nSource document: {url}", k, context)
            result.requests += enriched.requests
            result.reserved_cost_usd += enriched.reserved_cost_usd
            result.reported_cost_usd = (
                result.reported_cost_usd + enriched.reported_cost_usd
                if result.reported_cost_usd is not None and enriched.reported_cost_usd is not None
                else None
            )
            result.latency_ms = (result.latency_ms or 0) + (enriched.latency_ms or 0)
            result.observations.extend(enriched.observations)
            result.observations.append(
                Observation(kind="hybrid_enrichment", status=enriched.status)
            )
            if enriched.status in {"error", "budget_exhausted", "skipped"}:
                # Retain initial results, but runner must not publish a partial hybrid comparison.
                result.observations.append(Observation(kind="hybrid", status="incomplete"))
                continue
            for evidence in enriched.results:
                for bundle in evidence.bundles:
                    if canonical_url(bundle.source.document_url) == url:
                        document.bundles.append(bundle)
        return result
