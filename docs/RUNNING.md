# Running and releasing VESSEL

Start with the [README quickstart](../README.md#quickstart) for a local synthetic run.
All commands below execute from the repository root.

## Configure live providers

Copy `.env.example` to ignored `.env`. Evidence8 needs a configured workspace API
base URL; `evidence8.com` is not a hosted API base. Other adapters use their documented
HTTP interfaces. Missing credentials skip only the corresponding provider. Keyless
Keenable access is opt-in, not the default.

Copy `configs/live.yaml` to a run-specific configuration. Set conservative
`request_cost_ceiling_usd` values and an explicit `max_cost_usd`/`max_requests` cap.
A null per-request ceiling skips the provider. Zero is appropriate only for a
confirmed free/local interface. Reservations are estimates, not billing guarantees.
No paid requests run in CI; HTTP failures do not trigger automatic billable retries.

The following paths are placeholders for your independently reviewed dataset and
configured run. They are not released Core-100 artifacts.

```sh
uv run vessel run path/to/reviewed-gold.jsonl configs/my-live.yaml runs/core-100
uv run vessel run path/to/reviewed-gold.jsonl configs/my-live.yaml runs/core-100 --resume
uv run vessel report runs/core-100
uv run vessel compare runs/a/report.json runs/b/report.json runs/comparison.json
```

Compare requires matching data and protocol configuration and complete runs.
For Keenable alone, select `search`; for Keenable plus shared extraction, select
`search_fetch`. Report protocols separately.

Use a fresh output directory when changing code, dependencies, data or configuration.
Reservations persist before transmission. An interrupted request may have been billed
without a receipt; retrying it on resume reserves another call within the remaining
cap. Receipt, dataset, configuration and code artifacts are integrity checked.

Runs and authenticated artifacts are ignored by Git. Sanitize and review them before
redistribution. Keep credentials and private endpoints out of public artifacts.

## Hybrid evaluation

`configs/hybrid.yaml` evaluates Keenable, Evidence8 and Keenable + Evidence8 as
separate systems under the evidence protocol. Each system consumes its own requests,
including repeated underlying calls.

The hybrid searches Evidence8 using the original information need plus each of
Keenable's first five unique document URLs. It attaches only bundles whose source
URL matches that document. This uses documented search capability and does not
claim a native document-enrichment endpoint. Additional calls, observations, costs
and incomplete enrichment are recorded. Underlying providers must both be configured.

## Review and publication

Follow the [annotation guide](ANNOTATION_GUIDE.md). Discovery candidates are not gold.
Human reviews bind to record digests and become stale when content changes.

```sh
uv run vessel validate path/to/core-100.jsonl --release
uv run vessel audit runs/core-100 --reviewer HUMAN_NAME --notes 'Independent failure audit'
uv run vessel export runs/core-100 explorer/public/report.json --public-release
npm --prefix explorer run build
```

The reviewer and notes must record an actual human audit. Public release rejects
synthetic, unreviewed, unattested, incomplete or unaudited runs. Audit approval binds
to the archived responses; changing them invalidates approval. These commands do not
publish a domain. Deploy only after the [release gates](IMPLEMENTATION_STATUS.md) pass.

## Verify a change

```sh
uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
npm --prefix explorer test
npm --prefix explorer run build
```

Run `uv run vessel --help` for the full command list. `report` re-scores archived
receipts; `replay` verifies the archive and reproduces scores without provider calls.
