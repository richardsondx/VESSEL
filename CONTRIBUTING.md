# Contributing to VESSEL

VESSEL needs contributions that make visual-evidence measurement more reproducible.
Start with the [specification](SPEC.md), [methodology](METHODOLOGY.md), and
[current release status](docs/IMPLEMENTATION_STATUS.md).

## Contribute evidence or independent review

We welcome difficult original-source, PDF-hidden, temporal, comparative, and ambiguous
visual retrieval cases. Include a primary publisher reference, the intended information
need, known valid alternatives, and the uncertainty that makes the case useful.
A suggestion is discovery material, not automatically benchmark gold.

Follow the [annotation guide](docs/ANNOTATION_GUIDE.md). Evaluation query authoring
must follow index freeze. Every published query needs author review and a distinct
independent human reviewer; AI assistance cannot substitute for that reviewer.
Record exact source/asset identities, location, version and applicable datasets.
Resolve disagreements before requesting release inclusion.

## Add or improve a provider

Document the tested interface and observed capabilities in `docs/providers/` before
evaluation. Implement normalization under `src/vessel/adapters/`, configure the
factory in `src/vessel/runner.py`, and add offline mock/replay coverage under `tests/`.

Preserve ranking and actual result count. Record missing fields, timing, usage,
additional requests, errors and skips. Include sanitized fixtures and describe the
source/version of their shapes. Do not present mocks as captured live responses.
Adapters and extraction cannot access gold or import the scoring module.
Provider characterization determines invocation, never what constitutes success.

## Report an incorrect score or software failure

Open an [issue](https://github.com/richardsondx/VESSEL/issues/new) with the code commit,
benchmark/configuration versions, query ID, protocol and a minimal sanitized replay.
Explain the expected behavior and point to primary evidence when disputing identity,
localization or equivalence. Include the failure status and relevant observations.
Do not upload credentials, private endpoints or source assets without redistribution
rights. A newly discovered acceptable answer needs human adjudication, not a
provider-specific scoring exception.

## Submit a change

Keep the change focused and explain the problem, resulting behavior and verification.
Use the [running guide's checks](docs/RUNNING.md#verify-a-change) for code changes.
Documentation changes should have working links and executable commands. CI runs
without paid API requests. Substantive task/scoring revisions require a new benchmark
version and apply equally to every provider.

Code contributions use Apache-2.0; original annotation contributions use CC BY 4.0.
Third-party assets retain their own rights. See [LICENSE](LICENSE) and
[data licensing](data/LICENSE).
