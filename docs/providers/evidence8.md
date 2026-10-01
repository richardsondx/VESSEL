# Evidence8 characterization

Date: 2026-09-30. Status: public interface characterized; live adapter not yet tested.

- Interface: local/workspace HTTP `POST /v1/search`; no general hosted endpoint.
- Claim: deterministic lexical retrieval of candidate visuals with provenance.
- Result types: ranked assets and selected candidate; original and generated visuals.
- Fetch: public HTTP docs do not establish a document-enrichment operation.
- Ranking: preserve array order; scores are not semantic correctness.
- Limits: `candidateLimit` documented, workspace maximum not established.
- Configuration: base URL via environment; corpus `all`; ten candidates by default.
- Version: metadata envelope `evidence.asset-metadata.v1`; runtime version unknown.
- Eligibility: evidence; search where document references exist; shared search_fetch.
- Comparability: lexical indexed retrieval, corpus availability and generated visual
  semantics must be reported. No claim of general unseen-publisher support.
- Sources: [HTTP reference](https://evidence8.com/docs/api-reference.md),
  [metadata](https://evidence8.com/docs/metadata.md), [full study](../EVIDENCE8_STUDY.md).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
