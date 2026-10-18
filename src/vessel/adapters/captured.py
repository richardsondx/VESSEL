"""File-backed providers for browser-captured engine results.

Some engines are only drivable through their website (no API). Their
results are captured in the browser, stored as JSON, and replayed through
this provider. The capture file is the pinned, auditable request artifact
for that engine: it records exactly what the engine returned, when it was
captured, and for which queries.

Capture format (JSON):
    {"queries": [
        {"query_id": "q01", "query": "<exact query text>",
         "captured_at": "<UTC ISO timestamp>",
         "results": [{"url": ..., "title": ..., "snippet": ...}, ...]},
        ...
    ]}

Entries are matched on normalized query text (stripped, casefolded).
"""

import json
import os
import time
from pathlib import Path

from vessel.adapters.base import BudgetExceeded
from vessel.adapters.web import documents
from vessel.models import SearchResponse


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


class CapturedResultsProvider:
    """Replays browser-captured results from a JSON capture file."""

    name = "keenable-browser"
    capture_env = "KEENABLE_BROWSER_CAPTURE"

    def __init__(self, config):
        self.config = config
        self._entries: list[dict] | None = None

    def _capture_path(self) -> Path | None:
        raw = os.getenv(self.capture_env, "")
        return Path(raw) if raw.strip() else None

    def configured(self) -> bool:
        path = self._capture_path()
        return bool(path and path.exists())

    def _load(self) -> list[dict]:
        if self._entries is None:
            path = self._capture_path()
            data = json.loads(path.read_text())
            queries = data.get("queries")
            if not isinstance(queries, list):
                raise ValueError("capture file must contain a 'queries' array")
            self._entries = queries
        return self._entries

    def search(self, query: str, k: int, context) -> SearchResponse:
        if not self.configured():
            return SearchResponse(status="skipped", reason="capture file not configured")
        ceiling = self.config.request_cost_ceiling_usd
        if ceiling is None:
            return SearchResponse(
                status="skipped", reason="request cost ceiling not configured"
            )
        start = time.perf_counter()
        try:
            context.budget.reserve(ceiling)
        except BudgetExceeded:
            return SearchResponse(
                status="budget_exhausted", reason="request or spending cap reached"
            )
        wanted = _normalize(query)
        entry = next(
            (e for e in self._load() if _normalize(e.get("query", "")) == wanted),
            None,
        )
        if entry is None:
            return SearchResponse(
                status="error", reason="query not found in capture file"
            )
        response = documents({"results": entry.get("results", [])}, "results", k)
        response.latency_ms = (time.perf_counter() - start) * 1000
        return response
