"""Maps documented asset fields conservatively; missing facts stay unknown."""

from vessel.adapters.base import HTTPProvider
from vessel.models import Asset, Bundle, Dataset, EvidenceResult, Location, SearchResponse, Source


def mapping(value):
    if not isinstance(value, dict):
        raise ValueError("metadata group must be an object")
    return value


def name(value):
    if isinstance(value, dict):
        return value.get("name") or value.get("title")
    return value if isinstance(value, str) else None


def normalize_asset(row: dict, rank: int) -> EvidenceResult:
    if not isinstance(row, dict):
        raise ValueError("candidate must be an object")
    asset = row.get("asset", row)
    if not isinstance(asset, dict):
        raise ValueError("asset must be an object")
    metadata = mapping(asset.get("metadata") or {})
    provenance = mapping(metadata.get("provenance") or {})
    delivery = mapping(metadata.get("delivery") or {})
    identity = mapping(metadata.get("identity") or {})
    doc = provenance.get("sourceDocument") or asset.get("sourceDocument") or {}
    if not isinstance(doc, dict):
        doc = {"title": doc}
    source_url = (
        provenance.get("canonicalSourceUrl")
        or provenance.get("sourceUrl")
        or doc.get("url")
        or asset.get("sourceUrl")
    )
    visual_url = delivery.get("assetUrl") or asset.get("imageUrl") or asset.get("assetUrl")
    data_url = delivery.get("dataUrl") or asset.get("dataUrl")
    # A provider's asserted sha/primary flag is not a computed or adjudicated identity.
    source = Source(
        document_url=source_url,
        document_id=doc.get("id"),
        document_title=name(doc),
        publisher=name(provenance.get("publisher") or asset.get("publisher")),
        published_at=provenance.get("publishedAt") or asset.get("publishedAt"),
        version=provenance.get("version"),
    )
    page = provenance.get("pageIndex")
    label = provenance.get("pageLabel")
    figure = provenance.get("figureNumber") or asset.get("figureNumber")
    location = (
        Location(
            page_index=page, page_label=str(label) if label is not None else None, figure=figure
        )
        if page is not None or label is not None or figure
        else None
    )
    rendition = asset.get("rendition") or identity.get("rendition") or "unknown"
    if rendition not in {"publisher", "crop", "capture", "generated", "unknown"}:
        rendition = "unknown"
    visual = Asset(url=visual_url, rendition=rendition) if visual_url else None
    bundle = Bundle(
        source=source,
        visual=visual,
        location=location,
        datasets=[Dataset(url=data_url)] if data_url else [],
        rights=name(delivery.get("rights") or asset.get("rights")),
        derivation=asset.get("derivation"),
    )
    return EvidenceResult(
        rank=rank,
        provider_id=asset.get("assetId") or asset.get("id"),
        title=asset.get("title") or "",
        url=source_url,
        snippet=asset.get("description"),
        bundles=[bundle],
    )


class Evidence8(HTTPProvider):
    name = "evidence8"
    key_env = "EVIDENCE8_API_KEY"
    base_env = "EVIDENCE8_BASE_URL"
    default_base = ""
    path = "/v1/search"
    header = "Authorization"

    def __init__(self, config):
        super().__init__(config)
        # Optional workspace bearer key; public local documentation requires no auth.
        if self.key:
            self.key = "Bearer " + self.key

    def payload(self, query, k):
        return {"query": query, "corpus": self.config.corpus, "candidateLimit": k}

    def normalize(self, raw, k):
        status = raw.get("status")
        if status == "no_match":
            return SearchResponse(status="no_match")
        if status != "ok":
            raise ValueError("unexpected Evidence8 status")
        rows = raw.get("results")
        if rows is None and raw.get("selected"):
            rows = [raw["selected"]]
        if not isinstance(rows, list):
            raise ValueError("missing candidate array")
        results = [normalize_asset(row, rank) for rank, row in enumerate(rows[:k], 1)]
        return SearchResponse(status="ok" if results else "no_match", results=results)
