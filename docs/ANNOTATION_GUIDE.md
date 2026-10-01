# Gold annotation and independent review

## Practical human workflow

Gold is the verified answer specification for a task, not the result preferred by a
provider. It includes the evidence object, provenance and exact requirements.

Start by reviewing five newly authored tasks together to check the instructions,
then complete the twenty-task pilot. Evaluation tasks must be authored after an
index freeze. Keep existing discovery queries as development diagnostics; do not
use their search results to select answers for the evaluation set.

The author may be the project owner. The independent reviewer must be a different
human who did not author the task and can assess its subject matter. A researcher,
data analyst or suitably qualified colleague can fill this role. Record relevant
provider affiliations or conflicts when publishing the methodology. AI can prepare
records, locate sources and flag inconsistencies; it cannot provide either human
approval or serve as the independent reviewer.

For each task, the author inspects the primary publisher's page or PDF and records:

- A specific, realistic query with enough scope to identify acceptable answers
  (measure, population, period, geography or experiment, where relevant).
- The publisher, original document and exact visual; canonical URLs, version,
  figure locator and available computed hashes.
- Whether the visual is publisher-original, a crop, a reproduction or generated.
- The components required for success. Require data only after confirming that
  the publisher actually offers the relevant underlying dataset.
- Acceptable alternatives and why they satisfy the same information need.
- Evidence-family membership and honest index-membership status; unknown remains
  unknown and cannot count toward external-holdout claims.

Give the independent reviewer the query, proposed gold and primary-source references,
without provider names, returned rankings or benchmark scores. The reviewer checks
the original sources themselves, including whether alternatives were overlooked,
whether the task is ambiguous and whether every required component is obtainable.
They record approval or concrete requested changes. Resolve disagreements by
inspecting the primary source, not by majority vote among providers. Revised gold
needs fresh digest-bound approvals.

An operational worksheet is not itself a valid dataset. Once the worksheet is
complete, encode it as GoldRecord JSONL, validate it, and record the two actual
human decisions. For example, replacing the file, query ID and reviewer names:

```sh
uv run vessel validate data/pilot-reviewed.jsonl
uv run vessel review data/pilot-reviewed.jsonl pilot-001 \
  --reviewer 'Actual author name' --role author \
  --notes 'Checked primary document, figure identity and requirements.'
uv run vessel review data/pilot-reviewed.jsonl pilot-001 \
  --reviewer 'Actual second reviewer name' --role independent \
  --notes 'Independently inspected primary source and acceptable alternatives.'
```

Run these commands only after the named person has made the recorded decision.
The independent reviewer can request changes using `--decision changes_requested`.
The `--release` validator enforces Core-100's full composition; a twenty-task pilot
does not pass that final release gate.

## Detailed annotation sequence

1. Obtain an Evidence8 version/index freeze attestation before authoring evaluation
   queries. Existing candidate information needs are development material; newly
   authored evaluation queries must follow the freeze.
2. Select a primary publisher visual. Record exact canonical document/asset URLs,
   source identifiers and available source hashes. Resolve publisher versus host
   versus data originator. Do not use a provider response as gold.
3. Record original/generative status, version/vintage, exact PDF page index and
   printed label, figure ID/bbox, or stable web locator. A page number alone is not
   sufficient to establish visual identity without an accepted asset identity.
4. Inspect applicable underlying source data. Require it only when actually offered;
   never use extracted approximate values as if they were publisher data.
5. Write a plausible information need without copying the caption. Inspect lexical
   overlap and alternative valid answers. Keep associated queries in one family.
6. Build a GoldRecord using the exported schema. Include verification references,
   verification notes, creation time, taxonomy and attestation. Mark unknowns honestly.
7. Run `vessel validate dataset.jsonl`. The author records a human decision with
   `vessel review dataset.jsonl QUERY_ID --reviewer NAME --role author --notes '...'`.
8. A distinct human independently inspects primary evidence and records their own
   decision with `--role independent`. Changes-requested decisions block approval
   until that reviewer approves the revised record. Content changes invalidate old
   digest-bound approvals.
9. Use `vessel validate dataset.jsonl --release` before comparative publication.
   Exact Core-100 composition and forty attested holdout records are enforced.
10. Freeze the dataset digest, run provider configurations, audit each failure,
    document human equivalence decisions and export via `--public-release`.

Candidate source pages are navigation aids, not answers. Do not silently convert
pre-freeze development candidates into post-freeze evaluation gold.
