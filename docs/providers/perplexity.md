# Perplexity characterization

Date: 2026-10-14. Status: documentation characterized from Perplexity's public
Search API docs (docs.perplexity.ai/docs/search/quickstart) and integration
references on 2026-10-14; no authenticated live call performed. Full protocol
validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /search` on
  `api.perplexity.ai`.
- Interface tested: `POST https://api.perplexity.ai/search` with JSON body
  `{"query": "<query>", "max_results": <k>}`, header
  `Authorization: Bearer <key>`.
- Documented claims: ranked web results without LLM synthesis; no score field,
  list order is the ranking.
- Observed behavior: none yet; no live call performed.
- Result types: `results[]` entries `{title, url, snippet, date, last_updated}`.
- Fetch/content capabilities: none in the search call; VESSEL uses shared fetch
  under the search_fetch protocol.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `max_results` 1-20, pinned to k. `max_tokens_per_page` default
  4096 (left at default for the standard engine).
- Run configuration: `PERPLEXITY_API_KEY`; optional `PERPLEXITY_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call.
- Public primary documentation:
  [Perplexity Search API quickstart](https://docs.perplexity.ai/docs/search/quickstart).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
