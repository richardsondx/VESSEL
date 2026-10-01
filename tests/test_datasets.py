from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from vessel.datasets import DOMAINS, VISUAL_TARGETS, validate_dataset
from vessel.models import Attestation, GoldAlternative, Identity, Location, Review, SearchResponse


def approve(record):
    stamp = datetime(2026, 9, 30, 12, tzinfo=UTC)
    record.reviews = [
        Review(
            reviewer=name,
            role=role,
            decision="approved",
            content_sha256=record.content_digest(),
            reviewed_at=stamp,
        )
        for name, role in [("author", "author"), ("second-human", "independent")]
    ]


def test_review_digest_invalidated(gold):
    approve(gold)
    assert gold.reviewed()
    gold.query += " changed"
    assert not gold.reviewed()


def test_self_review_rejected(gold):
    approve(gold)
    gold.reviews[1].reviewer = "author"
    assert not gold.reviewed()


def test_unresolved_changes(gold):
    approve(gold)
    gold.reviews.append(
        Review(
            reviewer="second-human",
            role="independent",
            decision="changes_requested",
            content_sha256=gold.content_digest(),
            reviewed_at=datetime(2026, 9, 30, 13, tzinfo=UTC),
        )
    )
    assert not gold.reviewed()


def test_duplicates_and_family_leakage(gold):
    second = gold.model_copy(deep=True)
    second.split = "evaluation"
    issues = validate_dataset([gold, second])
    assert any("duplicate" in i for i in issues)
    assert any("crosses" in i for i in issues)


def test_attestation_requires_evidence(gold):
    gold.attestation.bucket = "external_holdout"
    assert any("membership requires" in i for i in validate_dataset([gold]))


def test_freeze_precedes_creation(gold):
    gold.attestation = Attestation(
        bucket="external_holdout",
        frozen_at=gold.created_at,
        index_version="v1",
        evidence_reference="public attestation",
    )
    assert any("precede" in i for i in validate_dataset([gold]))


def test_data_not_required_when_absent():
    with pytest.raises(ValidationError):
        GoldAlternative(evidence_id="bad", document=Identity(), required={"document", "data"})


def test_missing_localization_rejected():
    with pytest.raises(ValidationError):
        GoldAlternative(
            evidence_id="bad", document=Identity(), required={"document", "localization"}
        )


def test_invalid_bbox():
    with pytest.raises(ValidationError):
        Location(bbox=(0.5, 0.1, 0.2, 0.8))


def test_duplicate_ranks():
    with pytest.raises(ValidationError):
        SearchResponse(status="ok", results=[{"rank": 1}, {"rank": 1}])


def test_synthetic_and_unreviewed_release_rejected(gold):
    gold.synthetic = True
    issues = validate_dataset([gold], release=True)
    assert any("synthetic" in i for i in issues)
    assert any("independent" in i for i in issues)
    assert any("exactly 100" in i for i in issues)


def test_complete_core100_gate(gold):
    records = []
    types = [key for key, count in VISUAL_TARGETS.items() for _ in range(count)]
    for i in range(100):
        r = gold.model_copy(deep=True)
        r.query_id = f"q{i}"
        r.family_id = f"family{i}"
        r.domain = DOMAINS[i // 10]
        r.visual_type = types[i]
        r.split = "evaluation"
        r.attestation = Attestation(
            bucket="external_holdout" if i < 40 else "indexed",
            frozen_at=r.created_at - timedelta(days=1),
            index_version="v1",
            evidence_reference="independently supplied freeze statement",
        )
        r.alternatives[0].verification_urls = ["https://example.org/report.pdf"]
        r.alternatives[0].verification_notes = "Test-only gate example, not a real release"
        approve(r)
        records.append(r)
    assert validate_dataset(records, release=True) == []
