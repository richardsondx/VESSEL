# Firecrawl characterization

Date: 2026-10-14. Status: documentation characterized from Firecrawl's public
docs (docs.firecrawl.dev) and the firecrawl repo on 2026-10-14; no authenticated
live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /v2/search` on
  `api.firecrawl.dev`.
- Interface tested: `POST https://api.firecrawl.dev/v2/search` with JSON body
  `{"query": "<query>", "limit": <k>, "sources": ["web"]}`, header
  `Authorization: Bearer <key>`.
- Documented claims: web search with optional in-line content scraping;
  `sources` selects web/news/images.
- Observed behavior: none yet; no live call performed.
- Result types: `{"success": true, "data": {"web": [{url, title, description,
  position}], "news": ..., "images": ...}}`. Older v2 variants return `data`
  as a flat list; the adapter accepts both and reads `web` when present.
  `description` maps to the snippet; `position` is retained.
- Fetch/content capabilities: `scrapeOptions` in-line scraping exists; pinned
  off (search protocol pins one request, no provider fetch; every response
  carries `creditsUsed` for cost accounting).
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `limit` pinned to k (documented max 100). Only the `web`
  source is requested; news/images are never requested.
- Run configuration: `FIRECRAWL_API_KEY`; optional `FIRECRAWL_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call; which `data` envelope shape the live
  endpoint returns (both are handled, but pin one after the first live call).
- Public primary documentation:
  [Firecrawl search docs](https://docs.firecrawl.dev/features/search),
  [firecrawl repo](https://github.com/mendableai/firecrawl).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
