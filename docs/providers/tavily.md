# Tavily characterization

Date: 2026-10-14. Status: documentation characterized from Tavily's public API
docs and integration references on 2026-10-14; no authenticated live call
performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /search` on `api.tavily.com`.
- Interface tested: `POST https://api.tavily.com/search` with JSON body
  `{"query": "<query>", "max_results": <k>, "search_depth": "basic",
  "include_answer": false}`, header `Authorization: Bearer <key>` (key never in
  the body).
- Documented claims: real-time search for agents; relevance `score` per result.
- Observed behavior: none yet; no live call performed.
- Result types: `results[]` entries `{title, url, content, score,
  published_date}`. Adapter maps `content` to the snippet.
- Fetch/content capabilities: `include_raw_content` exists; pinned off (search
  protocol pins one request, no provider fetch).
- Observable ranking: preserve returned array order; `score` is retained only
  in the archived raw response, not used for ranking or scoring.
- Limits/quotas: `max_results` 0-20, pinned to k. `search_depth` pinned to
  `basic` (1 credit); `advanced` is a deliberately separate cost/latency point
  and is not run unless configured.
- Run configuration: `TAVILY_API_KEY`; optional `TAVILY_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call.
- Public primary documentation:
  [Tavily API docs](https://docs.tavily.com/documentation/api-reference/endpoint/search)
  (endpoint, Bearer auth, `query`/`max_results`/`search_depth` fields).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
