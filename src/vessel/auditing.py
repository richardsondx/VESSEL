"""Human audit gate bound to the exact archived response population."""

import json
from datetime import UTC, datetime
from pathlib import Path

from vessel.artifacts import atomic_json
from vessel.datasets import dataset_digest, validate_dataset
from vessel.models import GoldRecord, RunManifest, digest
from vessel.runner import read_receipt, receipt_path


def audit_fingerprint(root: Path, manifest: RunManifest, records: list[GoldRecord]) -> str:
    receipts = []
    for provider in manifest.config.providers:
        for record in records:
            path = receipt_path(root, provider.name, record.query_id)
            receipt = read_receipt(path)
            if receipt["provider"] != provider.name or receipt["query_id"] != record.query_id:
                raise ValueError("receipt identity mismatch")
            receipts.append(digest(receipt))
    return digest(
        {
            "dataset": dataset_digest(records),
            "config": manifest.config_sha256,
            "code": manifest.code_sha256,
            "receipts": receipts,
        }
    )


def audit_valid(root: Path, manifest: RunManifest, records: list[GoldRecord]) -> bool:
    path = root / "audit.json"
    if not path.exists():
        return False
    audit = json.loads(path.read_text())
    return bool(
        audit.get("decision") == "approved"
        and audit.get("reviewer")
        and audit.get("notes")
        and audit.get("fingerprint") == audit_fingerprint(root, manifest, records)
    )


def record_audit(root: Path, reviewer: str, notes: str):
    if not reviewer.strip() or not notes.strip():
        raise ValueError("actual human reviewer and audit notes are required")
    manifest = RunManifest.model_validate_json((root / "manifest.json").read_text())
    records = [
        GoldRecord.model_validate(r) for r in json.loads((root / "dataset.json").read_text())
    ]
    if manifest.status != "complete":
        raise ValueError("audit requires a complete run")
    audit = {
        "decision": "approved",
        "reviewer": reviewer,
        "notes": notes,
        "reviewed_at": datetime.now(UTC).isoformat(),
        "fingerprint": audit_fingerprint(root, manifest, records),
    }
    atomic_json(root / "audit.json", audit)
    manifest.publication_eligible = (
        manifest.mode == "live"
        and not validate_dataset(records, release=True)
        and dataset_digest(records) == manifest.dataset_sha256
    )
    atomic_json(root / "manifest.json", manifest)
    return audit
