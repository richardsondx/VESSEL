# Evidence8 characterization

Date: 2026-10-01. Status: public interface characterized; ten-query local search
diagnostic passed. Full protocol validation remains pending.

- Interface: local/workspace HTTP `POST /v1/search`; no general hosted endpoint.
- Claim: deterministic lexical retrieval of candidate visuals with provenance.
- Result types: ranked assets and selected candidate; original and generated visuals.
- Fetch: public HTTP docs do not establish a document-enrichment operation.
- Ranking: preserve array order; scores are not semantic correctness.
- Limits: `candidateLimit` documented, workspace maximum not established.
- Configuration: base URL via environment; corpus `all`; ten candidates by default.
- Version: metadata envelope `evidence.asset-metadata.v1`; tested local runtime
  reports `local-v0.1`. The run also records the index file hash and registry hash;
  the version string alone is not an immutable index identity.
- Eligibility: evidence; search where document references exist; shared search_fetch.
- Comparability: lexical indexed retrieval, corpus availability and generated visual
  semantics must be reported. No claim of general unseen-publisher support.
- Sources: [HTTP reference](https://evidence8.com/docs/api-reference.md),
  [metadata](https://evidence8.com/docs/metadata.md), [full study](../EVIDENCE8_STUDY.md).

Credentials, private endpoint overrides and authenticated artifacts are excluded.

Observed local responses use relative preview paths. The adapter maps these to the
documented `/v1/assets/{id}/content` API route, retains unknown page conventions,
and marks `derived-from-source-data` visuals as generated. Local `dataPath` values
are not treated as publicly fetchable datasets. Retrieval diagnostics establish
response compatibility, not correctness, original-asset equivalence or holdout status.
