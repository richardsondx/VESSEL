# Human review workspace

VESSEL includes a private browser workspace for authoring evidence tasks and
recording independent human review. The public results explorer remains read-only.
No provider requests or paid model calls occur in this workspace.

## Start locally

From the repository, build the browser application once:

```sh
cd explorer
npm ci
npm run build
cd ..
uv run vessel review-ui
```

Open <http://127.0.0.1:8788/review>. The service binds only to loopback. Its default
workspace file is `.private/review-workspace/workspace.json`, excluded from Git.
Use `--workspace PATH` or `--port PORT` for a separate workspace.

## Review prepared benchmark tasks

The repository includes three real, source-linked development proposals. Starting
`vessel review-ui` loads them into the inbox without replacing existing work. These
are AI-assisted proposals, not approved gold or the twenty-query pilot.

1. Enter your actual name and select **First reviewer / task author**.
2. Select a prepared question and click **Start first review**. This assigns the
   first human review to you; it records no approval.
3. Read the proposed question. The visual appears automatically above the notes;
   select it to inspect it at full size. Open the publisher page and data links.
   Check whether they answer the question and whether the required components are fair.
4. In **Decision & history**, complete the five checks, add your verification notes,
   confirm your own human review, then approve or request changes.
5. Send the exported packet to a different human for the independent review below.

You do not need to write questions or enter evidence links for prepared tasks.
If a proposal is wrong, request changes or edit it before approval. Preparation
is distinct from human verification; no AI identity counts as a reviewer. The
initial batch uses one visual publisher and cannot establish broad coverage,
external holdout, or Core-100 readiness. Its dynamic endpoints have no frozen
data vintage; check current metadata before approving.

## Author a custom task

1. Enter your actual reviewer name and select **First reviewer / task author**.
2. Choose **Author custom task**. Start from primary publisher evidence independently of
   provider output, following the [annotation guide](ANNOTATION_GUIDE.md).
3. Write the question and specify domain, visual type and evidence family.
4. Add acceptable answers. Identify the document and exact visual, verify the
   publisher, distinguish PDF page indices from printed labels, and explain the
   primary-source verification. Add multiple acceptable answers where justified.
5. Select only the components the task legitimately requires. Data availability
   and original-visual requirements are explicit; missing data is not invented.
6. **Save draft**, then open **Decision & history**. Inspect the primary evidence,
   complete all five checks, add verification notes, confirm your own human review,
   and choose **Approve & send for second review**.

Drafts persist after saving. Unsaved edits are visibly marked; leaving or switching
tasks asks before discarding them. Evaluation tasks need a preserved index freeze
that predates their creation. Existing development queries cannot be backdated.

## Independent review

Export a review packet and send a copy to a distinct human. That person starts their
own local workspace, imports the packet, enters their name, and selects
**Independent reviewer**. They inspect the primary sources themselves, without
provider results, rankings or scores, and choose **Approve this version** or
**Request changes** with specific notes. Independent reviewers cannot edit the
author's proposed gold. Requested changes remain in the history.

The second reviewer exports their updated packet for the author to import. Compatible
histories merge; divergent or older packets cannot overwrite local work. If two
people revised the same task concurrently, keep both packets and resolve the
conflict before importing. Do not fabricate a second identity to approve your own
work. Reviewer names are recorded attestations, not authenticated accounts; this
local application is not a hosted multi-user service.

## Revisions and exports

Editing question content, evidence, requirements or membership makes earlier
approvals stale. Previous content and decisions remain available in the history.
The author and second reviewer must approve the revised content again.
The author can restore an earlier snapshot as a new draft from the history.
Restoration does not reactivate the older content's past approvals.

Both export buttons save a real file under the workspace's `exports/` directory
and attempt a browser download. The success message includes the saved file's
absolute location, so it remains usable in browsers without download support.

- **Export review packet** preserves drafts, previous content and decisions for
  backup or transfer. Share it only with the intended reviewer.
- **Export reviewed gold** produces GoldRecord JSONL containing only tasks with
  current author and independent approvals, using the harness's Python digest.
  It does not publish anything or certify a Core-100 release.

Before running a dataset, validate it with `uv run vessel validate PATH.jsonl`.
Before comparative publication, complete all release and audit gates, including
`--release` validation. A twenty-task pilot is not a completed Core-100 release.
