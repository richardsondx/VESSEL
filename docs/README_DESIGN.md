# README design research

Research date: September 30, 2026 (America/Toronto). Primary sources: each project's
current GitHub README and repository metadata. The
[reference manifest](research/public/readme-reference-manifest.json) records exact
retrieval timestamps, star counts and hashes. Source README files are not redistributed.

## Recommendation

**MTEB is the closest structural reference for VESSEL's README.** Its concise
navigation, short runnable example, and routes into tasks, results and contribution
serve people arriving with different jobs. This is an editorial judgment from the
observed document, not evidence that its layout caused adoption.

Combine that navigation pattern with BEIR's data transparency, SWE-bench's concrete
reproduction paths, LM Evaluation Harness's configuration specificity, and HELM's
connection between execution and inspectable results. Needle is useful for its
compact mapping from benchmark tasks to scoring and its explanation of shared
execution rules. VESSEL's wording, examples, organization and task definitions are
original.

## Repositories studied

Stars are GitHub API snapshots, not quality scores or measures of scientific validity.

| Repository | Stars at inspection | Useful observed pattern | VESSEL application |
|---|---:|---|---|
| [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) | 14,105 | Backend-specific usage and documentation links make evaluation settings explicit | Put run/configuration details in a linked operator guide |
| [SWE-bench](https://github.com/SWE-bench/SWE-bench) | 5,940 | Defines the task, supplies setup and evaluation commands, and links datasets, contribution and citation | Explain success concretely, then show an executable path and its outputs |
| [MTEB](https://github.com/embeddings-benchmark/mteb) | 3,440 | Early navigation, short examples, and a documentation map for tasks/models/results/contributions | Give scientists, researchers and developers distinct starting points |
| [HELM](https://github.com/stanford-crfm/helm) | 2,929 | Quickstart connects running, summarizing and viewing; reproduction links accompany research outputs | Make artifact inspection part of the reproduction journey |
| [BEIR](https://github.com/beir-cellar/beir) | 2,305 | Dataset table exposes availability, splits, sizes and checksums alongside runnable retrieval examples | Clearly inventory available fixtures, candidates and unreleased gold |
| [Needle](https://github.com/keenableai/needle) | 32 | Early task/scoring table and explicit shared configuration rules | Keep protocol and scoring summaries compact and operational |

Needle is a relevant search-benchmark reference rather than a high-star example.
These repositories were selected for adoption and relevance to retrieval/evaluation;
this was not an exhaustive ranking of all benchmark repositories.

## Reader requirements

| Reader | Questions the README should answer | Concrete content |
|---|---|---|
| Scientist | Does the retrieved object actually support the intended information need? Who checked it? | Coherent bundle example, primary-source trail, review process, annotation rights |
| Researcher | Can I interpret, reproduce and challenge the comparison? | Scoring definition, protocol boundaries, versions, leakage/holdout policy, failure accounting |
| Developer | Can I run it without an account? How do I extend it? | Credential-free replay, expected output, schemas, adapters, contribution instructions |

## Changes made

1. Lead with VESSEL's measurement unit: visual, primary source, location and applicable data.
2. Place the development/review status near the top, next to useful navigation.
3. Offer a short credential-free journey with expected counts, costs and artifact path.
4. Use an original hypothetical example to explain document recall versus Full Support.
5. Put protocol allowances beside their comparison boundaries.
6. Inventory data artifacts with explicit scientific status; do not turn discovery
   counts or software fixtures into benchmark release claims.
7. Move detailed configuration, hybrid strategy and release operations into
   `docs/RUNNING.md`; add concrete contribution instructions in `CONTRIBUTING.md`.
8. Include citation/version requirements and separate code, annotation and source-asset rights.

The README has no provider-performance table, invented paper, DOI, deployed demo
link, or download badge implying a scientific release. Its CI badge refers to an
existing workflow; links resolve to current files or actual source repositories.

## When Core-100 is released

Replace the pending status with a versioned dataset card and stable artifact links.
Add one independently reviewed example with a redistributable source visual or a
reference/hash when rights prohibit inclusion. Link an audited results explorer and
report downloadable manifests. Explain comparison settings next to every result table;
retain uncertainty and failure accounting. Add a release DOI only after registration.

A future usability check should ask a scientist to locate an accepted source and
review history, a researcher to identify what a number means and how to reproduce
it, and a developer to complete the no-key quickstart. Those user studies have not
been conducted; the current checks establish document and command correctness.
