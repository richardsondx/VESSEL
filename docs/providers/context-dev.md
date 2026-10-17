# Context.dev characterization

Date: 2026-10-14. Status: documentation characterized from Context.dev's public
OpenAPI document (docs.context.dev/openapi.json, version 1.0.0) on 2026-10-14;
no authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; OpenAPI 3.1.0, operation `POST /web/search`,
  server `https://api.context.dev/v1`.
- Interface tested: `POST https://api.context.dev/v1/web/search` with JSON body
  `{"query": "<query>", "numResults": <n>}`, header
  `Authorization: Bearer <key>` (bearerAuth per the OpenAPI security scheme).
- Documented claims: web search returning ranked results with optional
  per-result markdown scraping and highlights; results ordered by relevance.
- Observed behavior: none yet; no live call performed.
- Result types: `results[]` entries `{url, title, description, relevance,
  markdown: {...}, highlights: {...}}`. `description` maps to the snippet;
  `relevance` is high/medium/low. Markdown/highlights are not requested.
- Fetch/content capabilities: `markdownOptions`/`highlightsOptions` exist;
  both pinned off (search protocol pins one request, no provider fetch).
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `numResults` schema requires 10-100, so the adapter sends
  `max(k, 10)` and slices to k locally. Cost: 1 credit per 10 results per the
  OpenAPI `x-mint` annotation.
- Run configuration: `CONTEXT_DEV_API_KEY`; optional `CONTEXT_DEV_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components. Note the minimum-10
  `numResults`: the engine always retrieves at least 10, so cost and recall
  are computed on a slightly wider retrieval than k<10 engines.
- Unknowns: live latency/cost per call.
- Public primary documentation:
  [Context.dev OpenAPI](https://docs.context.dev/openapi.json)
  (`/web/search` operation).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
