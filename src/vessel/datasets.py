import json
from collections import Counter
from pathlib import Path

from vessel.models import GoldRecord, digest

DOMAINS = [
    "economics",
    "finance",
    "energy",
    "ai",
    "climate",
    "demographics",
    "labor",
    "housing",
    "science",
    "policy",
]
VISUAL_TARGETS = {"chart": 55, "table": 15, "map": 10, "multi_panel": 10, "diagram": 5, "other": 5}


def load_dataset(path: Path) -> list[GoldRecord]:
    records = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            try:
                records.append(GoldRecord.model_validate_json(line))
            except ValueError as error:
                raise ValueError(f"line {line_number}: {error}") from error
    if not records:
        raise ValueError("dataset is empty")
    return records


def save_dataset(path: Path, records: list[GoldRecord]):
    path.write_text("".join(r.model_dump_json() + "\n" for r in records))


def dataset_digest(records: list[GoldRecord]) -> str:
    return digest([r.model_dump(mode="json") for r in records])


def validate_dataset(records: list[GoldRecord], release: bool = False) -> list[str]:
    issues = []
    ids = [r.query_id for r in records]
    if len(set(ids)) != len(ids):
        issues.append("duplicate query IDs")
    families = {}
    for r in records:
        if r.family_id in families and families[r.family_id] != r.split:
            issues.append(f"{r.family_id}: evidence family crosses development/evaluation splits")
        families[r.family_id] = r.split
        if r.attestation.bucket != "unknown" or (release and r.attestation.frozen_at):
            a = r.attestation
            if not (a.frozen_at and a.index_version and a.evidence_reference):
                issues.append(
                    f"{r.query_id}: membership requires freeze evidence and index version"
                )
            elif a.frozen_at >= r.created_at:
                issues.append(f"{r.query_id}: freeze must precede query creation")
        if release:
            if r.synthetic:
                issues.append(f"{r.query_id}: synthetic record cannot be released")
            if not r.reviewed():
                issues.append(f"{r.query_id}: current author/independent approvals required")
            if r.split != "evaluation":
                issues.append(f"{r.query_id}: release requires evaluation split")
            if not all(g.verification_urls and g.verification_notes for g in r.alternatives):
                issues.append(f"{r.query_id}: primary validation references/notes required")
            if not (
                r.attestation.frozen_at
                and r.attestation.index_version
                and r.attestation.evidence_reference
            ):
                issues.append(f"{r.query_id}: provider freeze attestation required for release")
    if release:
        if len(records) != 100:
            issues.append("Core-100 requires exactly 100 queries")
        counts = Counter(r.domain for r in records)
        if any(counts[d] != 10 for d in DOMAINS):
            issues.append("Core-100 requires ten queries per domain")
        if sum(r.attestation.bucket == "external_holdout" for r in records) < 40:
            issues.append("Core-100 requires forty verified external-holdout queries")
        if dict(Counter(r.visual_type for r in records)) != VISUAL_TARGETS:
            issues.append("Core-100 visual-type targets not met")
    return issues


def read_json(path: Path):
    return json.loads(path.read_text())
