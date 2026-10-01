# Exa characterization

Date: 2026-09-30. Status: documentation characterized; one authenticated search smoke check passed.

- Interface: `POST https://api.exa.ai/search`, `x-api-key` header.
- Claim/result types: ranked document records with URL, title and optional content,
  publication date/author. Content retrieval can be configured separately.
- Fetch: contents API exists; VESSEL uses shared fetch for search_fetch.
- Ranking: preserve returned order; a provider score is not VESSEL correctness.
- Limits: documented numResults 1–100; search-type limits can differ.
- Configuration: `type: auto`, `numResults: 10`, no `contents` enrichment by default.
- Version: unversioned interface; capture config/test date and response request ID.
- Eligibility: search and search_fetch. No evidence-object capability assumed.
- Comparability: synthesized deep modes are not mixed with default search runs.
- Source: [official search reference](https://exa.ai/docs/reference/search).

## Observed live smoke check

One authenticated search requested three results and returned three normalized
results without adapter errors. No provider fetch, shared extraction, retry or
benchmark scoring was performed. This checks authentication and the sampled response
shape; full protocol, failure and benchmark validation remain pending.
Authenticated payloads and credentials are kept in ignored local artifacts.

Tested settings: `type: auto`, `numResults: 3`, no contents. The response reported
`costDollars.total: 0.007`; this is provider-reported usage, not an audited invoice.
