# SearchApi.io (Bing) characterization

Date: 2026-10-14. Status: documentation characterized from SearchApi.io's
official engine docs (searchapi.io/docs/bing, searchapi.io/docs/duckduckgo-api)
on 2026-10-14; no authenticated live call performed. Full protocol validation
remains pending.

- Date/version tested: 2026-10-14; endpoint `GET /api/v1/search` on
  `www.searchapi.io`.
- Interface tested: `GET https://www.searchapi.io/api/v1/search?engine=bing&q=<query>&num=<n>`,
  header `Authorization: Bearer <key>` (the docs also allow `api_key` as a
  query parameter; the header form is pinned so the key never lands in URLs).
- Documented claims: real-time SERP data across engines; organic results share
  the same structure across engines.
- Observed behavior: none yet; no live call performed.
- Result types: `organic_results[]` entries `{position, title, source, link,
  domain, displayed_link, snippet, ...}`. `position` is retained.
- Fetch/content capabilities: none in the search call; VESSEL uses shared
  fetch under the search_fetch protocol.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `engine` pinned to `bing` so an upstream default change
  cannot silently switch the engine; `num` pinned to `min(k, 50)`.
- Run configuration: `SEARCHAPI_API_KEY`; optional `SEARCHAPI_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components. This is the Bing counterfactual
  to Serper's Google baseline.
- Unknowns: live latency/cost per call.
- Public primary documentation:
  [Bing Search API docs](https://www.searchapi.io/docs/bing).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
