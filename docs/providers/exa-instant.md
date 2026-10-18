# exa-instant

Exa search with `type=instant` (pinned at adapter level; see `Exa.payload`).
Same key, base URL, and request shape as `exa`; differs only in the pinned
search type. Intended as the latency/cost baseline for the Exa family:
instant answers trade recall for speed and price.

- Endpoint: `POST https://api.exa.ai/search`, header `x-api-key: <EXA_API_KEY>`
- Pinned: `type=instant`, `numResults=k`
- Shares the `EXA_API_KEY` credential with the `exa` configuration.
