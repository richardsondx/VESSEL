# Prepared benchmark review

Status: COMPLETE for starter workflow; full pilot preparation remains pending

Customer value: a reviewer opens prepared questions and proposed primary evidence,
checks correctness, and records a decision without inventing a benchmark task.

Acceptance: prepared drafts contain questions, source/asset/data references and
verification notes; preparation is labeled AI-assisted and creates no human
approvals; first human can adopt a draft for review; existing work is preserved;
second human remains mandatory; development tasks make no holdout/release claim.

Verification: batch integrity, idempotent loading, safe adoption, approval firewall,
actual browser queue and evidence-to-decision journey.

Verified: 97 backend tests, Ruff, TypeScript/Vite build and 14 frontend tests.
Actual browser: three prepared questions appear alongside the user's existing
draft; source links and proposed requirements are visible; an isolated QA
workspace's Start first review assigns a name and shows the decision checklist
with all approvals empty. Real workspace proposals remain unassigned and have
zero human decisions. No paid provider requests were made.

Screenshot: .private/prepared-review-qa/prepared-inbox.png (real workspace).
Primary public pages plus SVG and CSV returned HTTP 200. OWID chart API docs
confirm downloadable endpoint conventions. Source definitions were inspected
through public publisher pages. Human source verification remains outstanding.

Limit: the starter batch is three development charts from one publisher. It does
not fulfill the 20-query pilot, balanced Core-100, independent-review or release
gates. Its URLs are dynamic, membership unknown, and no data vintage is frozen.
