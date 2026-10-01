# Methodology

## Provider characterization

Before a provider is evaluated, VESSEL documents the tested interface, observable
capabilities, configuration, limits, and protocol eligibility. These profiles exist
to ensure reproducibility and fair invocation. Provider-specific characteristics
do not modify benchmark queries, gold records, success criteria, or scoring rules.

**Provider characterization determines how a system is invoked, never what
constitutes success.**

Order: freeze task/scoring principles → characterize providers → implement adapters
→ curate and freeze gold → evaluate → independently audit → publish.

## Gold and review

Primary publisher records validate gold, not a provider's own metadata. Original
publisher visuals and generated renditions are labeled separately. Dates distinguish
publication, retrieval, observation period and vintage. Location can be PDF page
index, printed label, figure identifier, bounding box or stable web asset locator.

Every release query requires an author and distinct independent reviewer; each
approval binds to the record's content digest. Revisions invalidate prior approval.
Equally valid answers are separate alternatives. Related queries share a family
identifier for splitting and uncertainty estimates. No perceptual-hash threshold
alone can award a match. Record all human equivalence decisions.

## Reporting

Report document, visual, primary-source, localization, dataset and full-support
recall at K=1,5,10 and reciprocal rank. Missing data requirements have an explicit
denominator. Missing credentials are skips; provider failures remain visible and
cannot silently change the comparison population. Only complete runs on identical
dataset digests/protocol configurations can be compared. Use paired differences
and 95% bootstrap intervals resampling evidence families, with a fixed seed.

Search results occupy their original rank even when repeated. Search+Fetch crops
remain within their document's rank. No reranking using gold. Scoring can check
whether a document contains gold without exposing gold to an adapter/extractor.

## Public research hygiene

Publish observable behavior, documented interfaces, uncertainty and evidence for
design choices. Do not publish private endpoints, privileged-access observations,
secrets, infrastructure/security details, unpublished roadmaps or business strategy.
Authenticated artifacts stay in ignored `.private/` or ignored `runs/`. Public
fixtures are explicitly synthetic. Sanitization is required before redistribution.
