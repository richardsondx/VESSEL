# Brave Search characterization

Date: 2026-10-14. Status: documentation characterized from Brave's public API
references (brave-search-skills repo, api-dashboard.search.brave.com); no
authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `/res/v1/web/search` under Brave Search API v1.
- Interface tested: `GET https://api.search.brave.com/res/v1/web/search?q=<query>&count=<n>`,
  header `X-Subscription-Token: <key>` (not Bearer).
- Documented claims: independent Brave index; ranked web results with title, URL,
  description and optional extra snippets.
- Observed behavior: none yet; no live call performed.
- Result types: `web.results[]` entries `{title, url, description, extra_snippets[],
  age}`. Adapter maps `description` to the snippet.
- Fetch/content capabilities: none in the search call; VESSEL uses shared fetch
  under the search_fetch protocol.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `count` 1-20 per page; pinned at `min(k, 20)`. Adapter sends
  `country` (upper-cased config country) and `search_lang`.
- Run configuration: `BRAVE_API_KEY`; optional `BRAVE_BASE_URL`; pinned params
  `q`, `count`, `country`, `search_lang`.
- Protocol eligibility: search and search_fetch (document baseline only; no
  visual/location/dataset components).
- Comparability limitations: same query text and K as every engine; returns
  snippets only, so visual, localization and dataset components cannot score.
- Unknowns: live latency/cost per call; whether `extra_snippets=true` is worth
  the extra tokens (not pinned; left off for comparability).
- Public primary documentation:
  [Brave Search API quick start](https://api-dashboard.search.brave.com/documentation/services/web-search)
  (endpoint and header also documented in
  [brave-search-skills](https://github.com/brave/brave-search-skills/blob/main/skills/web-search/SKILL.md)).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
