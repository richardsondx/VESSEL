from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from vessel.adapters.base import Budget, Context
from vessel.artifacts import ArtifactStore
from vessel.models import (
    Asset,
    Bundle,
    Dataset,
    GoldAlternative,
    GoldRecord,
    Identity,
    Location,
    Source,
)


@pytest.fixture
def gold():
    return GoldRecord(
        query_id="q1",
        query="Find original evidence",
        family_id="f1",
        domain="energy",
        visual_type="chart",
        query_type="descriptive",
        created_at=datetime(2026, 9, 30, tzinfo=UTC),
        alternatives=[
            GoldAlternative(
                evidence_id="e1",
                document=Identity(urls=["https://example.org/report.pdf"]),
                visual=Identity(urls=["https://example.org/visual.png"]),
                authoritative_urls=["https://example.org/report.pdf"],
                locations=[Location(page_index=4, figure="3.8")],
                data_available=True,
                datasets=[Identity(urls=["https://example.org/data.csv"])],
                required={"document", "visual", "primary", "localization", "data"},
            )
        ],
    )


@pytest.fixture
def bundle():
    return Bundle(
        source=Source(document_url="https://example.org/report.pdf"),
        visual=Asset(url="https://example.org/visual.png", rendition="publisher"),
        location=Location(page_index=4, figure="3.8"),
        datasets=[Dataset(url="https://example.org/data.csv")],
    )


@pytest.fixture
def context(tmp_path: Path):
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))
    ) as client:
        yield Context(Budget(1, 100), ArtifactStore(tmp_path / "objects"), client)
