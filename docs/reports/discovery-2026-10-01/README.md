# VESSEL retrieval diagnostics — 1 October 2026

This is an archived, unscored discovery report: ten queries, three systems,
30 successful searches, and 300 returned results. **Retrieval correctness has
not been evaluated.** Field counts are response metadata, not accuracy, recall,
Full Support, or a provider quality ranking. The report is not an eligible
benchmark release.

## Open locally

Open `index.html` directly in a browser, or serve this directory:

```sh
python3 -m http.server 8769 --bind 127.0.0.1 --directory docs/reports/discovery-2026-10-01
```

Then visit http://127.0.0.1:8769. The report embeds its data, uses no external
JavaScript dependencies, and makes no provider searches. Publisher and visual
links are followed only when clicked. Evidence8 visual links point to the local
API recorded in the original run and require that service to be running.

## Contents and rebuild

- `index.html`: portable report with embedded normalized response data.
- `template.html`: presentation source.
- `report-data.json`: archived normalized responses, derived diagnostic summaries,
  run manifest, and recorded response-file SHA-256 hashes.
- `build_report.py`: embeds the archived data into the template; no scoring or
  provider requests.

```sh
python3 docs/reports/discovery-2026-10-01/build_report.py
```

The data originated in the local `runs/discovery-10-2026-10-01` diagnostic.
The original raw provider artifacts and receipts are not included here. Integrity
and normalization checks described in the report are recorded findings from the
original run, not checks repeated by the renderer. Recorded response-file hashes
refer to those original files, not this export.

## Interpretation

Field inventory counts results carrying document, visual, publisher, location,
or dataset references in their normalized bundles. A populated reference may be
irrelevant or incorrect; an absent field does not prove retrieval failure.
Adapter behavior also influences these fields. No URL or visual is certified by
this report.

Latency uses recorded successful-call durations, with linearly interpolated p50
and p95 over ten calls per system. Evidence8 used a local API, while Keenable
and Exa used remote services. URL overlap compares exact saved URLs. Unknown
costs are left unknown. The run has no independently accepted gold, pre-authoring
index attestation, or attested external holdout membership.

Presentation was inspired by [NEEDLE](https://keenableai.github.io/needle/).
