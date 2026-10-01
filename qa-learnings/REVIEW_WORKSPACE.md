# Review workspace

Status: COMPLETE — local workflow verified; human acceptance pending.

Contract: a human can create and revise evidence tasks, inspect primary sources,
complete a guided checklist, request changes or approve, and transfer a private
review packet to another human entirely through the browser.

Local scope: loopback service, atomic file persistence, portable packets; no hosted
accounts, provider requests or publishing. Named reviewer identities are recorded
human attestations, not verified logins. No AI-created human approvals.

Acceptance: empty state and queue, draft validation, author/independent modes,
distinct reviewers, provider-free review data, version-bound approvals, disagreement
history, recovery after reload, import/export and executable GoldRecord export.

Verification: backend workflow/integrity tests, frontend type/build checks,
cross-language exported dataset validation, desktop/mobile browser journeys.

Verified: 96 backend tests and 14 browser-logic tests pass; Ruff, TypeScript and
Vite production build pass. Actual browser journeys cover draft creation, primary
reference editing, multiline aliases, saving/reload, author verification,
distinct-reviewer enforcement, requested changes, independent approval, revision
invalidation, restoration without approval reactivation and packet import/export.
Desktop at 1280 pixels and mobile at 390 × 844 have no horizontal overflow.
Visual preview renders an isolated synthetic SVG. Console inspection found no
application errors. PDF embedding is publisher-dependent and has an explicit
open-source fallback; it is not claimed universally embeddable.

Export integrity: JSONL generated from the browser-authored synthetic practice task
passes Python GoldRecord validation and digest-bound approval checks. The in-app
browser does not expose a download event; export therefore writes real local files
and shows their absolute location. Actual packet and JSONL output files were checked.
All simulated reviews are isolated in `.private/review-qa/`; the user's default
workspace starts empty. No provider search or paid model requests occurred.

Boundary: local named human attestations, not authenticated reviewer accounts or
hosted collaboration. The service binds loopback and rejects cross-origin writes
and unrecognized Host headers; these controls have an executable HTTP regression.
