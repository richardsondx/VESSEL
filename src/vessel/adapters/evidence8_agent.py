"""Evidence8 agent-mode provider: LLM reformulation + MCP search tools.

Mirrors the architecture of Evidence8's in-app Research Chat (LLM connected
to Evidence via MCP): an OpenAI model rewrites the raw query into targeted
keyword searches, each executed through the hosted MCP search_visual_evidence
tool, with results merged and normalized like the direct API provider.

This is a distinct retrieval path from the plain evidence8 provider (single
lexical search). Both are benchmarked separately.
"""

import json
import os
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request  # noqa: E402

import httpx  # noqa: E402

from vessel.adapters.base import HTTPProvider  # noqa: E402
from vessel.adapters.evidence8 import normalize_asset  # noqa: E402
from vessel.models import SearchResponse  # noqa: E402

MCP_URL = "https://evidence8.com/mcp"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Corpora the agent may target. Slugs and display names verified against the
# live corpus directory (https://evidence8.com/corpora). Note: the /v1/corpora
# API endpoint omits several searchable corpora, so this list is authoritative.
CORPORA = {
    "macro-public-data": "FRED",
    "world-bank": "World Bank Indicators",
    "sec-filing-visuals": "SEC Filing Visuals",
    "investor-relations": "Company Investor Relations",
    "iea-data": "IEA Energy Charts",
    "ember": "Ember Energy",
    "eia": "U.S. Energy Information Administration",
    "eurostat": "Eurostat",
    "statistics-canada": "Statistics Canada",
    "epoch-ai": "Epoch AI",
    "ghsl": "GHSL Urban Centre Database",
    "bls-data": "U.S. Bureau of Labor Statistics",
    "imf-weo": "IMF World Economic Outlook",
    "our-world-in-data": "Our World in Data",
    "census-visualizations": "U.S. Census Visualizations",
    "unep-emissions-gap": "UNEP Emissions Gap Report",
    "ipcc-wg3-ar6": "IPCC AR6 Working Group III",
    "treasury-fiscal-data": "U.S. Treasury Fiscal Data",
    "ecb-data-portal": "ECB Data Portal",
    "cbo-budget": "CBO Budget and Economic Outlook",
    "zillow-housing-data": "Zillow Housing Data",
    "pew-research": "Pew Research Center",
    "us-drought-monitor": "U.S. Drought Monitor",
    "cred-canada": "CRED Canadian Research Economic Data",
}
KNOWN_CORPORA = list(CORPORA.keys())

REFORMULATE_PROMPT = """You reformulate visual-evidence search queries for a deterministic lexical search engine.

The engine matches on keyword coverage (at least 62% of query keywords must appear in the indexed text). Long natural-language questions FAIL. Short keyword phrases SUCCEED.

Given the user query, produce 2-3 short keyword searches (3-6 words each), each naming the most relevant corpus slug from this list (slug: Display Name):

{corpus_list}

Rules:
- Strip question words (where, show me, what does, can I see).
- Keep concrete nouns: publisher names, indicator names, years, figure numbers.
- Each reformulation should emphasize different keywords, not repeat the same phrase.
- Match the query's publisher to the corpus Display Name (e.g. a FRED query -> macro-public-data, an EIA query -> eia, a World Bank query -> world-bank).

Respond with JSON only: {{"searches": [{{"query": "...", "corpus": "slug or null"}}]}}

User query: {query}"""


class Evidence8Agent(HTTPProvider):
    name = "evidence8-agent"
    key_env = "EVIDENCE8_API_KEY"
    base_env = "EVIDENCE8_BASE_URL"
    default_base = ""
    path = "/v1/search"  # unused; MCP transport instead
    header = "Authorization"

    def __init__(self, config):
        super().__init__(config)
        if self.key:
            self.key = "Bearer " + self.key

    def _proxy_client(self, timeout=120):
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        return httpx.Client(trust_env=False, proxy=proxy, timeout=timeout)

    def _reformulate(self, query):
        """Ask the LLM for targeted keyword searches."""
        body = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": REFORMULATE_PROMPT.format(
                corpus_list="\n".join(f"{s}: {n}" for s, n in CORPORA.items()),
                query=query)}],
            "temperature": 0.2,
            "max_tokens": 300,
        }).encode()
        req = urllib.request.Request(
            OPENAI_URL, data=body, headers={"content-type": "application/json"})
        add_surrogate_to_request(req, "custom.openai", allowed_hosts=["api.openai.com"])
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        text = data["choices"][0]["message"]["content"]
        # Extract JSON from the response.
        start = text.find("{")
        end = text.rfind("}") + 1
        data = json.loads(text[start:end])
        return data.get("searches", [])[:3]

    def _mcp_search(self, query, corpus, limit):
        """Call search_visual_evidence via the hosted MCP endpoint."""
        params = {"query": query, "limit": limit}
        if corpus:
            params["corpus"] = corpus
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "search_visual_evidence", "arguments": params},
        }
        with self._proxy_client() as client:
            r = client.post(
                MCP_URL,
                json=payload,
                headers={
                    "Authorization": self.key,
                    "content-type": "application/json",
                    "accept": "application/json, text/event-stream",
                },
            )
            r.raise_for_status()
            data = r.json()
        # MCP tools/call returns result.content; the search result is JSON text.
        result = data.get("result", {})
        content = result.get("content", [])
        for block in content:
            if block.get("type") == "text":
                return json.loads(block["text"])
        return {"status": "no_match", "results": []}

    def _rerank(self, query, rows):
        """Re-rank merged results using the visual metadata the API returns.

        The raw MCP results carry ticker (e.g. FRED series IDs), chartKind,
        type, tags, and relevance.matchedTerms. This is a general precision
        step: prefer results whose structured identifiers match tokens in the
        query, rather than trusting the lexical order alone.
        """
        import re
        # Extract candidate identifiers: all-caps tokens (tickers like UNRATE),
        # figure references (1.1), and years.
        qtokens = set(re.findall(r"[A-Z]{2,}[A-Z0-9]*", query.upper()))
        figures = set(re.findall(r"(?:figure|fig\.?)\s*([0-9.]+)", query, re.I))
        years = set(re.findall(r"\b(19|20)\d{2}\b", query))
        qwords = set(re.findall(r"[a-z]{3,}", query.lower()))

        def score(row):
            asset = row.get("asset", row)
            s = 0.0
            # Ticker / series-ID match is the strongest signal.
            ticker = str(asset.get("ticker", "")).upper()
            if ticker and ticker in qtokens:
                s += 10.0
            # Figure number match.
            title = str(asset.get("title", ""))
            for fig in figures:
                if fig in title:
                    s += 6.0
            # Year match in title or date.
            text = (title + " " + str(asset.get("date", ""))).lower()
            for y in years:
                if y in text:
                    s += 2.0
            # Keyword overlap with title + tags.
            tags = " ".join(str(t) for t in asset.get("tags", [])).lower()
            overlap = len(qwords & set(re.findall(r"[a-z]{3,}", title.lower() + " " + tags)))
            s += overlap * 0.5
            # Prefer actual charts over generic pages.
            if asset.get("type", "").lower() in ("chart", "figure", "graph", "map"):
                s += 1.5
            # Blend with the engine's own relevance score.
            rel = asset.get("relevance", {}) or {}
            try:
                s += float(rel.get("score", 0) or 0)
            except (TypeError, ValueError):
                pass
            return s

        return sorted(rows, key=score, reverse=True)

    def search(self, query, k, context=None):
        searches = self._reformulate(query)
        if not searches:
            searches = [{"query": query, "corpus": None}]
        seen = set()
        merged = []
        for s in searches:
            try:
                raw = self._mcp_search(s["query"], s.get("corpus"), k)
            except Exception:
                continue
            if raw.get("status") != "ok":
                continue
            for row in raw.get("results", []):
                asset = row.get("asset", row)
                aid = asset.get("assetId") or asset.get("id") or str(row)
                if aid in seen:
                    continue
                seen.add(aid)
                merged.append(row)
                if len(merged) >= k:
                    break
            if len(merged) >= k:
                break
        # Re-rank using visual metadata before normalizing.
        merged = self._rerank(query, merged)
        results = [
            normalize_asset(row, rank, self.base or "https://evidence8.com")
            for rank, row in enumerate(merged[:k], 1)
        ]
        return SearchResponse(status="ok" if results else "no_match", results=results)
