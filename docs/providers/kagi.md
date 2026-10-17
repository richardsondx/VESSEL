# Kagi characterization

Date: 2026-10-14. Status: documentation characterized from Kagi's published
Search API v0 reference (help.kagi.com, mirrored in kagisearch/kagi-docs) on
2026-10-14; no authenticated live call performed. Full protocol validation
remains pending.

- Date/version tested: 2026-10-14; Kagi Search API v0 (legacy but officially
  documented and stable; a v1 POST shape exists in third-party integrations but
  is not pinned here because it could not be verified against Kagi's own docs).
- Interface tested: `GET https://kagi.com/api/v0/search?q=<query>&limit=<k>`,
  header `Authorization: Bot <token>` (note: `Bot`, not `Bearer`).
- Documented claims: curated high-signal index; billed per query.
- Observed behavior: none yet; no live call performed.
- Result types: `data[]` entries typed by `t`: `t=0` web results `{rank, url,
  title, snippet, published, thumbnail}`; `t=1` related searches (`list` of
  strings). Adapter keeps only `t=0` rows.
- Fetch/content capabilities: separate Enrich endpoints exist; VESSEL does not
  call them (search protocol pins one request).
- Observable ranking: preserve returned array order (also carries `rank`);
  no inferred confidence.
- Limits/quotas: `limit` pinned to k. Search API is invite-only per Kagi docs;
  missing credentials skip.
- Run configuration: `KAGI_API_KEY`; optional `KAGI_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call; whether the v1 POST contract should
  replace v0 before the live run (re-verify against Kagi's docs at run time).
- Public primary documentation:
  [Kagi Search API (legacy v0)](https://github.com/kagisearch/kagi-docs/blob/HEAD/docs/kagi/api/search-legacy.md),
  [Kagi API help](https://help.kagi.com/kagi/api/search.html).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
