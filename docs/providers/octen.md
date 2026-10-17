# Octen characterization

Date: 2026-10-14. Status: documentation characterized from Octen's official
skill references (octen-team/octen-cli, octen-team/web-search-skills) on
2026-10-14; no authenticated live call performed. Full protocol validation
remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /search` on `api.octen.ai`.
- Interface tested: `POST https://api.octen.ai/search` with JSON body
  `{"query": "<query>", "count": <n>, "highlight": {"enable": true,
  "max_tokens": 300}}`, header `X-Api-Key: <key>`.
- Documented claims: LLM-native real-time web search; query-relevant
  highlights per result.
- Observed behavior: none yet; no live call performed.
- Result types: `{"code": 0, "msg": ..., "request_id": ..., "data": {"query",
  "results": [{title, url, highlight, full_content, authors, time_published,
  time_last_crawled}]}, "meta": {...}}`. `code: 0` is success; any other
  code raises. `highlight` maps to the snippet; `time_published` to the
  published date.
- Fetch/content capabilities: `full_content` exists; pinned off (search
  protocol pins one request, no provider fetch).
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `count` 1-20, pinned to `min(k, 20)`. Highlight pinned on
  with a 300-token cap per result.
- Run configuration: `OCTEN_API_KEY`; optional `OCTEN_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call.
- Public primary documentation:
  [octen-search SKILL.md](https://github.com/octen-team/octen-cli/blob/HEAD/skills/octen-search/SKILL.md)
  (official Octen Team reference for endpoint, headers, request and response).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
