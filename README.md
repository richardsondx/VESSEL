# VESSEL

**Visual Evidence Search & Source Evaluation Live**

An open benchmark and evaluation harness for retrieving **the right visual,
its primary source, its precise location, and applicable underlying data**.

[![Offline verification](https://github.com/richardsondx/VESSEL/actions/workflows/ci.yml/badge.svg)](https://github.com/richardsondx/VESSEL/actions/workflows/ci.yml)
[![Code: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue)](LICENSE)
[![Annotations: CC BY 4.0](https://img.shields.io/badge/annotations-CC_BY_4.0-blue)](data/LICENSE)

[Quickstart](#quickstart) · [What we measure](#what-we-measure) ·
[Methodology](METHODOLOGY.md) · [Data](#data-and-release-status) ·
[Contribute](CONTRIBUTING.md) · [Cite](#citation-and-rights)

> **Development release:** the harness and explorer work with offline fixtures.
> Core-100 is awaiting independent human review and index attestations.
> No validated provider rankings have been published. Demo values are synthetic.

## Start here

| Your goal | Where to start | What you can inspect |
|---|---|---|
| **Scientist:** assess evidence and its source trail | [Gold annotation guide](docs/ANNOTATION_GUIDE.md) | Primary references, visual identity, figure/page locations, available data, and review decisions |
| **Researcher:** reproduce or critique an evaluation | [Methodology](METHODOLOGY.md) and [contamination policy](CONTAMINATION.md) | Protocol boundaries, scoring rules, versions, uncertainty, and holdout requirements |
| **Developer:** run the harness or add a provider | [Quickstart](#quickstart) and [contributor guide](CONTRIBUTING.md) | Normalized contracts, replay artifacts, adapters, and failure diagnostics |

## Quickstart

Run a complete software demonstration without provider credentials or paid API calls.
Installation downloads dependencies; evaluation uses local fixtures.
Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/richardsondx/VESSEL.git
cd VESSEL
uv sync --frozen --python 3.12
uv run vessel validate data/synthetic-pilot.jsonl
uv run vessel run data/synthetic-pilot.jsonl configs/replay.yaml runs/quickstart \
  --fixture tests/fixtures/replay.json
uv run vessel replay runs/quickstart
```

**Expected:** 20 synthetic queries × 4 system fixtures = 80 result cells,
zero provider requests, and $0 reserved spend. The output is labeled
`SYNTHETIC SOFTWARE FIXTURE — NOT PROVIDER PERFORMANCE`.
Inspect `runs/quickstart/report.json`; re-scoring makes no provider requests.

To explore the results, install Node.js 22.12+ and run:

```sh
uv run vessel export runs/quickstart explorer/public/report.json
npm --prefix explorer ci
npm --prefix explorer run dev
```

Open the local URL printed by Vite. Filter by provider, domain, visual type,
membership, or outcome; inspect each query's accepted gold, returned bundles,
provenance, and missing requirements. Import or download JSON reports locally.
The frontend reads exported artifacts and contains no provider credentials.

Use a fresh run directory when changing code, dependencies, data, or configuration.
For an identical interrupted run, add `--resume`. See the
[running guide](docs/RUNNING.md) for live configuration and release commands.

## API configuration

Offline replay and CI need **no API keys**. For live testing, copy
[`.env.example`](.env.example) to an ignored `.env` in the repository root, or edit
an existing `.env`. Exported environment variables take precedence.

| Variable | Used by | Requirement |
|---|---|---|
| `EVIDENCE8_BASE_URL` | Evidence8 | Actual workspace HTTP API base; documented local default is `http://127.0.0.1:8787`. The public website is not an API base. |
| `EVIDENCE8_API_KEY` | Evidence8 | Optional for the documented local API; set only if your workspace requires bearer authentication. |
| `KEENABLE_API_KEY` | Keenable | Required by default; keyless access is an explicit configuration option. |
| `EXA_API_KEY` | Exa | Required when evaluating Exa. |
| `SERPER_API_KEY` | Google results through Serper | Required when evaluating Serper. |

Check configuration without displaying keys or making provider requests:

```sh
uv run vessel doctor --config configs/live.yaml
```

A configured key does not enable spending: live runs also need explicit total
budgets and per-request cost ceilings. Missing keys or ceilings produce recorded
skips. VESSEL's deterministic scorer needs no LLM judge key. Keep keys in `.env`
or your environment; the explorer receives exported reports only.
See the [live running guide](docs/RUNNING.md#configure-live-providers).

## What we measure

A document hit can point to the right report while missing the requested figure,
returning a reproduction, or omitting its source data. VESSEL records those outcomes
separately.

**Full Support@K** means that one coherent bundle within the first K results
satisfies every required component of one independently accepted gold alternative.
The scorer cannot assemble support from unrelated bundles. Gold may accept multiple
valid answers; source data is required only when verified as available and applicable.

Illustrative example, **not a benchmark query or measured result**: retrieve an
original publisher chart, its report location, and the CSV the publisher supplies.

| Returned evidence | Document recall | Full Support |
|---|---|---|
| The correct report URL | Yes | No: the visual and required supporting components are missing |
| A new chart drawn from the same CSV | May be yes | No: an original publisher visual is required |
| The accepted chart, primary report, verified figure location, and CSV in one bundle | Yes | Yes |

The harness reports:

- Document, visual, primary-source, localization, and applicable-data recall.
- Full Support and MRR of the first fully supporting result at K=1, 5, and 10,
  where the configured result depth supports them.
- Latency, reserved/reported cost, failures, and paired differences with 95%
  intervals resampled by evidence family.
- Rights, methodology, and reproducibility recall with applicable denominators;
  these affect Full Support only when explicitly required by gold.

Matching uses accepted URLs, exact hashes, source identifiers, verified locations,
and recorded human adjudications. Perceptual hashes alone do not establish equivalence.
PDF page indices and printed page labels remain distinct. Read the
[scoring principles](SPEC.md) before interpreting a comparison.

## Evaluation protocols

| Protocol | Retrieval allowance | Reporting boundary |
|---|---|---|
| **Search** | One request, up to ten ranked results | Retains native returned content; no additional shared fetch |
| **Search + Fetch** | Search, then the first five eligible unique documents | Shared HTML/PDF extraction; figures retain their parent result rank |
| **Evidence Retrieval** | Direct evidence bundles | Additional operations and requests are recorded |

Shared fetch defaults: 20 MiB/document, 60 seconds, 200 PDF pages, and 100,000
extracted characters. Truncation and exhaustion are recorded. Extraction receives
no gold. Compare matching benchmark versions and protocols; incomplete runs cannot
become headline rankings.

> **Provider characterization determines how a system is invoked, never what
> constitutes success.**

Adapters exist for [Evidence8](docs/providers/evidence8.md),
[Keenable](docs/providers/keenable.md), [Exa](docs/providers/exa.md), and
[Serper](docs/providers/serper.md). Their public interface profiles distinguish
claims, observations, and unknowns. Single-search Keenable and Exa connectivity
checks pass; full protocol and benchmark validation remain pending.
Evidence8 is one evaluated provider and does not supply benchmark ground truth.
The Keenable + Evidence8 hybrid is a separately reported system with a documented
[retrieval strategy](docs/RUNNING.md#hybrid-evaluation).

## Data and release status

| Artifact | Available now | Scientific status |
|---|---|---|
| [Synthetic pilot](data/synthetic-pilot.jsonl) | 20 fixture queries with synthetic gold | Software checks only; no provider-performance claim |
| [Discovery queue](data/core-100-candidates.jsonl) | 100 candidate information needs | No reviewed gold or attested holdout membership |
| **Core-100** | Planned: 100 independently reviewed queries | Not released |
| [Explorer demo export](explorer/public/demo-report.json) | Downloadable JSON | Synthetic outcomes only |

Core-100 targets ten queries in each of ten domains: economics, finance, energy,
AI, climate, demographics, labor, housing, science, and policy. Its planned visual
mix is 55 charts, 15 tables, 10 maps, 10 multi-panel figures, five diagrams, and five
other visuals, with at least 40 attested external-holdout queries.

Every evaluation query needs author approval and a distinct independent human
reviewer. Index/version freeze precedes evaluation query authoring. Unknown corpus
membership cannot support a headline holdout claim. Related queries stay grouped by
evidence family. See [release gates and outstanding work](docs/IMPLEMENTATION_STATUS.md).

Core-500, VESSEL-Live, Trace, and Research follow a validated Core-100 release.
Publication at `vessel.evidence8.com` follows validation; the public explorer is not
currently deployed.

## Documentation and contributions

| Need | Reference |
|---|---|
| Task definitions and success criteria | [Specification](SPEC.md) |
| Fair invocation, scoring, and uncertainty | [Methodology](METHODOLOGY.md) |
| Leakage, membership, and holdout rules | [Contamination policy](CONTAMINATION.md) |
| Configure, resume, compare, audit, and export runs | [Running guide](docs/RUNNING.md) |
| Author or independently review gold | [Annotation guide](docs/ANNOTATION_GUIDE.md) |
| Understand normalized record shapes | [JSON schemas](schemas/) and [models](src/vessel/models.py) |
| Understand provider capabilities | [Provider profiles](docs/providers/) and [Evidence8 study](docs/EVIDENCE8_STUDY.md) |
| Add an adapter, report a failure, or improve documentation | [Contributing](CONTRIBUTING.md) |
| Inspect what was verified | [QA evidence](qa-learnings/IMPLEMENTATION_QA.md) and [CI](https://github.com/richardsondx/VESSEL/actions/workflows/ci.yml) |

Current contribution priorities are independent primary-evidence review, difficult
visual retrieval cases, and sanitized adapter fixtures. The
[contributor guide](CONTRIBUTING.md) explains the evidence each contribution needs.

## Citation and rights

Cite the software using [CITATION.cff](CITATION.cff). For an experiment, also identify
the code commit, benchmark version, dataset hash, protocol, configuration, and run
manifest. A citation to development software does not imply a validated benchmark
release. Cite the primary publishers and datasets used in your analysis separately.

Code is [Apache-2.0](LICENSE). Original VESSEL annotations are
[CC BY 4.0](data/LICENSE). Source visuals and documents retain their own rights;
VESSEL publishes references and hashes where redistribution is unavailable.
