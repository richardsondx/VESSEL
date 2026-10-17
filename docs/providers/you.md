# You.com characterization

Date: 2026-10-14. Status: documentation characterized from You.com's published
OpenAPI behavior and integration references on 2026-10-14; no authenticated live
call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `/v1/search` on `ydc-index.io`.
- Interface tested: `POST https://ydc-index.io/v1/search` with JSON body
  `{"query": "<query>", "count": <k>}`, header `X-API-Key: <key>`.
  (A GET form with the same query params is also documented; POST is pinned.)
- Documented claims: You.com's own index with relevance ranking and snippet
  extraction; web and news sections.
- Observed behavior: none yet; no live call performed.
- Result types: `results.web[]` entries `{title, url, description,
  snippets[], page_age}`. Adapter prefers `description`, falls back to
  `snippets[0]`; `page_age` maps to the published date when present.
- Fetch/content capabilities: separate `/v1/contents` extraction exists; VESSEL
  does not call it (search protocol pins one request; shared fetch otherwise).
- Observable ranking: preserve returned array order; no inferred confidence.
  A response with no `web` section normalizes to no results.
- Limits/quotas: `count` pinned to k. News section is ignored, not coerced into
  source cards.
- Run configuration: `YDC_API_KEY`; optional `YOU_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call; exact `count` ceiling semantics.
- Public primary documentation:
  [You.com search integration reference](https://github.com/janhq/jan/commit/2cca0ab2347de04e7e8daf534da49483c8ab79df)
  (documents POST https://ydc-index.io/v1/search with X-API-Key per You.com's
  published OpenAPI specs).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
