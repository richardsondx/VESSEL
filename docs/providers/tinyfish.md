# TinyFish characterization

Date: 2026-10-14. Status: documentation characterized from TinyFish's official
Search API reference (docs.tinyfish.ai/search-api/reference, updated
2026-10-10) and the tinyfish-cookbook repo on 2026-10-14; no authenticated
live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `GET https://api.search.tinyfish.ai`
  (root path).
- Interface tested: `GET https://api.search.tinyfish.ai?query=<query>`, header
  `X-API-Key: <key>`. Optional geo/language params (`location`, `language`)
  are not pinned.
- Documented claims: rank-stable structured JSON for agent retrieval; free up
  to 12,000 requests/day per key, then HTTP 402.
- Observed behavior: none yet; no live call performed.
- Result types: `{"query": ..., "results": [{position, site_name, title,
  snippet, url, date}], "total_results": n, "page": 0}`. `position` is
  retained; `date` is not mapped to a published date (field semantics vary by
  result type).
- Fetch/content capabilities: separate Fetch API (`api.fetch.tinyfish.ai`)
  exists; VESSEL does not call it (search protocol pins one request).
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: no documented result-count parameter; the endpoint pages
  with `page` (0-10) but the adapter requests page 0 only and slices to k.
  30 requests/minute per key.
- Run configuration: `TINYFISH_API_KEY`; optional `TINYFISH_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components. NEEDLE reported a 27.7% error
  rate; expect skips, not scores.
- Unknowns: live latency per call; how many results page 0 returns.
- Public primary documentation:
  [TinyFish Search API reference](https://docs.tinyfish.ai/search-api/reference),
  [tinyfish-cookbook](https://github.com/tinyfish-io/tinyfish-cookbook).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
