# Implementation status

Status: **software verified; research and publication gates pending**.

The repository contains a working offline harness, strict schemas, provider adapters,
shared extraction, deterministic scoring, budgeted/resumable execution, diagnostic
reports, human review/audit commands, offline CI and a React results explorer.

## Release gates

| Gate | Current evidence | Remaining work |
|---|---|---|
| Principles | Provider-independent principles committed before characterization; firewall in methodology | Version future substantive revisions equally for all providers |
| Characterization | Public A–M Evidence8 study, all 36 registry/detail pages inspected, source hashes, four provider profiles | Configured workspace response audit; inaccessible examples and unknown fields remain explicitly unverified |
| Pilot | Twenty **synthetic software fixtures**, deterministic replay | Twenty real primary-evidence queries with author and independent human review |
| Core-100 | One hundred **unreviewed discovery candidates**, schema and composition checks | Freeze index before authoring; verify gold and at least 40 holdout queries; independent review |
| Validation | 81 backend tests; 10 explorer tests; local replay, resume, lint and production build pass | Full live protocol validation; capped comparisons; human failure audit |
| Publication | Read-only artifact explorer and public-export rejection gates | Eligible audited Core-100 artifacts; deploy to vessel.evidence8.com after validation |

No live benchmark evaluation has been run. A separate user-authorized connectivity
check made one search each against Keenable and Exa; both returned three normalized
results. Its $1 cap reserved $0.50 conservatively; Exa reported $0.007 and Keenable's
dollar cost was unknown. This was not a comparative benchmark or scoring run.
No human review or index attestation was invented. Missing configuration produces
explicit skips; the local Evidence8 API was not reachable and Serper was unconfigured.

## Verification

See [QA evidence](../qa-learnings/IMPLEMENTATION_QA.md). Run source code and dependency
lock are archived as content-addressed objects; receipt, dataset, configuration and
code integrity are checked on replay. Changing dependencies prevents resume.

The current preview and checked-in demo show synthetic outcomes, never provider
performance. The discovery queue is not gold and cannot be evaluated by the runner.

## Operator handoff

1. Configure the Evidence8 workspace base URL/key privately and comparison keys as
   available. Confirm per-call ceilings and an explicit maximum spending cap.
2. Obtain an index/version freeze attestation and identify the author and independent
   human reviewer. Follow the annotation guide; author evaluation queries after freeze.
3. Validate the real pilot, expand to Core-100, then run separate protocol configurations.
4. Audit the complete comparisons and export with `--public-release` before deployment.

Do not interpret the presence of an adapter, corpus catalog or generated report as
live verification, non-ingestion proof or completed research review.
