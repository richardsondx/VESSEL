# keenable-browser

Keenable results captured through the keenable.ai website in the browser
(Richardson's signed-in Google session), replayed from a JSON capture
file. Used because the benchmark runs Keenable through the browser per
Richardson's standing instruction, not the API.

- No API calls. The capture file is the pinned request artifact: it
  records the exact queries, result lists, and capture timestamps.
- Capture file path via `KEENABLE_BROWSER_CAPTURE` env var. Format:
  `{"queries": [{"query_id", "query", "captured_at", "results":
  [{"url", "title", "snippet"}]}]}`. Entries match on normalized query
  text.
- Each captured result becomes one document bundle (source only), like
  the Tier 2 text engines. No API cost; budget reservation still applies.
- Calibration only: browser captures are not pinned API request shapes,
  so this configuration is documented as a methodological deviation for
  the calibration run, not for final benchmark claims.
