import pytest

from vessel.identity import canonical_url
from vessel.models import Adjudication, Asset, EvidenceResult, Identity, Location, digest
from vessel.scoring import location_matches, score_query


def evaluate(gold, bundle, rank=1, k=10):
    return score_query(gold, [EvidenceResult(rank=rank, bundles=[bundle])], k)


def test_complete_bundle(gold, bundle):
    assert evaluate(gold, bundle)["full_support"]


@pytest.mark.parametrize("component", ["visual", "location", "datasets"])
def test_missing_component(gold, bundle, component):
    setattr(bundle, component, [] if component == "datasets" else None)
    assert not evaluate(gold, bundle)["full_support"]


def test_not_stitched_across_results(gold, bundle):
    a = bundle.model_copy(deep=True)
    b = bundle.model_copy(deep=True)
    a.datasets = []
    b.visual = None
    result = score_query(
        gold, [EvidenceResult(rank=1, bundles=[a]), EvidenceResult(rank=2, bundles=[b])], 10
    )
    assert all(result["components"][name] for name in gold.alternatives[0].required)
    assert not result["full_support"]


def test_not_stitched_across_bundles(gold, bundle):
    a = bundle.model_copy(deep=True)
    b = bundle.model_copy(deep=True)
    a.location = None
    b.visual = None
    assert not score_query(gold, [EvidenceResult(rank=1, bundles=[a, b])], 10)["full_support"]


@pytest.mark.parametrize("rendition", ["generated", "unknown"])
def test_original_requirement(gold, bundle, rendition):
    bundle.visual.rendition = rendition
    if rendition == "unknown":
        bundle.visual.url = "https://example.org/unverified.png"
    assert not evaluate(gold, bundle)["full_support"]


def test_generated_allowed_only_explicitly(gold, bundle):
    gold.alternatives[0].original_required = False
    bundle.visual.rendition = "generated"
    assert evaluate(gold, bundle)["full_support"]


def test_secondary_source(gold, bundle):
    gold.alternatives[0].document.urls.append("https://mirror.example/report.pdf")
    bundle.source.document_url = "https://mirror.example/report.pdf"
    result = evaluate(gold, bundle)
    assert result["components"]["visual"]
    assert result["failure"] == "SECONDARY_SOURCE"


def test_wrong_figure(gold, bundle):
    bundle.location.figure = "3.9"
    assert not evaluate(gold, bundle)["full_support"]


def test_pdf_index_not_printed_label(gold, bundle):
    bundle.location = Location(page_label="4", figure="3.8")
    assert not evaluate(gold, bundle)["full_support"]


def test_data_not_required_when_unavailable(gold, bundle):
    alt = gold.alternatives[0]
    alt.required.remove("data")
    alt.data_available = False
    alt.datasets = []
    bundle.datasets = []
    assert evaluate(gold, bundle)["full_support"]


def test_wrong_version(gold, bundle):
    gold.alternatives[0].version = "2025-final"
    gold.alternatives[0].required.add("version")
    bundle.source.version = "2024-final"
    assert evaluate(gold, bundle)["failure"] == "VERSION_FAIL"


def test_hash_identity(gold, bundle):
    gold.alternatives[0].visual = Identity(sha256=["a" * 64])
    bundle.visual = Asset(sha256="a" * 64, rendition="crop")
    assert evaluate(gold, bundle)["full_support"]


def test_perceptual_hash_not_identity(gold, bundle):
    bundle.visual = Asset(
        url="https://wrong.example/chart.png", rendition="publisher", perceptual_hash="same"
    )
    assert not evaluate(gold, bundle)["full_support"]


def test_adjudication_binds_bundle(gold, bundle):
    bundle.visual.url = "https://example.org/rendition.png"
    decision = Adjudication(
        query_id="q1",
        evidence_id="e1",
        bundle_sha256=digest(bundle),
        decision="equivalent",
        reviewer="human",
        reason="Same rendition audited",
    )
    assert score_query(gold, [EvidenceResult(rank=1, bundles=[bundle])], 10, [decision])[
        "full_support"
    ]
    bundle.source.document_url = "https://different.example/report"
    assert not score_query(gold, [EvidenceResult(rank=1, bundles=[bundle])], 10, [decision])[
        "full_support"
    ]


def test_multiple_gold_alternatives(gold, bundle):
    other = gold.alternatives[0].model_copy(deep=True)
    gold.alternatives[0].visual = Identity(urls=["https://wrong.example/chart"])
    gold.alternatives.append(other)
    assert evaluate(gold, bundle)["full_support"]


def test_rank_cutoff_and_mrr(gold, bundle):
    assert not evaluate(gold, bundle, rank=6, k=5)["full_support"]
    assert evaluate(gold, bundle, rank=6)["reciprocal_rank"] == 1 / 6


def test_page_only_not_visual_identity(gold, bundle):
    gold.alternatives[0].visual = Identity()
    gold.alternatives[0].locations = [Location(page_index=4)]
    bundle.visual.url = "https://example.org/wrong-figure.png"
    assert not evaluate(gold, bundle)["full_support"]


def test_locator_identifies_web_visual(gold, bundle):
    gold.alternatives[0].visual = Identity()
    gold.alternatives[0].locations = [Location(locator="#figure-7")]
    bundle.location = Location(locator="#figure-7")
    assert evaluate(gold, bundle)["full_support"]


def test_bbox_threshold():
    assert location_matches(
        Location(bbox=(0.1, 0.1, 0.9, 0.9)), Location(bbox=(0.1, 0.1, 0.9, 0.9))
    )
    assert not location_matches(
        Location(bbox=(0.1, 0.1, 0.9, 0.9)), Location(bbox=(0.1, 0.1, 0.2, 0.2))
    )


def test_url_keeps_vintage_query():
    assert (
        canonical_url("https://EXAMPLE.org/a?vintage=1#chart") == "https://example.org/a?vintage=1"
    )
    assert canonical_url("https://example.org/a?vintage=1") != canonical_url(
        "https://example.org/a?vintage=2"
    )


def test_exact_original_identity_without_renderer_label(gold, bundle):
    bundle.visual.rendition = "unknown"
    assert evaluate(gold, bundle)["full_support"]


def test_supplemental_requirements_are_independent_and_optional(gold, bundle):
    from vessel.models import Identity
    from vessel.scoring import score_query

    result = EvidenceResult(rank=1, bundles=[bundle])
    g = gold.alternatives[0]
    g.accepted_rights = ["CC BY 4.0"]
    g.methodology = Identity(urls=["https://example.org/methodology"])
    g.reproducibility = Identity(urls=["https://example.org/reproduce"])
    before = score_query(gold, [result], 10)
    assert before["full_support"]
    assert not before["components"]["rights"]
    g.required = g.required | {"rights", "methodology", "reproducibility"}
    assert not score_query(gold, [result], 10)["full_support"]
    bundle = result.bundles[0]
    bundle.rights = "CC BY 4.0"
    bundle.methodology_url = "https://example.org/methodology"
    bundle.reproducibility_url = "https://example.org/reproduce"
    assert score_query(gold, [result], 10)["full_support"]
