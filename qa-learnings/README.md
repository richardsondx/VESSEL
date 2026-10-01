# QA conventions

Verify offline replay, scoring edge cases, budgets, persistence and browser journeys.
Never label synthetic fixtures or candidate gold as reviewed benchmark observations.
Every release claim must have a corresponding artifact or executable check.

## Regression: missing report fallback

Principle: a successful HTTP status does not establish artifact type; SPA dev servers
can return an HTML shell for missing JSON paths.
Enforcement: explorer `default report loading` tests check MIME before parsing and
verify fallback and missing-artifact states. Browser review caught and fixed this.

## Regression: stable review digests

Principle: unordered fields must serialize deterministically across processes.
Enforcement: gold requirements serialize in sorted order; subprocess regression
uses distinct PYTHONHASHSEED values to verify identical review digests.

## Regression: page versus visual identity

Principle: the right document page can contain the wrong visual.
Enforcement: `test_page_only_not_visual_identity` requires accepted asset identity
or a precise figure/bbox/web locator before awarding visual recall.

## Regression: filtered inspector and imported depths

Principle: inspection must reflect the active query population; imported summaries
and cells must have every supported K before rendering.
Enforcement: filter changes reset selected evidence; artifact tests reject missing
summary/score depths and duplicate cells. Browser verifies no-match inspector reset.
