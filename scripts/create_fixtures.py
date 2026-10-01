"""Generate SYNTHETIC software fixtures, never benchmark gold or measured results."""

from datetime import UTC, datetime
from pathlib import Path

from vessel.artifacts import atomic_json
from vessel.datasets import DOMAINS, save_dataset
from vessel.models import (
    Asset,
    Bundle,
    Dataset,
    EvidenceResult,
    GoldAlternative,
    GoldRecord,
    Identity,
    Location,
    SearchResponse,
    Source,
)

root = Path(__file__).resolve().parents[1]
records = []
responses = {p: {} for p in ("evidence8", "keenable", "exa", "serper")}
for i in range(20):
    document = f"https://example.org/reports/fixture-{i}.pdf"
    visual = f"https://example.org/visuals/fixture-{i}.png"
    dataset = f"https://example.org/data/fixture-{i}.csv"
    location = Location(page_index=i % 4, figure=str(i + 1))
    require_data = i % 3 == 0
    alternative = GoldAlternative(
        evidence_id=f"synthetic-{i}",
        document=Identity(urls=[document]),
        visual=Identity(urls=[visual]),
        authoritative_urls=[document],
        locations=[location],
        datasets=[Identity(urls=[dataset])] if require_data else [],
        data_available=require_data,
        required={"document", "visual", "primary", "localization"}
        | ({"data"} if require_data else set()),
    )
    record = GoldRecord(
        query_id=f"fixture-{i:02}",
        query=f"SYNTHETIC: retrieve fixture visual {i}",
        family_id=f"fixture-family-{i // 2}",
        domain=DOMAINS[i // 2],
        visual_type="chart",
        query_type="descriptive",
        created_at=datetime(2026, 9, 30, tzinfo=UTC),
        alternatives=[alternative],
        synthetic=True,
    )
    records.append(record)
    for p_index, provider in enumerate(responses):
        bundle = Bundle(
            source=Source(document_url=document),
            visual=Asset(url=visual, rendition="publisher") if i % 4 <= p_index else None,
            location=location if i % 4 <= p_index else None,
            datasets=[Dataset(url=dataset)] if require_data and p_index >= 2 else [],
        )
        response = SearchResponse(
            status="ok",
            results=[
                EvidenceResult(
                    rank=1, title=f"Synthetic fixture visual {i}", url=document, bundles=[bundle]
                )
            ],
            replay=True,
        )
        responses[provider][record.query] = response.model_dump(mode="json")
save_dataset(root / "data/synthetic-pilot.jsonl", records)
atomic_json(root / "tests/fixtures/replay.json", {"synthetic": True, "responses": responses})
