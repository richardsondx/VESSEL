# Implementation QA evidence

Recorded September 30, 2026 (America/Toronto). All provider traffic in software
checks uses mock HTTP transports or clearly synthetic fixtures.

- `uv run pytest -q`: **81 passed**. Identity/equivalence, original versus generated,
  precise localization, alternatives, coherence, version/data/supplemental dimensions,
  independent reviews, freeze/holdout requirements, duplicates, provider normalization,
  malformed/error responses, budgets, missing credentials, interrupted runs, persisted
  reservations, dependency changes, receipt/code integrity and deterministic replay.
- Ruff lint and format checks pass. JSON schemas regenerate from strict models.
- Offline replay: 20 synthetic queries × 4 systems, 80 cells, zero requests and $0
  reserved cost. Re-score is deterministic; identical resume succeeds. Synthetic
  public release is rejected by tests.
- `npm ci`, `npm test`: **10 passed**. Artifact shape, unsafe links, publication
  contradictions, missing/duplicate cells/depths and JSON MIME fallback.
- `npm run build`: passes TypeScript and Vite production compilation.
- `npm audit`: zero vulnerabilities in the locked dependency tree at verification.

Browser journeys in the Codex in-app browser:

- Default synthetic report loads with explicit fixture notice and zero paid usage.
- Provider/domain/outcome filters narrow to one known synthetic result.
- Inspector exposes accepted gold, source/provenance and coherent Full Support diagnostics.
- A filter change clears the inspector; no-match state is visible.
- Local valid JSON import succeeds; invalid fixture JSON shows an error; subsequent
  valid import recovers.
- Statistical breakdowns, paired differences and supplemental recall are visible.
- 390 × 844 mobile view renders without document-width overflow. Override reset.
- Artifact download exposes a persistent blob link with the expected `.json` filename.
  The in-app browser did not deliver a download event/path; filesystem delivery remains
  unverified there. CLI export produces a verified local JSON artifact independently.

Non-blocking toolchain messages: PyMuPDF SWIG deprecation warnings and upstream Zod
pure-annotation warnings during Rollup. Neither failed a check.

Live provider behavior, independent human annotations, freeze attestations, empirical
leaderboards and domain publication remain unverified. GitHub CI results should be
checked separately from these locally executed checks.

Configuration follow-up: `vessel doctor` checks only set/missing state and budget
prerequisites. Tests verify current-directory `.env` loading, exported-variable
precedence, no network requests and no secret values in diagnostics or YAML errors.
Local credential files remain ignored; diagnostic commands make no provider requests.

## Separate live connectivity check

User authorized a $1 total smoke-test cap. Exactly one Keenable `pro` search and one
Exa `auto` search requested three results each. Both returned `ok` and three normalized
results. There were no retries, fetches, scoring or scientific performance conclusions.
Each request reserved $0.25; total reservation was $0.50. Exa reported $0.007;
Keenable supplied no dollar cost. Provider-reported costs are not audited invoices.
The response artifacts and reservation manifest remain under ignored `runs/`.
Evidence8's public `/v1/search` URL served HTML, not an API response; the configured
local API was not running. No Serper key was found in the inspected local SEOBeaver
configuration, and no Serper request was made.
