# Perplexity Fast characterization

Date: 2026-10-14. Status: documentation characterized 2026-10-14; no
authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST /search` on
  `api.perplexity.ai` (same endpoint as `perplexity`).
- Interface tested: `POST https://api.perplexity.ai/search` with JSON body
  `{"query": "<query>", "max_results": <k>, "max_tokens_per_page": 512}`,
  header `Authorization: Bearer <key>`.
- Documented claims: this is a VESSEL-pinned cost/latency tradeoff variant, not
  a separate Perplexity product. Perplexity documents no "fast" search type;
  the reduction comes from the documented `max_tokens_per_page` parameter
  (default 4096, pinned here to 512), which shrinks extracted page content per
  result and therefore billed tokens and latency.
- Observed behavior: none yet; no live call performed.
- Result types: same as `perplexity`: `results[]` entries `{title, url,
  snippet, date, last_updated}`.
- Fetch/content capabilities: none in the search call.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `max_results` 1-20, pinned to k; `max_tokens_per_page` pinned
  to 512.
- Run configuration: `PERPLEXITY_API_KEY`; optional `PERPLEXITY_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; differs
  from `perplexity` only in the token budget. Cannot score
  visual/localization/dataset components.
- Unknowns: live latency/cost per call; whether the token reduction changes
  snippet completeness.
- Public primary documentation:
  [Perplexity Search API quickstart](https://docs.perplexity.ai/docs/search/quickstart).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
