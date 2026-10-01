# Serper characterization

Date: 2026-09-30. Status: public examples characterized; live adapter not yet tested.

- Interface: `POST https://google.serper.dev/search`, `X-API-KEY` header.
- Claim/result types: Google search results normalized into organic links/snippets;
  non-organic answer panels are not treated as additional ranked evidence slots.
- Fetch: shared VESSEL extraction; no undocumented provider fetch dependency.
- Ranking: preserve organic array order and record provider positions separately.
- Limits/quotas: account-specific; no assumed universal quota or price.
- Configuration: `q`, `num: 10`, `gl: us`, `hl: en`.
- Version: unversioned interface; archive run date/settings.
- Eligibility: search and search_fetch; Google/Serper is one named configuration.
- Comparability: location/language and search volatility affect reproducibility.
- Source: [Serper public product/examples](https://serper.dev/).
