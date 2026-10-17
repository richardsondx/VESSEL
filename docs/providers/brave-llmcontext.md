# Brave LLM Context characterization

Date: 2026-10-14. Status: documentation characterized from Brave's public API
references (brave-search-skills llm-context SKILL.md, api-dashboard); no
authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `/res/v1/llm/context`.
- Interface tested: `POST https://api.search.brave.com/res/v1/llm/context` with
  JSON body `{"q": "<query>", "count": <n>, "maximum_number_of_urls": <n>}`,
  header `X-Subscription-Token: <key>`. (GET with query params is also
  documented; POST is pinned for parity with the other adapters.)
- Documented claims: pre-extracted, relevance-ranked page content (text chunks,
  tables, code) optimized for LLM grounding; one search per request.
- Observed behavior: none yet; no live call performed.
- Result types: `grounding.generic[]` entries `{url, title, snippets[]}`.
  Adapter joins the snippets into the result snippet.
- Fetch/content capabilities: the endpoint itself extracts page content; VESSEL
  still treats it as a search provider and applies no extra provider fetch.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `count`/`maximum_number_of_urls` 1-50; pinned at `min(k, 50)`.
  Token budget parameters (`maximum_number_of_tokens`, etc.) are not pinned.
- Run configuration: `BRAVE_API_KEY` (same key as Brave web search); optional
  `BRAVE_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; snippet-only
  baseline, cannot score visual/localization/dataset components.
- Unknowns: live latency/cost per call; snippet join order vs relevance order.
- Public primary documentation:
  [LLM Context docs](https://api-dashboard.search.brave.com/documentation/services/llm-context),
  [skill reference](https://github.com/brave/brave-search-skills/blob/main/skills/llm-context/SKILL.md).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
