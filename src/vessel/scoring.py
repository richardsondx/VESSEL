"""Deterministic scoring. No provider dependencies or provider-specific exceptions."""

from vessel.identity import canonical_url
from vessel.models import (
    Adjudication,
    Bundle,
    EvidenceResult,
    GoldAlternative,
    GoldRecord,
    Identity,
    Location,
    digest,
)

COMPONENTS = (
    "document",
    "visual",
    "primary",
    "localization",
    "data",
    "version",
    "rights",
    "methodology",
    "reproducibility",
)


def matches(identity: Identity, url=None, sha=None, identifier=None) -> bool:
    return bool(
        (url and canonical_url(url) in {canonical_url(x) for x in identity.urls})
        or (sha and sha in identity.sha256)
        or (identifier and identifier in identity.ids)
    )


def location_matches(actual: Location | None, expected: Location) -> bool:
    if not actual:
        return False
    fields = expected.model_dump(exclude_none=True)
    if not fields:
        return False
    for key, value in fields.items():
        got = getattr(actual, key)
        if key == "bbox":
            if got is None:
                return False
            ix = max(0, min(got[2], value[2]) - max(got[0], value[0]))
            iy = max(0, min(got[3], value[3]) - max(got[1], value[1]))
            intersection = ix * iy
            union = (
                (got[2] - got[0]) * (got[3] - got[1])
                + (value[2] - value[0]) * (value[3] - value[1])
                - intersection
            )
            if union <= 0 or intersection / union < 0.8:
                return False
        elif got != value:
            return False
    return True


def components(
    bundle: Bundle, gold: GoldAlternative, query_id: str, adjudications: list[Adjudication]
) -> dict[str, bool]:
    src = bundle.source
    document = matches(gold.document, src.document_url, src.document_sha256, src.document_id)
    localization = document and any(
        location_matches(bundle.location, loc) for loc in gold.locations
    )
    visual = False
    if bundle.visual:
        visual = matches(gold.visual, bundle.visual.url, bundle.visual.sha256)
        # Reviewed document + precise figure location identifies a PDF/web rendition.
        if not gold.visual.urls and not gold.visual.sha256:
            precise = any(
                loc.figure or loc.bbox or loc.locator
                for loc in gold.locations
                if location_matches(bundle.location, loc)
            )
            visual = bool(localization and precise and (bundle.visual.url or bundle.visual.sha256))
        decisions = [
            a
            for a in adjudications
            if a.query_id == query_id
            and a.evidence_id == gold.evidence_id
            and a.bundle_sha256 == digest(bundle)
        ]
        if decisions:
            # Conflicting judgments cannot become automatic support.
            visual = all(a.decision == "equivalent" for a in decisions)
        if gold.original_required and bundle.visual.rendition == "generated":
            visual = False
        elif gold.original_required and bundle.visual.rendition == "unknown":
            # Gold's independently accepted original asset identity can prove originality
            # even when a provider does not supply a renderer label.
            visual = visual and matches(gold.visual, bundle.visual.url, bundle.visual.sha256)
    primary = bool(
        document
        and canonical_url(src.document_url) in {canonical_url(u) for u in gold.authoritative_urls}
    )
    data = bool(
        gold.data_available
        and gold.datasets
        and all(
            any(matches(expected, d.url, d.sha256, d.dataset_id) for d in bundle.datasets)
            for expected in gold.datasets
        )
    )
    version = bool(gold.version and src.version == gold.version)
    if gold.version and not version:
        visual = False
    return dict(
        document=document,
        visual=visual,
        primary=primary,
        localization=localization,
        data=data,
        version=version,
        rights=bool(document and bundle.rights and bundle.rights in gold.accepted_rights),
        methodology=bool(document and matches(gold.methodology, bundle.methodology_url)),
        reproducibility=bool(
            document and matches(gold.reproducibility, bundle.reproducibility_url)
        ),
    )


def score_query(
    record: GoldRecord,
    results: list[EvidenceResult],
    k: int,
    adjudications: list[Adjudication] | None = None,
) -> dict:
    adjudications = adjudications or []
    available = {name: False for name in COMPONENTS}
    full_rank = None
    diagnostics = []
    for result in results:
        if result.rank > k:
            continue
        bundles = result.bundles or [Bundle(source={"document_url": result.url})]
        for index, bundle in enumerate(bundles):
            for gold in record.alternatives:
                flags = components(bundle, gold, record.query_id, adjudications)
                for name in COMPONENTS:
                    available[name] |= flags[name]
                full = all(flags[name] for name in gold.required)
                if full and (full_rank is None or result.rank < full_rank):
                    full_rank = result.rank
                diagnostics.append(
                    {
                        "rank": result.rank,
                        "bundle": index,
                        "bundle_sha256": digest(bundle),
                        "evidence_id": gold.evidence_id,
                        "components": flags,
                        "full_support": full,
                        "missing": sorted(name for name in gold.required if not flags[name]),
                    }
                )
    if full_rank:
        failure = None
    elif not available["document"]:
        failure = "DOC_MISS"
    elif any(g.version for g in record.alternatives) and not available["version"]:
        failure = "VERSION_FAIL"
    elif not available["visual"]:
        failure = "FIGURE_MISS"
    elif not available["primary"]:
        failure = "SECONDARY_SOURCE"
    elif not available["localization"]:
        failure = "LOCALIZATION_FAIL"
    elif any("data" in g.required for g in record.alternatives) and not available["data"]:
        failure = "DATA_MISS"
    else:
        failure = "PROVENANCE_BREAK"
    return {
        "query_id": record.query_id,
        "k": k,
        "components": available,
        "full_support": full_rank is not None,
        "reciprocal_rank": 1 / full_rank if full_rank else 0,
        "failure": failure,
        "diagnostics": diagnostics,
    }
