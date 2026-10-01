# Evidence8 study for VESSEL

> **Scope:** This document records observations about Evidence8 relevant to the
> design of VESSEL. It is based on publicly observable product behavior and
> documented interfaces. Evidence8 is one provider evaluated by VESSEL and is not
> used as benchmark ground truth.

Study date: September 30, 2026 (America/Toronto). Principles were committed before
this characterization. No privileged access was used. This is a public research
report, not internal investigative notes. Corpus membership remains unattested.

## A. Executive summary

Evidence8 exposes candidate visual retrieval with source context, not independently
verified claim support. Public documentation describes deterministic lexical search
and local HTTP/stdio interfaces, with no generally available hosted agent endpoint.
The website is not an API base URL. See [agent guide](https://evidence8.com/agents.md)
and [HTTP reference](https://evidence8.com/docs/api-reference.md).

The useful abstraction is a visual plus its source trail. The corpus also includes
visuals generated from source facts; these cannot automatically satisfy a request
for an original publisher visual. Availability is workspace-specific.

## B. Evidence object model

Observed library/viewer fields: title, descriptive text, visual type, source name,
source document, a displayed publication date, rights label, source link and optional
data link. The [metadata guide](https://evidence8.com/docs/metadata.md) documents
identity, agent context, provenance, delivery, quality and retrieval groups.

Conceptual relations, inferred rather than a claim about internal storage:

`candidate → visual rendition → source document/series → publisher`

`generated rendition → observations/dataset/API → data originator`

Documents/PDFs contain figures and tables; dataset series contain observations.
A source host is not necessarily the original data producer. In the FRED examples,
FRED hosts charts while BLS or the Federal Reserve Board originates observations.
Evidence8-specific asset IDs, lexical hints and quality labels are adapter metadata,
not VESSEL identity or correctness. Structural completeness is not semantic review.

## C. Corpus taxonomy

All 36 registry/detail pages were inspected. The dated
[corpus inventory](research/public/corpus-inventory.json) records each publisher,
acquisition model, status, counts, provenance and retention claims. Unknown means
not established publicly; claimed retention is not independently verified storage.

Distinct models:

- Native publisher exports: FRED, IEA, OWID and publisher chart images.
- Captured publisher renderings: Ember, Zillow Tableau and weekly maps.
- Extracted PDF figures/tables/pages: investor relations and research reports.
- Derived visuals: SEC facts, World Bank, EIA, IMF, BLS, Treasury and ECB API data.
- Data-only ledgers: GHSL and Eurostat have no exposed visual examples.
- Proposed on-demand web acquisition: labeled coming later.

Registry and detail counts differ for IEA, Ember, Epoch and source-catalog entries.
Preserve both; neither establishes actual searchable coverage or a frozen index.
Many detail pages repeat generic coverage text and example queries. Those templates
are not evidence that every record has precise page provenance.

## D. Provenance model

Inspected native FRED records link the series and CSV. World Bank records link
indicator pages and API payloads and explicitly describe local rendering. PDF
examples link the report, but the inspected viewer does not expose page/figure
coordinates. Source-catalog descriptions mention native assets, raw data and rights
with varying specificity. Full original document retention is not publicly proven.

A source URL must be classified as document, visual, dataset or landing page. An
“Open original chart” link can lead to a containing PDF or series page rather than
an image. VESSEL keeps publisher, data originator, renderer and host distinct.

## E. Evidence completeness

Test separately: document identity, visual identity, authoritative origin,
localization, version/vintage and applicable source data. Measure rights/context and
methodology availability without treating access as redistribution permission.
Gold determines required components. A dataset is not mandatory where the publisher
does not supply it. Publication date cannot be substituted with acquisition time or
an API-wide update date.

## F. Retrieval task taxonomy

Known-item, descriptive, claim-to-evidence, fuzzy recall, comparative, source-unknown,
PDF-hidden, original-source, temporal and data-oriented tasks are relevant. The
public lexical path supports evaluating caption/context overlap; it does not
establish visual similarity or semantic claim-verification capability.

## G. Deterministic identifiers

Use reviewed source/asset URLs, series/dataset codes, document identifiers, exact
file hashes, page indices, printed labels and figure locators. VESSEL must add
versioned gold alternatives, independently reviewed rendition families, source
snapshot hashes and adjudication records. Evidence8 asset IDs alone cannot score a
match. Perceptual hashes require review before equivalence acceptance.

## H. Strengths

Observed native charts, source PDFs and generated API charts appear in one library,
with links to source/data where available. Explicit derivation descriptions and
rights labels are useful to preserve. These are representational capabilities;
no comparative accuracy or speed conclusion follows from this study.

## I. Limitations and falsification cases

Coverage labels/counts are inconsistent across surfaces. Local-only interfaces and
lexical search limit what can be inferred about hosted integration and semantic
retrieval. Two data-only collections expose no visual to inspect. PDF locations,
image hashes, version lineage, transformations and full payload completeness were
not verified in sampled viewers. Test maps, scientific multi-panel figures,
reproductions, chart revisions, unsupported publishers and caption-poor evidence.
A displayed date or rights label requires primary-source validation.

## J. Leakage and contamination

Known registry publishers cannot be called unseen solely because a document is
absent from the viewer. Unlisted publishers also require freeze attestation for
holdout claims. This study records public coverage claims, not a private index
inventory. Preserve `unknown` when unsupported/unindexed status cannot be attested.

## K. Proposed VESSEL abstractions

Keep document, visual asset, dataset, provenance and derivation independently
representable, within a coherent bundle. Distinguish original visuals, PDF crops,
captures and generated renditions. Missing fields remain unknown. Gold supplies
accepted identities and requirements independently. Provider characterization maps
responses into these contracts without altering success.

## L. Evidence8 adapter contract

Use configurable local/workspace HTTP `POST /v1/search` with `query`, `corpus` and
`candidateLimit`. Preserve result order and actual count. Normalize the documented
`results` array, or a lone `selected` candidate when that is all the interface returns.
Map available asset metadata; never fabricate page numbers, authority, image hashes
or data links. Record no-match, usage, timing and request count. Endpoint credentials
stay outside public profiles. Live integration is unverified until configured.

## M. Open questions and sample audit

Two native examples inspected: FRED FEDFUNDS and UNRATE. Two API-derived examples:
World Bank USA GDP and GDP per capita. Two PDF examples: Meta Q3 2025 advertising
revenue chart and AMD Q2 2026 summary P&L. GHSL and Eurostat are the two data-only
examples; there is no individual visual to inspect. More per-corpus item audits are
needed before making completeness claims.

Primary checks:

- [FEDFUNDS](https://fred.stlouisfed.org/series/FEDFUNDS) identifies the Federal Reserve
  Board as originator, monthly percentages and September 2026 updates. The viewer's
  displayed August 23 date cannot be taken as the current series update.
- [UNRATE](https://fred.stlouisfed.org/series/UNRATE) identifies BLS, monthly seasonally
  adjusted percentages and September 2026 updates. Its data-source role differs
  from FRED's chart-host role.
- [World Bank GDP API](https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page=2)
  confirms the indicator/country and `lastupdated` of July 13, 2026. That is an API
  update field, not independently established chart publication time.
- [Meta presentation](https://s21.q4cdn.com/399680738/files/doc_financials/2025/q3/Earnings-Presentation-Q3-2025-Final.pdf)
  is an 18-page Q3 2025 report containing the advertising geography visual. The
  viewer's displayed August 2026 date does not establish report publication.
- AMD's linked PDF was observed; its content/date has not been independently audited.

Unresolved: exact authenticated response variants, tested workspace version, index
freeze, timestamp semantics, per-asset rights validation and provenance completeness.
These do not change the frozen task/scoring principles.
