# Contamination policy

Freeze task/scoring principles first. Obtain a provider version/index attestation
before authoring evaluation queries. Record benchmark, configuration, source and
gold timestamps, code hash, provider configuration and registry snapshot hashes.

- `indexed`: attested documents already indexed at freeze.
- `known_unindexed`: attested unindexed documents in a supported source family.
- `external_holdout`: attested unsupported publisher family at freeze.
- `unknown`: not reliably established; excluded from headline holdout claims.

Public registry absence is insufficient evidence of non-ingestion. VESSEL does not
claim holdout status without documentary attestation. Post-freeze ingestion is
separate from frozen-index retrieval; live/on-demand indexing must be characterized.
Freeze timestamps precede query creation. Query authors do not see provider results
before gold is frozen. Development families cannot cross into evaluation splits.

Core-100 targets ten queries in each of ten domains, at least forty verified
external-holdout queries and 55 charts/15 tables/10 maps/10 multi-panel figures/
5 diagrams/5 other visuals. VESSEL-Live, later, releases gold after evaluation.
