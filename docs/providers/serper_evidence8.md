# serper_evidence8 hybrid characterization

Date: 2026-10-14. Status: composition characterized from the existing
`keenable_evidence8` pattern and the pinned `serper` / `evidence8` interfaces;
no live run performed. Full protocol validation remains pending.

- Date/version tested: 2026-10-14.
- Interface tested: Serper `POST /search` (Google SERP, see
  [serper.md](serper.md)) produces up to k ranked documents; then, for up to 5
  unique canonicalized document URLs, Evidence8 local `POST /v1/search` (see
  [evidence8.md](evidence8.md)) runs a document-conditioned query of the form
  `"<query>\nSource document: <url>"`. Exactly the `KeenableEvidence8` flow
  with the Serper adapter substituted.
- Documented claims: none of its own; it tests whether Google SERP results
  plus Evidence8 visual enrichment close the visual-evidence gap.
- Observed behavior: none yet; no live run performed.
- Result types: Serper documents with Evidence8 bundles attached only when the
  bundle's canonical source URL matches the searched document (same-document
  attachment rule as `keenable_evidence8`).
- Fetch/content capabilities: Evidence8 side is lexical visual retrieval; no
  shared document fetching inside the hybrid.
- Observable ranking: document order comes from Serper; no re-ranking.
- Limits/quotas: 5-document cap per query; one Serper call plus up to 5
  Evidence8 calls per query, each under its own cost ceiling.
- Run configuration: `serper` and `evidence8` provider entries must both exist
  in the config with ceilings set; `SERPER_API_KEY` and Evidence8 base URL.
- Protocol eligibility: evidence protocol only, reported separately from
  single-engine rankings. Never mixed into Tier 1/Tier 2 rankings: a hybrid
  win proves composition value, not single-engine superiority.
- Comparability limitations: the enrichment query leaks the document URL into
  Evidence8's lexical retrieval; cost accounting covers both sides.
- Unknowns: live latency/cost per query; how often same-document attachment
  succeeds.
- Public primary documentation: [serper.md](serper.md),
  [evidence8.md](evidence8.md).

Credentials, private endpoint overrides and authenticated artifacts are excluded.
