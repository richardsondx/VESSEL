# VESSEL

**Visual Evidence Search & Source Evaluation Live** — an independent, open
benchmark for retrieving primary visual evidence and its source trail.

Provider characterization determines invocation, never success.

Status: development infrastructure. No validated Core-100 or provider leaderboard
has been released. Synthetic fixtures test software; they are not provider results.

See [SPEC](SPEC.md), [methodology](METHODOLOGY.md), [contamination policy](CONTAMINATION.md),
[Evidence8 study](docs/EVIDENCE8_STUDY.md), and [implementation status](docs/IMPLEMENTATION_STATUS.md).

## Run offline

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and Node.js 22.12+ for the explorer.

```sh
uv sync --frozen --python 3.12
uv run vessel validate data/synthetic-pilot.jsonl
uv run vessel run data/synthetic-pilot.jsonl configs/replay.yaml runs/demo \
  --fixture tests/fixtures/replay.json
uv run vessel replay runs/demo
uv run vessel export runs/demo explorer/public/report.json
npm --prefix explorer ci
npm --prefix explorer run dev
```

The explorer loads an exported `report.json`, or the clearly labeled synthetic demo.
It also imports local JSON reports, filters query outcomes, inspects coherent bundles,
and downloads artifacts. No keys or provider calls run in the frontend.

## Configure live providers

Copy `.env.example` to ignored `.env`. Evidence8 requires a configured workspace
API base URL; `evidence8.com` is not a hosted API base. Other adapters use the official
Keenable, Exa and Serper interfaces. Missing credentials skip only the corresponding
provider. Keyless Keenable is opt-in via configuration.

Set conservative `request_cost_ceiling_usd` values in a copy of `configs/live.yaml`
and an explicit `max_cost_usd`/`max_requests`. A null ceiling skips the provider.
Costs are reservations/estimates, not a guarantee about provider billing. No paid
requests run in CI. HTTP failures are recorded without automatic billable retries.

```sh
uv run vessel run path/to/reviewed-gold.jsonl configs/my-live.yaml runs/core-100
uv run vessel run path/to/reviewed-gold.jsonl configs/my-live.yaml runs/core-100 --resume
uv run vessel report runs/core-100
uv run vessel compare runs/a/report.json runs/b/report.json runs/comparison.json
```

`configs/hybrid.yaml` records Keenable, Evidence8 and the document-conditioned hybrid
as separate systems. The hybrid searches Evidence8 using the original information
need plus each of Keenable's first five unique document URLs, attaching only bundles
whose source URL matches. It makes no claim of a native document-enrichment endpoint.
For Keenable plus shared extraction, use `search_fetch`; for Keenable alone use
`search`. Comparisons across protocols are shown separately.

Use a fresh output directory when changing code, data or configuration. Reservations
persist before requests; an interrupted call may be charged again on resume, within
the remaining cap. Receipts and content-addressed artifacts are integrity checked.
Runs and authenticated artifacts are ignored by Git. Review them before redistribution.

## Review and release

Follow the [annotation guide](docs/ANNOTATION_GUIDE.md). The 100-entry candidate queue
is discovery material; none of its entries is reviewed gold or attested holdout.
Human reviews bind to record digests and become stale when a record changes.

```sh
uv run vessel validate path/to/core-100.jsonl --release
uv run vessel audit runs/core-100 --reviewer HUMAN_NAME --notes 'Independent failure audit'
uv run vessel export runs/core-100 explorer/public/report.json --public-release
npm --prefix explorer run build
```

Public release rejects synthetic, unreviewed, unattested, incomplete or unaudited runs.
A human audit binds to every archived response; changing receipts invalidates it. Domain
publication follows independent validation; this repository does not deploy to
`vessel.evidence8.com` automatically.

## Verification

```sh
uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
npm --prefix explorer test
npm --prefix explorer run build
```

[Schemas](schemas/) define gold, normalized bundles/responses, adjudications and run
manifests. Provider implementations cannot import gold/scoring. Full Support MRR
refers to the first complete supporting bundle, not the first matching document.

## Later milestones

Validated Core-100 → Core-500 → VESSEL-Live → Trace → Research. Internal Evidence8
ablations require reproducible exposed configurations and are outside v0.1.
