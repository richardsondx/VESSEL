# Exa characterization

Date: 2026-09-30. Status: documentation characterized; live adapter not yet tested.

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
