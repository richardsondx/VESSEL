from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
    model_validator,
)

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def digest(value: object) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, allow_inf_nan=False)


class Protocol(StrEnum):
    SEARCH = "search"
    SEARCH_FETCH = "search_fetch"
    EVIDENCE = "evidence"


class Location(Model):
    page_index: int | None = Field(default=None, ge=0)
    page_label: str | None = None
    figure: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    locator: str | None = None

    @model_validator(mode="after")
    def validate_box(self):
        if self.bbox and not (
            0 <= self.bbox[0] < self.bbox[2] <= 1 and 0 <= self.bbox[1] < self.bbox[3] <= 1
        ):
            raise ValueError("bbox must be normalized x0,y0,x1,y1")
        return self


class Source(Model):
    document_url: HttpUrl | None = None
    document_id: str | None = None
    document_sha256: Digest | None = None  # computed by shared fetch, not provider assertion
    publisher: str | None = None
    publisher_id: str | None = None
    data_originator: str | None = None
    document_title: str | None = None
    published_at: str | None = None
    retrieved_at: datetime | None = None
    version: str | None = None


class Asset(Model):
    url: HttpUrl | None = None
    sha256: Digest | None = None  # computed bytes in the artifact store
    rendition: Literal["publisher", "crop", "capture", "generated", "unknown"] = "unknown"
    media_type: str | None = None
    perceptual_hash: str | None = None  # diagnostic only


class Dataset(Model):
    url: HttpUrl | None = None
    dataset_id: str | None = None
    sha256: Digest | None = None


class Bundle(Model):
    source: Source = Field(default_factory=Source)
    visual: Asset | None = None
    location: Location | None = None
    datasets: list[Dataset] = Field(default_factory=list)
    rights: str | None = None
    methodology_url: HttpUrl | None = None
    reproducibility_url: HttpUrl | None = None
    derivation: str | None = None


class EvidenceResult(Model):
    rank: int = Field(ge=1)
    provider_id: str | None = None
    title: str = ""
    url: HttpUrl | None = None
    snippet: str | None = None
    bundles: list[Bundle] = Field(default_factory=list)
    provider_position: int | None = None


class Observation(Model):
    kind: str
    status: str
    bytes: int = Field(default=0, ge=0)
    artifact_sha256: Digest | None = None
    truncated: bool = False
    detail: str | None = None


class SearchResponse(Model):
    status: Literal["ok", "no_match", "skipped", "error", "budget_exhausted"]
    results: list[EvidenceResult] = Field(default_factory=list)
    reason: str | None = None
    requests: int = Field(default=0, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    reported_cost_usd: float | None = Field(default=None, ge=0)
    reserved_cost_usd: float = Field(default=0, ge=0)
    observations: list[Observation] = Field(default_factory=list)
    request_id: str | None = None
    replay: bool = False

    @model_validator(mode="after")
    def ranks(self):
        ranks = [r.rank for r in self.results]
        if ranks != sorted(set(ranks)):
            raise ValueError("result ranks must be unique and ascending")
        if self.status != "ok" and self.results:
            raise ValueError("non-ok response cannot contain results")
        return self


class Identity(Model):
    urls: list[HttpUrl] = Field(default_factory=list)
    sha256: list[Digest] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)


class GoldAlternative(Model):
    evidence_id: str
    document: Identity
    visual: Identity = Field(default_factory=Identity)
    authoritative_urls: list[HttpUrl] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    datasets: list[Identity] = Field(default_factory=list)
    data_available: bool = False
    original_required: bool = True
    version: str | None = None
    accepted_rights: list[str] = Field(default_factory=list)
    methodology: Identity = Field(default_factory=Identity)
    reproducibility: Identity = Field(default_factory=Identity)
    required: set[
        Literal[
            "document",
            "visual",
            "primary",
            "localization",
            "data",
            "version",
            "rights",
            "methodology",
            "reproducibility",
        ]
    ] = Field(default_factory=lambda: {"document", "visual", "primary", "localization"})
    verification_urls: list[HttpUrl] = Field(default_factory=list)
    verification_notes: str = ""

    @field_serializer("required")
    def serialize_required(self, required):
        return sorted(required)

    @model_validator(mode="after")
    def requirements(self):
        if not self.required or "document" not in self.required:
            raise ValueError("a gold alternative must require document identity")
        if "data" in self.required and (not self.data_available or not self.datasets):
            raise ValueError("data can only be required when available and identified")
        if "localization" in self.required and not self.locations:
            raise ValueError("localization requires an accepted location")
        if "primary" in self.required and not self.authoritative_urls:
            raise ValueError("primary requires independently verified authoritative URLs")
        if "version" in self.required and not self.version:
            raise ValueError("version requirement needs an explicit vintage")
        if "rights" in self.required and not self.accepted_rights:
            raise ValueError("rights requirement needs independently accepted statements")
        for name in ("methodology", "reproducibility"):
            if name in self.required and not getattr(self, name).urls:
                raise ValueError(f"{name} requirement needs independently accepted URLs")
        return self


class Review(Model):
    reviewer: str
    role: Literal["author", "independent"]
    decision: Literal["approved", "changes_requested"]
    content_sha256: Digest
    reviewed_at: AwareDatetime
    notes: str = ""


class Attestation(Model):
    bucket: Literal["indexed", "known_unindexed", "external_holdout", "unknown"] = "unknown"
    provider: str = "evidence8"
    frozen_at: AwareDatetime | None = None
    index_version: str | None = None
    evidence_reference: str | None = None


class GoldRecord(Model):
    query_id: str
    query: str = Field(min_length=1)
    family_id: str
    domain: Literal[
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
    visual_type: Literal["chart", "table", "map", "multi_panel", "diagram", "other"]
    query_type: str
    split: Literal["development", "evaluation"] = "development"
    created_at: AwareDatetime
    alternatives: list[GoldAlternative] = Field(min_length=1)
    attestation: Attestation = Field(default_factory=Attestation)
    reviews: list[Review] = Field(default_factory=list)
    synthetic: bool = False

    def content_digest(self) -> str:
        return digest(self.model_dump(mode="json", exclude={"reviews"}))

    def reviewed(self) -> bool:
        approvals = [
            r
            for r in self.reviews
            if r.decision == "approved" and r.content_sha256 == self.content_digest()
        ]
        authors = {r.reviewer for r in approvals if r.role == "author"}
        independent = {r.reviewer for r in approvals if r.role == "independent"}
        unresolved = any(
            r.decision == "changes_requested"
            and r.content_sha256 == self.content_digest()
            and not any(
                a.reviewer == r.reviewer and a.reviewed_at > r.reviewed_at for a in approvals
            )
            for r in self.reviews
        )
        return bool(authors and independent and authors.isdisjoint(independent) and not unresolved)


class Adjudication(Model):
    query_id: str
    evidence_id: str
    bundle_sha256: Digest
    decision: Literal["equivalent", "not_equivalent"]
    reviewer: str
    reason: str = Field(min_length=1)


class FetchLimits(Model):
    max_documents: int = Field(default=5, ge=1, le=5)
    max_bytes: int = Field(default=20 * 1024 * 1024, ge=1)
    timeout_seconds: float = Field(default=60, gt=0, le=60)
    max_pages: int = Field(default=200, ge=1, le=200)
    max_text_chars: int = Field(default=100000, ge=1, le=100000)
    max_assets: int = Field(default=200, ge=1)


class ProviderConfig(Model):
    name: Literal["evidence8", "keenable", "exa", "serper", "keenable_evidence8"]
    request_cost_ceiling_usd: float | None = Field(default=None, ge=0)
    mode: str | None = None
    corpus: str = "all"
    country: str = "us"
    language: str = "en"
    keyless: bool = False


class RunConfig(Model):
    benchmark_version: str = "development-v0.1"
    protocol: Protocol = Protocol.EVIDENCE
    k: int = Field(default=10, ge=1, le=10)
    providers: list[ProviderConfig] = Field(min_length=1)
    max_cost_usd: float = Field(default=0, ge=0)
    max_requests: int = Field(default=1000, ge=1)
    fetch: FetchLimits = Field(default_factory=FetchLimits)
    seed: int = 17

    @model_validator(mode="after")
    def unique_providers(self):
        if len({p.name for p in self.providers}) != len(self.providers):
            raise ValueError("duplicate provider configuration")
        return self


class RunManifest(Model):
    schema_version: str = "vessel.run.v1"
    run_id: str
    benchmark_version: str
    dataset_sha256: Digest
    config_sha256: Digest
    code_sha256: Digest
    code_artifact_sha256: Digest | None = None
    dependency_lock_sha256: Digest | None = None
    started_at: datetime
    completed_at: datetime | None = None
    config: RunConfig
    mode: Literal["live", "replay"]
    status: Literal["running", "complete", "incomplete"] = "running"
    dataset_release_ready: bool = False
    publication_eligible: bool = False
    requests: int = 0
    reserved_cost_usd: float = 0
    freeze_attestations: list[Attestation] = Field(default_factory=list)
