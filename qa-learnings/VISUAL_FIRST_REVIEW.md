# Visual-first review

Status: COMPLETE — local browser verified; human acceptance pending

User feedback: "why it's not showing the visual directly .. since the whole
benchamark is based on checking visual correctness ... it would make it easier
for a reviewer to see the visual directly no?"

Acceptance: known image loads automatically above verification notes; full-size
view is available; exact image takes precedence over its containing PDF; missing
or failed visual has a useful source fallback; existing decisions are untouched.
Verification: rendered-component regression checks and actual local browser.

Verification: 17 frontend tests passed, TypeScript/Vite production build passed.
The actual review tab rendered the publisher SVG automatically (850×600 natural
dimensions), before verification notes. Clicking Enlarge visual opened the actual
publisher SVG in a new tab. Screenshot saved at
.private/prepared-review-qa/visual-first-review.png. No human decisions changed.
PDF rendering is browser/publisher dependent; component test confirms recorded
zero-based page index maps to the correct one-based PDF fragment.

Executable rule: Visual first — evidence.test.tsx asserts immediate image
rendering before notes, image precedence over a containing PDF, recorded PDF
page fallback, missing-preview explanation and full-size access.
