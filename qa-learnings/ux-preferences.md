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

## Prepared review inbox — 2026-10-01

Exact feedback: "why should i write a specific questiojn? why they are not prepared
for me in advance.. wasnt i supposed to review things fro the benchmark?"

Confirmed product requirement: review begins with prepared questions and proposed
primary evidence. Authoring is optional. The agent owns preparation; humans own
verification and decisions. Scope: /review; this does not authorize fabricated
reviewer identities, approvals or provider-derived gold.

QA rule: **Review starts with prepared work**. Check actual inbox contents, not
just form functionality. Preparation must preserve existing drafts and decisions,
remain idempotent, and never count as a human review.
Executable protection: `test_prepared_inbox_preserves_work_and_requires_two_humans`.
Initial implementation has three real development proposals; this is a starter
batch, not the twenty-query pilot or Core-100. Browser verification recorded in
PREPARED_REVIEW.md. Confidence: explicit user correction.

## Visual-first review — 2026-10-01

Exact feedback: "why it's not showing the visual directly ... it would make it
easier for a reviewer to see the visual directly no?"
Confirmed requirement: the object being judged must appear immediately in its
review context. Scope: /review evidence cards. Visual precedes long verification
notes; full-size access remains available. Missing/failed images retain source
links, and PDFs use the recorded page when no image exists.
QA rule: **Visual first**, enforced by rendered-component tests in
explorer/src/evidence.test.tsx and actual browser inspection. This correction
strengthens the review workflow's acceptance criteria beyond form mechanics.

## Explicit checkbox decisions — 2026-10-01

Exact feedback: "these dont tell me when i should check or leave uncheckl."
Confirmed requirement: review attestations need observable pass/fail criteria,
not definitions alone. The alternatives check states the proposed-answer count,
that one answer can suffice, and what wrong/missing/uncertain answers require.
Requirements help depends on whether the current task requires data; no-data
questions do not require a dataset to pass. Unknowns remain unchecked and receive
notes/requested changes. No human decisions were made by the agent.
Executable protection: review.test.ts checks guidance for one answer and both
required/optional data cases. 18 frontend tests and TypeScript/Vite build pass.
Browser verified in a separate tab to preserve the user's current transient
checkboxes. Screenshot: .private/prepared-review-qa/checklist-guidance.png.
Requested empty draft pilot-74cb3d90 was removed from the private workspace with
an archived copy; all three prepared tasks remain unchanged. No deletion feature
or permanent data deletion was introduced.
