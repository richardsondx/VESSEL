import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol as TypingProtocol

import httpx

from vessel.artifacts import ArtifactStore, sanitize
from vessel.models import Observation, ProviderConfig, SearchResponse


class BudgetExceeded(Exception):
    pass


@dataclass
class Budget:
    max_usd: float
    max_requests: int
    requests: int = 0
    reserved_usd: float = 0

    def reserve(self, ceiling: float):
        if self.requests >= self.max_requests or self.reserved_usd + ceiling > self.max_usd + 1e-9:
            raise BudgetExceeded("request or spending cap reached")
        self.requests += 1
        self.reserved_usd += ceiling


@dataclass
class Context:
    budget: Budget
    artifacts: ArtifactStore
    client: httpx.Client


class Provider(TypingProtocol):
    name: str

    def search(self, query: str, k: int, context: Context) -> SearchResponse: ...


class HTTPProvider:
    name = ""
    key_env = ""
    base_env = ""
    default_base = ""
    path = ""
    header = "X-API-Key"

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.key = os.getenv(self.key_env, "")
        self.base = os.getenv(self.base_env, self.default_base).rstrip("/")

    def configured(self) -> bool:
        return bool(
            self.base
            and (
                self.key
                or self.name == "evidence8"
                or (self.name == "keenable" and self.config.keyless)
            )
        )

    def payload(self, query: str, k: int) -> dict:
        raise NotImplementedError

    def normalize(self, raw: dict, k: int) -> SearchResponse:
        raise NotImplementedError

    def search(self, query: str, k: int, context: Context) -> SearchResponse:
        if not self.configured():
            return SearchResponse(status="skipped", reason="provider not configured")
        ceiling = self.config.request_cost_ceiling_usd
        if ceiling is None:
            return SearchResponse(status="skipped", reason="request cost ceiling not configured")
        start = time.perf_counter()
        try:
            context.budget.reserve(ceiling)
        except BudgetExceeded:
            return SearchResponse(
                status="budget_exhausted", reason="request or spending cap reached"
            )
        headers = {self.header: self.key} if self.key else {}
        path = self.path
        if self.name == "keenable" and not self.key and self.config.keyless:
            path += "/public"
            headers["X-Keenable-Title"] = "VESSEL"
        observations = []
        try:
            response = context.client.post(
                self.base + path, json=self.payload(query, k), headers=headers, timeout=30
            )
            response.raise_for_status()
            raw = response.json()
            if not isinstance(raw, dict):
                raise ValueError("provider returned a non-object response")
            clean = sanitize(raw, (self.key, os.getenv(self.key_env, "")))
            import json

            sha = context.artifacts.put_bytes(json.dumps(clean, sort_keys=True).encode())
            observations.append(
                Observation(kind="provider_response", status="ok", artifact_sha256=sha)
            )
            result = self.normalize(raw, k)
        except httpx.HTTPStatusError as error:
            result = SearchResponse(status="error", reason=f"HTTP {error.response.status_code}")
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as error:
            result = SearchResponse(
                status="error", reason=f"response/transport failure: {type(error).__name__}"
            )
        result.requests = 1
        result.reserved_cost_usd = ceiling
        result.latency_ms = (time.perf_counter() - start) * 1000
        result.observations.extend(observations)
        if result.reported_cost_usd is not None and result.reported_cost_usd > ceiling:
            result.observations.append(Observation(kind="budget", status="ceiling_underestimated"))
            # Stop future calls if the configured ceiling was not conservative.
            context.budget.reserved_usd += result.reported_cost_usd - ceiling
            context.budget.max_requests = context.budget.requests
        return result


class ReplayProvider:
    def __init__(self, name: str, fixture: Path):
        import json

        self.name = name
        self.fixture = json.loads(fixture.read_text())
        if self.fixture.get("synthetic") is not True:
            raise ValueError("development fixture must be explicitly synthetic")

    def search(self, query: str, k: int, context: Context) -> SearchResponse:
        raw = self.fixture.get("responses", {}).get(self.name, {}).get(query)
        if raw is None:
            return SearchResponse(status="skipped", reason="no replay fixture", replay=True)
        result = SearchResponse.model_validate(raw)
        result.results = [r for r in result.results if r.rank <= k]
        result.requests = 0
        result.latency_ms = None
        result.reported_cost_usd = None
        result.reserved_cost_usd = 0
        result.replay = True
        return result
