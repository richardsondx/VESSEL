# Parallel Turbo characterization

Date: 2026-10-14. Status: documentation characterized 2026-10-14; no
authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /v1/search` on
  `api.parallel.ai` (same endpoint as `parallel`).
- Interface tested: identical JSON body to `parallel` except
  `"mode": "turbo"`: `{"objective": "<query>", "search_queries": ["<query>"],
  "mode": "turbo", "advanced_settings": {"max_results": <k>,
  "excerpt_settings": {"max_chars_per_result": 500}}}`, header
  `x-api-key: <key>`.
- Documented claims: `turbo` is the lowest-latency mode (roughly 200ms),
  trading retrieval depth for speed; four modes exist (turbo, fast, basic,
  advanced).
- Observed behavior: none yet; no live call performed.
- Result types: same as `parallel`: `results[]` entries `{url, title,
  excerpts[], publish_date}`.
- Fetch/content capabilities: none in the search call.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `max_results` pinned to k; excerpt budget pinned to 500
  chars/result; `mode` pinned to `turbo`.
- Run configuration: `PARALLEL_API_KEY`; optional `PARALLEL_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; differs
  from `parallel` only in mode. Cannot score visual/localization/dataset
  components.
- Unknowns: live latency/cost per call; how much retrieval depth turbo loses
  on visual-evidence queries.
- Public primary documentation:
  [Parallel search docs](https://docs.parallel.ai/search/search-quickstart).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
