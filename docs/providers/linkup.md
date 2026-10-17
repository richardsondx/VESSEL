# Linkup characterization

Date: 2026-10-14. Status: documentation characterized from Linkup's official
Python SDK (linkupplatform/linkup-python-sdk) and API docs on 2026-10-14; no
authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /v1/search` on
  `api.linkup.so`.
- Interface tested: `POST https://api.linkup.so/v1/search` with JSON body
  `{"q": "<query>", "depth": "standard", "outputType": "searchResults"}`,
  header `Authorization: Bearer <key>`.
- Documented claims: agentic web search; `depth` trades speed against coverage
  (`flash` < `fast` < `standard` < `deep`).
- Observed behavior: none yet; no live call performed.
- Result types: `outputType=searchResults` returns `results[]` entries
  `{name, url, snippet, favicon}`. Adapter maps `name` to the title.
- Fetch/content capabilities: separate `/v1/fetch` exists; VESSEL does not
  call it (search protocol pins one request).
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `depth` pinned to `standard` (single-pass agentic search,
  roughly 1-3s); `deep` (30-120s) is a deliberately separate cost/latency
  point and is not run unless configured.
- Run configuration: `LINKUP_API_KEY`; optional `LINKUP_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call; whether the raw response also nests
  results under a different key in some versions (re-verify at run time).
- Public primary documentation:
  [linkup-python-sdk README](https://github.com/linkupplatform/linkup-python-sdk),
  [Linkup search docs](https://docs.linkup.so/pages/documentation/api-reference/endpoint/post-search).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
