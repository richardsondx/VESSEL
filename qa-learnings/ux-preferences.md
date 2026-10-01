# VESSEL UX review context

No personal visual preferences have been asserted by the user.

Explicit product constraint: public provider characterization is factual and
sanitized; provider characteristics determine invocation, never success.

Implementation principle: every development/replay report carries a persistent
status notice; simulated values must never look like empirical provider rankings.
Scope: explorer, report downloads, README and public release validation.
Verification: runtime report schema, offline tests, desktop/mobile browser review.

## Review workflow experience — 2026-10-01

User quote: "what's a review workflow. did we build one that is user friendly well
designed experience?" Followed by "do it" after a browser workspace was proposed.

Interpretation: human review must be an executable browser journey, with guided
evidence inspection and decisions, rather than documentation and CLI commands
alone. Scope: task authoring, independent gold review, corrections and packet
transfer. This is a product requirement, not an inferred personal visual style.

Implementation: private task inbox, authoring forms, source/checklist inspection,
provider-free independent mode, version-bound decisions and file exports.
Verification: backend review lifecycle/packet/digest tests plus actual desktop and
390-pixel mobile browser journeys. Simulated approval tests use isolated synthetic
practice records; real gold receives no automatic human approval.

QA rule: **Usable review handoff** — export must save a real local file and report
its location even when the in-app browser does not expose a download event.
Executable protection: `test_review_export_matches_python_digest_and_survives_reload`
checks actual packet and JSONL files; browser export is checked against that output.
