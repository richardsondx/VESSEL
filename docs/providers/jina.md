# Jina characterization

Date: 2026-10-14. Status: documentation characterized from Jina AI's Search
API docs (docs.jina.ai) and integration references on 2026-10-14; no
authenticated live call performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14; endpoint `POST https://s.jina.ai/`.
- Interface tested: `POST https://s.jina.ai/` with JSON body
  `{"q": "<query>", "num": <k>}`, headers `Authorization: Bearer <key>`,
  `Content-Type: application/json`, `Accept: application/json`.
  (A `GET https://s.jina.ai/?q=<query>` form exists but returns markdown text;
  the POST JSON form is pinned so the response shape is machine-readable.)
- Documented claims: web search returning structured results with clean
  content; keyless search is rejected (401).
- Observed behavior: none yet; no live call performed.
- Result types: `{"code": 200, "status": 20000, "data": [{title, description,
  url, content, usage: {...}}]}`. `description` maps to the snippet. A `code`
  other than 200 means a provider-side failure and raises; an absent `code`
  is tolerated (some envelopes omit it).
- Fetch/content capabilities: none in the search call; `r.jina.ai` reader is
  separate and not used.
- Observable ranking: preserve returned array order; no inferred confidence.
- Limits/quotas: `num` pinned to k. Jina is token-priced and slow (NEEDLE p50
  18s); the adapter timeout is the shared 30s, so timeouts record as errors.
- Run configuration: `JINA_API_KEY`; optional `JINA_BASE_URL`.
- Protocol eligibility: search and search_fetch (document baseline only).
- Comparability limitations: same query text and K as every engine; cannot
  score visual/localization/dataset components.
- Unknowns: live latency/cost per call; whether the endpoint honors `num`
  above its default of 5.
- Public primary documentation:
  [Jina Search API](https://jina.ai/reader) (search docs under
  [docs.jina.ai](https://docs.jina.ai)).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
