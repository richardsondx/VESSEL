import { useEffect, useMemo, useState } from "react";
import { displayName, loadDefaultReport, parseReport, percent } from "./report";
import type { Cell, Report } from "./report";
import "./style.css";

const repo = "https://github.com/richardsondx/VESSEL";
function SourceLink({
  url,
  label = "Open source ↗",
}: {
  url: string;
  label?: string;
}) {
  return (
    <a href={url} target="_blank" rel="noreferrer">
      {label}
    </a>
  );
}
function Inspector({
  cell,
  k,
  onClose,
}: {
  cell: Cell;
  k: string;
  onClose: () => void;
}) {
  const score = cell.scores[k];
  return (
    <section className="inspector" aria-label="Query evidence inspector">
      <div className="section-label">
        EVIDENCE INSPECTOR <button onClick={onClose}>Close ×</button>
      </div>
      <h2>{cell.gold.query}</h2>
      <p className="muted">
        {cell.query_id} · {cell.gold.family_id} · {cell.gold.attestation.bucket}
      </p>
      <div className="inspection-grid">
        <div>
          <h3>Accepted gold</h3>
          {cell.gold.alternatives.map((g) => (
            <article key={g.evidence_id}>
              <strong>{g.evidence_id}</strong>
              <p>Requires {g.required.join(" · ")}</p>
              <p>
                {g.original_required
                  ? "Original publisher visual required"
                  : "Derived evidence permitted"}
              </p>
              {g.document.urls.map((u) => (
                <p key={u}>
                  <SourceLink url={u} />
                </p>
              ))}
              <p className="muted">
                {g.verification_notes ||
                  "No primary-source verification recorded."}
              </p>
              <details>
                <summary>Locations & identities</summary>
                <pre>
                  {JSON.stringify(
                    {
                      document: g.document,
                      visual: g.visual,
                      locations: g.locations,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
            </article>
          ))}
        </div>
        <div>
          <h3>{displayName(cell.provider)} returned</h3>
          <p>
            Status: {cell.response.status}
            {cell.response.reason && ` · ${cell.response.reason}`}
          </p>
          {cell.response.results.map((result) => (
            <article key={result.rank}>
              <strong>
                #{result.rank} {result.title || "Untitled result"}
              </strong>
              {result.url && (
                <p>
                  <SourceLink url={result.url} />
                </p>
              )}
              {result.bundles.map((bundle, i) => (
                <div className="bundle" key={i}>
                  <p>
                    Bundle {i + 1} ·{" "}
                    {bundle.visual?.rendition ?? "Document only"}
                  </p>
                  <p>{bundle.source.publisher ?? "Publisher unknown"}</p>
                  <p>{bundle.rights ?? "Rights unknown"}</p>
                  {bundle.datasets.map((d, j) =>
                    d.url ? (
                      <p key={j}>
                        <SourceLink url={d.url} label="Underlying data ↗" />
                      </p>
                    ) : null,
                  )}
                  <details>
                    <summary>Provenance & location</summary>
                    <pre>{JSON.stringify(bundle, null, 2)}</pre>
                  </details>
                </div>
              ))}
            </article>
          ))}
        </div>
      </div>
      <h3>Why this score?</h3>
      <div className="component-row">
        {Object.entries(score.components).map(([name, hit]) => (
          <span key={name} className={hit ? "hit" : "miss"}>
            {hit ? "✓" : "○"} {name}
          </span>
        ))}
      </div>
      <p>
        {score.full_support
          ? "A single bundle meets an accepted alternative."
          : `Full support not met: ${score.failure ?? "Missing requirements"}.`}
      </p>
      <p className="muted">
        Component recalls may come from different bundles; Full Support always
        requires one coherent bundle.
      </p>
      {score.diagnostics.map((d, i) => (
        <p className="diagnostic" key={i}>
          Rank {d.rank}, bundle {d.bundle + 1} → {d.evidence_id}:{" "}
          {d.full_support ? "full support" : `missing ${d.missing.join(", ")}`}
        </p>
      ))}
      <details>
        <summary>Fetch and provider observations</summary>
        <pre>{JSON.stringify(cell.response.observations, null, 2)}</pre>
      </details>
    </section>
  );
}
export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [k, setK] = useState("10");
  const [provider, setProvider] = useState("all");
  const [domain, setDomain] = useState("all");
  const [type, setType] = useState("all");
  const [membership, setMembership] = useState("all");
  const [outcome, setOutcome] = useState("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Cell | null>(null);
  const accept = (raw: unknown) => {
    const r = parseReport(raw);
    setReport(r);
    setError("");
    setSelected(null);
    setK(
      String(r.manifest.config.k >= 10 ? 10 : r.manifest.config.k >= 5 ? 5 : 1),
    );
    setProvider("all");
    setDomain("all");
    setType("all");
    setMembership("all");
    setOutcome("all");
    setSearch("");
  };
  useEffect(() => {
    let alive = true;
    loadDefaultReport()
      .then((raw) => {
        if (alive) accept(raw);
      })
      .catch((e) => {
        if (alive) setError(e.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);
  useEffect(
    () => setSelected(null),
    [provider, domain, type, membership, outcome, search, k],
  );
  const load = async (file: File | undefined) => {
    if (!file) return;
    try {
      if (file.size > 25 * 1024 * 1024)
        throw Error("Report exceeds the 25 MiB import limit.");
      accept(JSON.parse(await file.text()));
    } catch {
      setError(
        "Could not load this report. Choose a valid vessel.report.v1 JSON export (maximum 25 MiB).",
      );
    }
  };
  const cells = useMemo(
    () =>
      report?.cells.filter(
        (c) =>
          (provider === "all" || c.provider === provider) &&
          (domain === "all" || c.gold.domain === domain) &&
          (type === "all" || c.gold.visual_type === type) &&
          (membership === "all" || c.gold.attestation.bucket === membership) &&
          (outcome === "all" ||
            String(c.scores[k]?.full_support) === outcome) &&
          (search === "" ||
            `${c.gold.query} ${c.query_id}`
              .toLowerCase()
              .includes(search.toLowerCase())),
      ) ?? [],
    [report, provider, domain, type, membership, outcome, search, k],
  );
  const downloadUrl = useMemo(
    () =>
      report
        ? URL.createObjectURL(
            new Blob([JSON.stringify(report, null, 2)], {
              type: "application/json",
            }),
          )
        : undefined,
    [report],
  );
  useEffect(
    () => () => {
      if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    },
    [downloadUrl],
  );
  const filter = (
    label: string,
    value: string,
    set: (s: string) => void,
    values: string[],
  ) => (
    <label>
      {label}
      <select value={value} onChange={(e) => set(e.target.value)}>
        <option value="all">All {label.toLowerCase()}</option>
        {values.map((v) => (
          <option key={v} value={v}>
            {v.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
  const [breakdown, setBreakdown] = useState("domain");
  const demo = report?.manifest.mode === "replay";
  return (
    <>
      <header>
        <a className="wordmark" href="#">
          VESSEL<span>↗</span>
        </a>
        <span className="header-caption">
          VISUAL EVIDENCE / OPEN EVALUATION
        </span>
        <nav>
          <a href={`${repo}/blob/main/METHODOLOGY.md`}>Methodology ↗</a>
          <a href={repo}>GitHub ↗</a>
        </nav>
      </header>
      <main>
        <div className="eyebrow">
          <span className="dot" />
          {demo ? "OFFLINE DEMONSTRATION" : "EVIDENCE EXPLORER"}
        </div>
        <div className="hero">
          <div>
            <h1>
              Search finds documents.
              <br />
              <span>Where is the evidence?</span>
            </h1>
            <p>
              Inspect the distance between a retrieved page and a complete,
              source-grounded evidence bundle.
            </p>
          </div>
          <div className="import-controls">
            <label className="button secondary">
              Import report
              <input
                type="file"
                accept=".json,application/json"
                onChange={(e) => {
                  void load(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
            {report && (
              <a
                className="button"
                href={downloadUrl}
                download={`vessel-${report.manifest.run_id}.json`}
              >
                Download artifacts ↓
              </a>
            )}
          </div>
        </div>
        {loading && <p role="status">Loading evaluation artifacts…</p>}
        {error && (
          <div role="alert" className="error">
            {error}
          </div>
        )}
        {report && (
          <>
            <aside className={`notice ${demo ? "synthetic" : ""}`} role="note">
              <strong>
                {demo
                  ? "Synthetic software fixtures"
                  : report.manifest.publication_eligible
                    ? "Validated benchmark run"
                    : "Development run"}
              </strong>
              <span>
                {demo
                  ? "These values exercise the software. They do not measure provider performance."
                  : report.manifest.publication_eligible
                    ? "Reviewed gold and a complete recorded run."
                    : "Release gates have not been met. These results are not a validated Core-100 leaderboard."}
              </span>
            </aside>
            <section className="run-strip" aria-label="Run provenance">
              <div>
                <span>BENCHMARK</span>
                <strong>{report.manifest.benchmark_version}</strong>
              </div>
              <div>
                <span>PROTOCOL</span>
                <strong>
                  {report.manifest.config.protocol.replaceAll("_", " + ")}
                </strong>
              </div>
              <div>
                <span>RUN STATE</span>
                <strong>{report.manifest.status}</strong>
              </div>
              <div>
                <span>API REQUESTS</span>
                <strong>{report.manifest.requests}</strong>
              </div>
              <div>
                <span>RESERVED SPEND</span>
                <strong>${report.manifest.reserved_cost_usd.toFixed(2)}</strong>
              </div>
            </section>
            <section>
              <div className="section-heading">
                <div>
                  <div className="section-label">
                    01 / RETRIEVAL DIAGNOSTICS
                  </div>
                  <h2>{demo ? "Fixture outcomes" : "Recorded outcomes"}</h2>
                </div>
                <label className="k-select">
                  Result depth
                  <select
                    value={k}
                    onChange={(e) => {
                      setK(e.target.value);
                      setSelected(null);
                    }}
                  >
                    {Object.keys(Object.values(report.summary)[0] ?? {}).map(
                      (v) => (
                        <option key={v} value={v}>
                          Top {v}
                        </option>
                      ),
                    )}
                  </select>
                </label>
              </div>
              <div className="table-scroll">
                <table className="metrics">
                  <thead>
                    <tr>
                      <th>System {demo && "/ fixture"}</th>
                      <th>Document</th>
                      <th>Visual</th>
                      <th>Primary source</th>
                      <th>Location</th>
                      <th>Data</th>
                      <th className="highlight">Full Support@{k}</th>
                      <th>Failures / skips</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(report.summary).map(([name, values]) => {
                      const m = values[k];
                      return (
                        <tr key={name}>
                          <th>{displayName(name)}</th>
                          <td>{percent(m.components.document)}</td>
                          <td>{percent(m.components.visual)}</td>
                          <td>{percent(m.components.primary)}</td>
                          <td>{percent(m.components.localization)}</td>
                          <td>
                            {percent(m.data_recall)}
                            <small>n={m.data_denominator}</small>
                          </td>
                          <td className="highlight">
                            <strong>{percent(m.full_support)}</strong>
                            <small>
                              {m.full_support_ci95
                                ? `${percent(m.full_support_ci95[0])}–${percent(m.full_support_ci95[1])} CI`
                                : "Insufficient families for CI"}
                            </small>
                          </td>
                          <td>
                            {Object.entries(m.statuses)
                              .filter(([s]) => !["ok", "no_match"].includes(s))
                              .map(([s, n]) => `${s}: ${n}`)
                              .join(", ") || "0"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="footnote">
                Full Support requires the correct visual, source, location and
                applicable data in one bundle. Intervals resample evidence
                families. Protocols are reported separately.
              </p>
            </section>
            <details className="manifest">
              <summary>Breakdowns and paired comparisons</summary>
              <label>
                Breakdown dimension
                <select
                  value={breakdown}
                  onChange={(e) => setBreakdown(e.target.value)}
                >
                  {Object.keys(report.breakdowns).map((v) => (
                    <option key={v} value={v}>
                      {v.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </label>
              <p className="footnote">
                Breakdowns use the deepest recorded K (
                {report.manifest.config.k >= 10
                  ? 10
                  : report.manifest.config.k >= 5
                    ? 5
                    : 1}
                ).
              </p>
              <div className="table-scroll">
                <table className="metrics">
                  <thead>
                    <tr>
                      <th>Group</th>
                      <th>System</th>
                      <th>Queries</th>
                      <th>Full Support</th>
                      <th>MRR</th>
                      <th>Median ms</th>
                      <th>Reserved USD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(report.breakdowns[breakdown] ?? {}).flatMap(
                      ([group, systems]) =>
                        Object.entries(systems).map(([system, m]) => (
                          <tr key={`${group}-${system}`}>
                            <th>{group.replaceAll("_", " ")}</th>
                            <td>{displayName(system)}</td>
                            <td>{m.queries}</td>
                            <td>{percent(m.full_support)}</td>
                            <td>{m.mrr?.toFixed(3) ?? "—"}</td>
                            <td>{m.median_latency_ms?.toFixed(0) ?? "—"}</td>
                            <td>{m.reserved_cost_usd.toFixed(4)}</td>
                          </tr>
                        )),
                    )}
                  </tbody>
                </table>
              </div>
              <h3>Paired differences at K={k}</h3>
              {report.paired
                .filter((p) => String(p.k) === k)
                .map((p) => (
                  <p key={`${p.first}-${p.second}`}>
                    {displayName(p.first)} − {displayName(p.second)}:{" "}
                    {percent(p.difference)}{" "}
                    {p.ci95
                      ? `(${percent(p.ci95[0])} to ${percent(p.ci95[1])}; 95% family bootstrap interval)`
                      : "(insufficient families for interval)"}
                  </p>
                ))}
              {!report.paired.length && (
                <p>Paired comparisons require complete matching runs.</p>
              )}
              <h3>Supplemental recall at K={k}</h3>
              <p className="footnote">
                Rights, methodology and reproducibility use only independently
                annotated applicable records. They affect Full Support only when
                explicitly required by gold.
              </p>
              {Object.entries(report.summary).map(([system, values]) => (
                <p key={system}>
                  {displayName(system)}:{" "}
                  {Object.entries(values[k].supplemental ?? {})
                    .map(
                      ([name, m]) =>
                        `${name}: ${percent(m.recall)} (n=${m.denominator})`,
                    )
                    .join(" · ") || "Supplemental annotations unavailable"}
                </p>
              ))}
            </details>
            <section>
              <div className="section-heading">
                <div>
                  <div className="section-label">02 / QUERY-LEVEL AUDIT</div>
                  <h2>Every result has a paper trail.</h2>
                </div>
                <span className="count">{cells.length} result cells</span>
              </div>
              <div className="filters">
                <label className="search-label">
                  Search queries
                  <input
                    placeholder="Find a query or ID…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </label>
                {filter(
                  "Providers",
                  provider,
                  setProvider,
                  Object.keys(report.summary),
                )}
                {filter("Domains", domain, setDomain, [
                  ...new Set(report.cells.map((c) => c.gold.domain)),
                ])}
                {filter("Visual types", type, setType, [
                  ...new Set(report.cells.map((c) => c.gold.visual_type)),
                ])}
                {filter("Membership", membership, setMembership, [
                  ...new Set(
                    report.cells.map((c) => c.gold.attestation.bucket),
                  ),
                ])}
                <label>
                  Outcome
                  <select
                    value={outcome}
                    onChange={(e) => setOutcome(e.target.value)}
                  >
                    <option value="all">All outcomes</option>
                    <option value="true">Full support</option>
                    <option value="false">Incomplete support</option>
                  </select>
                </label>
              </div>
              <div className="query-list">
                {cells.slice(0, 200).map((c) => (
                  <button
                    className="query-row"
                    key={`${c.provider}-${c.query_id}`}
                    onClick={() => setSelected(c)}
                  >
                    <span className="query-id">
                      {c.query_id}
                      <small>{displayName(c.provider)}</small>
                    </span>
                    <span className="query-copy">
                      {c.gold.query}
                      <small>
                        {c.gold.domain} ·{" "}
                        {c.gold.visual_type.replaceAll("_", " ")} ·{" "}
                        {c.gold.attestation.bucket}
                      </small>
                    </span>
                    <span
                      className={
                        c.scores[k].full_support ? "badge success" : "badge"
                      }
                    >
                      {c.scores[k].full_support
                        ? "Full support"
                        : c.scores[k].failure?.replaceAll("_", " ") ||
                          c.response.status}
                    </span>
                    <span className="arrow">↗</span>
                  </button>
                ))}
              </div>
              {cells.length === 0 && (
                <p className="empty">
                  No results match these filters. Adjust the filters or search
                  text.
                </p>
              )}
              {cells.length > 200 && (
                <p className="footnote">
                  Showing the first 200 cells. Narrow the filters to inspect
                  more.
                </p>
              )}
              {selected && (
                <Inspector
                  cell={selected}
                  k={k}
                  onClose={() => setSelected(null)}
                />
              )}
            </section>
            <details className="manifest">
              <summary>Reproducibility manifest</summary>
              <dl>
                <dt>Dataset SHA-256</dt>
                <dd>{report.manifest.dataset_sha256}</dd>
                <dt>Code SHA-256</dt>
                <dd>{report.manifest.code_sha256}</dd>
                <dt>Configuration SHA-256</dt>
                <dd>{report.manifest.config_sha256}</dd>
              </dl>
              <pre>{JSON.stringify(report.manifest, null, 2)}</pre>
            </details>
          </>
        )}
      </main>
      <footer>
        <span>
          VESSEL / An independent benchmark for visual evidence retrieval.
        </span>
        <a href={`${repo}/blob/main/docs/providers/TEMPLATE.md`}>
          Provider characterization ↗
        </a>
      </footer>
    </>
  );
}
