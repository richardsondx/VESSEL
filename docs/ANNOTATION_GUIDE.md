# Gold annotation and independent review

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
