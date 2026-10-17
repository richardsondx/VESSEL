# Parallel characterization

Date: 2026-10-14. Status: documentation characterized from Parallel's public
API docs (docs.parallel.ai) and the parallel-web-systems-pair-programming docs
mirror on 2026-10-14; no authenticated live call performed. Full protocol
validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /v1/search` on
  `api.parallel.ai`.
- Interface tested: `POST https://api.parallel.ai/v1/search` with JSON body
  `{"objective": "<query>", "search_queries": ["<query>"], "mode": "basic",
  "advanced_settings": {"max_results": <k>, "excerpt_settings":
  {"max_chars_per_result": 500}}}`, header `x-api-key: <key>`.
- Documented claims: ranked URLs with LLM-optimized excerpts; modes trade
  latency against retrieval depth.
- Observed behavior: none yet; no live call performed.
- Result types: `results[]` entries `{url, title, excerpts[], publish_date}`.
  Adapter joins `excerpts` into the snippet.
- Fetch/content capabilities: separate `/v1/extract` exists; VESSEL does not
  call it (search protocol pins one request).
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `max_results` pinned to k; excerpt budget pinned to 500
  chars/result. `mode` pinned to `basic` (the documented default,
  roughly 3s); see `parallel-turbo` for the turbo mode point.
- Run configuration: `PARALLEL_API_KEY`; optional `PARALLEL_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components. The `objective` and the single
  keyword query carry the same text, so no extra query engineering advantages
  one engine over another.
- Unknowns: live latency/cost per call.
- Public primary documentation:
  [Parallel search quickstart](https://docs.parallel.ai/search/search-quickstart),
  [search API reference](https://docs.parallel.ai/api-reference/search/search).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
