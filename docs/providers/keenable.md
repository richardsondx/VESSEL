# Keenable characterization

Date: 2026-09-30. Status: documentation characterized; live adapter not yet tested.

- Interface: `POST https://api.keenable.ai/v1/search`, `X-API-Key` header.
- Claim/result types: ranked pages with URL, title, description, snippet and optional
  publication/acquisition dates. Snippets may contain extracted page text.
- Fetch: separate `GET /v1/fetch` returns markdown; VESSEL instead uses shared fetch.
- Ranking: preserve returned array order, no inferred confidence or authority.
- Limits: documented `max_results` 1–50; snippet length 180–10,000.
- Configuration: `mode: pro`, `max_results: 10`; no source restrictions by default.
- Version: unversioned HTTP shape under `/v1`; run records capture test date.
- Eligibility: search and search_fetch; hybrid is a separately configured system.
- Comparability: native snippets are retained; no extra provider fetch in Search.
- Source: [official search reference](https://docs.keenable.ai/api-reference/search).

Keyless endpoints exist but are opt-in; missing credentials skip by default.
