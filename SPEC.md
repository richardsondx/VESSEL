# VESSEL specification — principles v0.1

Status: principles frozen before provider characterization and implementation.

VESSEL asks whether retrieval finds primary visual evidence, its precise source
location, and applicable underlying data. Document retrieval and evidence retrieval
are distinct outcomes. Evidence8 is one provider, never benchmark ground truth.

## Success

Gold is independently validated against primary publishers. A query can admit
multiple alternatives. Full Support@K requires one coherent returned bundle in the
first K results to satisfy every component required by one gold alternative.
Components from unrelated bundles cannot be combined. Original-visual tasks reject
newly generated visuals even when they use correct source data. Missing publisher
data is not a provider failure. Unavailable data is never required.

Exact file identity, rendition equivalence, and evidence equivalence are distinct.
Exact hashes, reviewed URL aliases and identifiers, verified figure/page/bounding
box locations are deterministic signals. Perceptual hashes only suggest matches.
Ambiguous equivalence requires recorded human adjudication. No model judge in v0.1.

## Protocols

- `search`: one search, up to ten ranked results, no shared fetching.
- `search_fetch`: the same search, first five eligible unique documents in rank
  order; shared HTML/PDF extraction. Maximum 20 MiB/document, 60 seconds/fetch,
  200 PDF pages, 100,000 text characters. Exhaustion/truncation are recorded.
- `evidence`: direct evidence bundles. Additional operations and costs are recorded.

Report protocols separately. Native content returned by a search is retained;
additional content options and automatic provider work must be characterized.
Extracted figures retain their parent search rank; they do not inflate top-K slots.

## Versioning and publication

Provider characterization determines invocation, never success. A substantive task
or scoring revision requires a new benchmark version, applies to all providers,
and cannot retroactively improve a provider's published score.

Human author and independent second reviewer approval, resolved disagreements,
freeze attestations, and complete auditable runs are publication prerequisites.
Fixtures and unreviewed candidates are never empirical benchmark results.
