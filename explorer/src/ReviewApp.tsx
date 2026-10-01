import { useEffect, useState } from "react";
import type { Alternative, Draft, Identity, Task, Workspace } from "./review";
import {
  blankAlternative,
  blankIdentity,
  checks,
  cleanDraft,
  domains,
  downloadReview,
  lines,
  reviewRequest,
  safeSource,
  samePerson,
  statusNames,
} from "./review";
import "./review.css";

function Field({
  label,
  value,
  onChange,
  hint,
  multiline = false,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  hint?: string;
  multiline?: boolean;
  type?: string;
}) {
  return (
    <label className="review-field">
      <span>{label}</span>
      {multiline ? (
        <textarea
          aria-label={label}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
        />
      ) : (
        <input
          aria-label={label}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
      {hint && <small>{hint}</small>}
    </label>
  );
}
function Source({ url, label }: { url?: string; label: string }) {
  const safe = safeSource(url);
  return safe ? (
    <a className="source-link" href={safe} target="_blank" rel="noreferrer">
      {label} ↗
    </a>
  ) : (
    <span className="muted">{label}: not recorded</span>
  );
}
function Evidence({ alternative: a }: { alternative: Alternative }) {
  const [preview, setPreview] = useState(false);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    setPreview(false);
    setFailed(false);
  }, [a.evidence_id, a.visual.urls.join()]);
  const visual = safeSource(a.visual.urls[0]);
  const document = safeSource(a.document.urls[0]);
  const pdf =
    document && new URL(document).pathname.toLowerCase().endsWith(".pdf");
  return (
    <section className="evidence-card">
      <div className="section-label">PRIMARY EVIDENCE</div>
      <h3>{a.evidence_id || "Answer identity not recorded"}</h3>
      <div className="review-links">
        <Source url={document} label="Original document" />
        <Source url={visual} label="Exact visual" />
      </div>
      <p>
        {a.original_required
          ? "Publisher-original visual required"
          : "Derived visuals may satisfy this task"}
      </p>
      {a.version && <p>Version: {a.version}</p>}
      {a.locations.map((l, i) => (
        <p key={i} className="locator">
          {l.figure && `Figure ${l.figure} · `}
          {l.page_index !== null &&
            `PDF page ${l.page_index + 1} (index ${l.page_index}) · `}
          {l.page_label && `Printed label ${l.page_label} · `}
          {l.locator}
        </p>
      ))}
      <p className="verification-note">
        {a.verification_notes ||
          "Primary-source verification notes have not been added."}
      </p>
      {(visual || pdf) && (
        <button
          className="review-secondary"
          onClick={() => setPreview(!preview)}
        >
          {preview ? "Hide preview" : "Show source preview"}
        </button>
      )}
      {preview &&
        (pdf ? (
          <>
            <iframe
              title="Primary document preview"
              sandbox="allow-same-origin"
              src={`${document?.split("#")[0]}#page=${(a.locations[0]?.page_index ?? 0) + 1}`}
            />
            <small>
              If the publisher blocks embedding, open the original document
              above.
            </small>
          </>
        ) : failed ? (
          <p role="status">
            This visual cannot be previewed here. Open the exact visual above.
          </p>
        ) : (
          <img
            src={visual}
            alt={`Primary evidence ${a.evidence_id}`}
            onError={() => setFailed(true)}
          />
        ))}
      <h4>Required for success</h4>
      <div className="review-tags">
        {a.required.map((r) => (
          <span key={r}>{r}</span>
        ))}
      </div>
      <h4>Underlying data</h4>
      <p>
        {a.data_available
          ? "Recorded as available — verify against the publisher."
          : "Availability not verified; do not assume a dataset exists."}
      </p>
      {a.datasets
        .flatMap((d) => d.urls)
        .map((u) => (
          <p key={u}>
            <Source url={u} label="Dataset" />
          </p>
        ))}
      <details>
        <summary>Verified identities & source references</summary>
        <pre>
          {JSON.stringify(
            {
              document: a.document,
              visual: a.visual,
              verification_urls: a.verification_urls,
              locations: a.locations,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </section>
  );
}

export default function ReviewApp() {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [selectedId, setSelectedId] = useState(
    () => localStorage.getItem("vessel-review-selected") ?? "",
  );
  const [draft, setDraft] = useState<Draft | null>(null);
  const [dirty, setDirty] = useState(false);
  const [name, setName] = useState(
    () => localStorage.getItem("vessel-reviewer-name") ?? "",
  );
  const [role, setRole] = useState(() =>
    localStorage.getItem("vessel-review-role") === "independent"
      ? "independent"
      : "author",
  );
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [step, setStep] = useState("evidence");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [selectedChecks, setSelectedChecks] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const [human, setHuman] = useState(false);
  const task = workspace?.tasks.find((t) => t.record.query_id === selectedId);
  const canEdit = !!task && role === "author" && samePerson(name, task.author);
  const matchesRole =
    !!task &&
    (role === "author"
      ? samePerson(name, task.author)
      : !samePerson(name, task.author));
  const decisionAllowed =
    matchesRole && (role === "author" || task?.status !== "draft");

  const accept = (w: Workspace, id = selectedId) => {
    setWorkspace(w);
    const t = w.tasks.find((t) => t.record.query_id === id);
    setSelectedId(t?.record.query_id ?? "");
    setDraft(t ? structuredClone(t.record) : null);
    setDirty(false);
    setSelectedChecks([]);
    setNotes("");
    setHuman(false);
  };
  useEffect(() => {
    document.title = "VESSEL · Human review";
    reviewRequest<Workspace>("workspace")
      .then((w) => accept(w, selectedId))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    localStorage.setItem("vessel-reviewer-name", name);
  }, [name]);
  useEffect(() => {
    localStorage.setItem("vessel-review-role", role);
  }, [role]);
  useEffect(() => {
    localStorage.setItem("vessel-review-selected", selectedId);
  }, [selectedId]);
  useEffect(() => {
    const guard = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);
  useEffect(() => {
    setSelectedChecks([]);
    setNotes("");
    setHuman(false);
  }, [name, role, selectedId]);
  const execute = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save.");
    } finally {
      setBusy(false);
    }
  };
  const discard = () =>
    !dirty ||
    confirm("Discard unsaved changes? Save your draft first to keep them.");
  const choose = (t: Task) => {
    if (!discard()) return;
    accept(workspace!, t.record.query_id);
    setStep("evidence");
    setError("");
    setNotice("");
  };
  const update = (patch: Partial<Draft>) => {
    if (draft) {
      setDraft({ ...draft, ...patch });
      setDirty(true);
    }
  };
  const updateAlternative = (index: number, patch: Partial<Alternative>) => {
    if (draft)
      update({
        alternatives: draft.alternatives.map((a, i) =>
          i === index ? { ...a, ...patch } : a,
        ),
      });
  };
  const create = () =>
    execute(async () => {
      if (!discard()) return;
      const w = await reviewRequest<Workspace>("create", { reviewer: name });
      const id = w.tasks.at(-1)!.record.query_id;
      accept(w, id);
      setStep("evidence");
      setNotice(
        "New draft created. Start with a clear question and its primary evidence.",
      );
    });
  const save = () =>
    execute(async () => {
      const w = await reviewRequest<Workspace>("save", {
        reviewer: name,
        task_id: selectedId,
        revision: task?.revision,
        record: draft ? cleanDraft(draft) : null,
      });
      accept(w);
      setNotice(
        "Draft saved on this computer. Any changed content needs fresh approvals.",
      );
    });
  const decide = (decision: string) =>
    execute(async () => {
      if (dirty) throw Error("Save your draft before recording a decision.");
      const w = await reviewRequest<Workspace>("decision", {
        task_id: selectedId,
        revision: task?.revision,
        reviewer: name,
        role,
        decision,
        notes,
        checks: selectedChecks,
        human_attestation: human,
      });
      accept(w);
      setStep("decision");
      setNotice(
        decision === "approved"
          ? role === "author"
            ? "Author approval recorded. Export a packet for a different human to review."
            : "Independent approval recorded for this exact version."
          : "Requested changes recorded. The author can revise the task and resubmit it.",
      );
    });
  const importFile = (file: File | undefined) =>
    execute(async () => {
      if (!file || !discard()) return;
      if (file.size > 5 * 1024 * 1024)
        throw Error("Choose a review packet smaller than 5 MiB.");
      const packet = JSON.parse(await file.text());
      const w = await reviewRequest<Workspace>("import", {
        packet,
        version: workspace?.version,
      });
      accept(w, "");
      setNotice("Review packet imported. Existing work was preserved.");
    });
  const exportFile = (kind: "packet" | "dataset") =>
    execute(async () => {
      if (dirty) throw Error("Save your draft before exporting.");
      const file = await downloadReview(kind);
      setNotice(
        (kind === "packet"
          ? "Review packet saved. Send a copy to your second reviewer; they can import it into their local workspace."
          : "Reviewed gold saved. Only tasks with current approvals were included; Core-100 release validation is a separate gate.") +
          "\nFile: " +
          file,
      );
    });
  const visibleTasks =
    workspace?.tasks.filter(
      (t) =>
        (filter === "all" || t.status === filter) &&
        `${t.record.query} ${t.record.query_id} ${t.record.domain}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    ) ?? [];
  return (
    <div className="review-app">
      <header>
        <a className="wordmark" href="/">
          VESSEL<span>↗</span>
        </a>
        <span className="header-caption">HUMAN REVIEW</span>
        <nav>
          <a href="/">Results explorer</a>
          <a
            href="https://github.com/richardsondx/VESSEL/blob/main/docs/ANNOTATION_GUIDE.md"
            target="_blank"
            rel="noreferrer"
          >
            Review guide ↗
          </a>
        </nav>
      </header>
      <main className="review-main">
        <div className="review-title">
          <div>
            <div className="eyebrow">
              <span className="dot" /> PRIVATE WORKSPACE
            </div>
            <h1>
              Make the evidence
              <br />
              <span>worth measuring.</span>
            </h1>
            <p>
              Verify the source. Define a fair answer. Get a second pair of
              eyes.
            </p>
          </div>
          <div className="review-transfer">
            <label className="review-secondary">
              Import review packet
              <input
                type="file"
                accept=".json"
                disabled={busy || !workspace}
                onChange={(e) => {
                  void importFile(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
            <button
              className="review-secondary"
              disabled={busy || !workspace?.tasks.length}
              onClick={() => void exportFile("packet")}
            >
              Export review packet ↗
            </button>
            <button
              className="review-primary"
              disabled={
                busy || !workspace?.tasks.some((t) => t.status === "approved")
              }
              onClick={() => void exportFile("dataset")}
            >
              Export reviewed gold
            </button>
          </div>
        </div>
        <div className="review-context">
          <p>
            <strong>Saved on this computer.</strong> Export a packet to transfer
            it to another reviewer. Reviewer names record human attestations;
            this local workspace has no verified sign-in.
          </p>
          <div className="review-person">
            <Field label="Your reviewer name" value={name} onChange={setName} />
            <label className="review-field">
              <span>Working as</span>
              <select
                value={role}
                onChange={(e) => {
                  if (discard()) {
                    setRole(e.target.value);
                    if (task) accept(workspace!, selectedId);
                  }
                }}
              >
                <option value="author">Task author</option>
                <option value="independent">Independent reviewer</option>
              </select>
            </label>
          </div>
        </div>
        {role === "independent" && (
          <aside className="blind-notice">
            Independent review: inspect the primary evidence and proposed
            answers. Provider names, rankings and scores are excluded from this
            workspace.
          </aside>
        )}
        {error && (
          <div className="review-error" role="alert">
            {error}
            <button
              onClick={() =>
                execute(async () => {
                  if (!discard()) return;
                  accept(await reviewRequest<Workspace>("workspace"));
                })
              }
            >
              Reload workspace
            </button>
          </div>
        )}
        {notice && (
          <p className="review-notice" role="status">
            {notice}
          </p>
        )}
        {!workspace && !error && (
          <p role="status">Loading your review workspace…</p>
        )}
        {workspace && (
          <>
            <div className="review-progress" aria-label="Review progress">
              {Object.entries(statusNames).map(([status, label]) => (
                <button
                  key={status}
                  className={filter === status ? "active" : ""}
                  onClick={() => setFilter(filter === status ? "all" : status)}
                >
                  <strong>
                    {workspace.tasks.filter((t) => t.status === status).length}
                  </strong>
                  <span>{label}</span>
                </button>
              ))}
            </div>
            <div className="review-layout">
              <aside className="review-queue">
                <div className="queue-heading">
                  <h2>
                    Task inbox <span>{workspace.tasks.length}</span>
                  </h2>
                  <button
                    disabled={busy || !name.trim() || role !== "author"}
                    onClick={() => void create()}
                  >
                    + New task
                  </button>
                </div>
                <input
                  aria-label="Search review tasks"
                  placeholder="Search question, ID or domain"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <label className="review-field">
                  <span>Status</span>
                  <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  >
                    <option value="all">All tasks</option>
                    {Object.entries(statusNames).map(([v, label]) => (
                      <option key={v} value={v}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="queue-list">
                  {visibleTasks.map((t) => (
                    <button
                      key={t.record.query_id}
                      className={`queue-task ${t.record.query_id === selectedId ? "selected" : ""}`}
                      onClick={() => choose(t)}
                    >
                      <span className={`review-status ${t.status}`}>
                        {statusNames[t.status]}
                      </span>
                      <strong>
                        {t.record.query || "Untitled evidence task"}
                      </strong>
                      <small>
                        {t.record.domain} · {t.record.query_id}
                      </small>
                    </button>
                  ))}
                </div>
                {!visibleTasks.length && (
                  <p className="muted">
                    {workspace.tasks.length
                      ? "No tasks match these filters."
                      : "Your first task starts here. Enter your name, then choose New task."}
                  </p>
                )}
              </aside>
              <section className="review-detail">
                {!task || !draft ? (
                  <div className="review-empty">
                    <span className="empty-icon">◎</span>
                    <h2>
                      A reliable benchmark starts
                      <br />
                      with a verified answer.
                    </h2>
                    <p>
                      Create a task from a primary publisher's evidence, or
                      import a packet from its author.
                    </p>
                    <ol>
                      <li>Write a specific information need.</li>
                      <li>
                        Identify its evidence and acceptable alternatives.
                      </li>
                      <li>Verify it independently before scoring.</li>
                    </ol>
                    <p className="muted">
                      The workspace starts empty. Discovery results and
                      synthetic demo scores are not pre-approved gold.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="task-heading">
                      <div>
                        <span className={`review-status ${task.status}`}>
                          {statusNames[task.status]}
                        </span>
                        <h2>{draft.query || "Untitled evidence task"}</h2>
                        <p>
                          {draft.query_id} · Author: {task.author} · Revision{" "}
                          {task.revision}
                          {draft.synthetic && " · SYNTHETIC PRACTICE RECORD"}
                        </p>
                      </div>
                      {canEdit && (
                        <button
                          className="review-primary"
                          disabled={busy || !dirty}
                          onClick={() => void save()}
                        >
                          {busy ? "Saving…" : "Save draft"}
                        </button>
                      )}
                    </div>
                    {dirty && (
                      <p className="unsaved" role="status">
                        Unsaved changes — save before switching tasks, reviewing
                        or exporting.
                      </p>
                    )}
                    <div className="review-steps">
                      <button
                        className={step === "evidence" ? "active" : ""}
                        onClick={() => setStep("evidence")}
                      >
                        1 · Task & evidence
                      </button>
                      <button
                        className={step === "decision" ? "active" : ""}
                        onClick={() => setStep("decision")}
                      >
                        2 · Decision & history
                      </button>
                    </div>
                    {step === "evidence" ? (
                      <>
                        {canEdit ? (
                          <>
                            <section className="review-panel">
                              <h3>The information need</h3>
                              <Field
                                label="Question"
                                value={draft.query}
                                onChange={(v) => update({ query: v })}
                                multiline
                                hint="Include the measure, population, period or experiment needed to distinguish valid answers. Avoid copying a figure caption."
                              />
                              <div className="review-form-grid">
                                <label className="review-field">
                                  <span>Domain</span>
                                  <select
                                    value={draft.domain}
                                    onChange={(e) =>
                                      update({ domain: e.target.value })
                                    }
                                  >
                                    {domains.map((d) => (
                                      <option key={d}>{d}</option>
                                    ))}
                                  </select>
                                </label>
                                <label className="review-field">
                                  <span>Visual type</span>
                                  <select
                                    value={draft.visual_type}
                                    onChange={(e) =>
                                      update({ visual_type: e.target.value })
                                    }
                                  >
                                    {[
                                      "chart",
                                      "table",
                                      "map",
                                      "multi_panel",
                                      "diagram",
                                      "other",
                                    ].map((v) => (
                                      <option key={v} value={v}>
                                        {v.replace("_", " ")}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                                <Field
                                  label="Evidence family"
                                  value={draft.family_id}
                                  onChange={(v) => update({ family_id: v })}
                                  hint="Related questions stay in one family and split."
                                />
                                <Field
                                  label="Question style"
                                  value={draft.query_type}
                                  onChange={(v) => update({ query_type: v })}
                                  hint="For example: descriptive, comparative, temporal."
                                />
                              </div>
                              <label className="review-field">
                                <span>Dataset split</span>
                                <select
                                  value={draft.split}
                                  onChange={(e) =>
                                    update({ split: e.target.value })
                                  }
                                >
                                  <option value="development">
                                    Development / pilot
                                  </option>
                                  <option value="evaluation">
                                    Frozen evaluation
                                  </option>
                                </select>
                              </label>
                            </section>
                            {draft.alternatives.map((a, i) => (
                              <section className="review-panel" key={i}>
                                <div className="alternative-heading">
                                  <h3>Acceptable answer {i + 1}</h3>
                                  <button
                                    className="review-secondary"
                                    onClick={() =>
                                      update({
                                        alternatives: draft.alternatives.filter(
                                          (_, j) => j !== i,
                                        ),
                                      })
                                    }
                                  >
                                    Remove answer
                                  </button>
                                </div>
                                <Field
                                  label="Evidence identity"
                                  value={a.evidence_id}
                                  onChange={(v) =>
                                    updateAlternative(i, { evidence_id: v })
                                  }
                                  hint="A stable VESSEL ID for this evidence object."
                                />
                                <div className="review-form-grid">
                                  <Field
                                    label="Original document URLs"
                                    value={a.document.urls.join("\n")}
                                    onChange={(v) =>
                                      updateAlternative(i, {
                                        document: {
                                          ...a.document,
                                          urls: lines(v),
                                        },
                                      })
                                    }
                                    multiline
                                    hint="Canonical publisher URLs; one verified alias per line."
                                  />
                                  <Field
                                    label="Exact visual URLs"
                                    value={a.visual.urls.join("\n")}
                                    onChange={(v) =>
                                      updateAlternative(i, {
                                        visual: { ...a.visual, urls: lines(v) },
                                      })
                                    }
                                    multiline
                                    hint="Identify the visual itself. A document page alone is not an asset identity."
                                  />
                                  <Field
                                    label="Verified primary-source URLs"
                                    value={a.authoritative_urls.join("\n")}
                                    onChange={(v) =>
                                      updateAlternative(i, {
                                        authoritative_urls: lines(v),
                                      })
                                    }
                                    multiline
                                  />
                                  <Field
                                    label="Version / vintage"
                                    value={a.version ?? ""}
                                    onChange={(v) =>
                                      updateAlternative(i, {
                                        version: v || null,
                                      })
                                    }
                                  />
                                </div>
                                <LocationFields
                                  alternative={a}
                                  change={(patch) =>
                                    updateAlternative(i, patch)
                                  }
                                />
                                <label className="review-check">
                                  <input
                                    type="checkbox"
                                    checked={a.original_required}
                                    onChange={(e) =>
                                      updateAlternative(i, {
                                        original_required: e.target.checked,
                                      })
                                    }
                                  />
                                  <span>
                                    Require the publisher's original visual.
                                    Matching data alone does not qualify a
                                    generated chart.
                                  </span>
                                </label>
                                <h4>What must one result bundle provide?</h4>
                                <div className="requirement-options">
                                  {[
                                    "document",
                                    "visual",
                                    "primary",
                                    "localization",
                                    "data",
                                    "version",
                                    "rights",
                                    "methodology",
                                    "reproducibility",
                                  ].map((c) => (
                                    <label key={c}>
                                      <input
                                        type="checkbox"
                                        checked={a.required.includes(c)}
                                        disabled={c === "document"}
                                        onChange={(e) =>
                                          updateAlternative(i, {
                                            required: e.target.checked
                                              ? [...a.required, c]
                                              : a.required.filter(
                                                  (v) => v !== c,
                                                ),
                                          })
                                        }
                                      />
                                      {c}
                                    </label>
                                  ))}
                                </div>
                                <label className="review-check">
                                  <input
                                    type="checkbox"
                                    checked={a.data_available}
                                    onChange={(e) =>
                                      updateAlternative(i, {
                                        data_available: e.target.checked,
                                      })
                                    }
                                  />
                                  <span>
                                    I verified that relevant underlying data is
                                    offered by the publisher.
                                  </span>
                                </label>
                                <Field
                                  label="Underlying dataset URLs"
                                  value={a.datasets
                                    .flatMap((d) => d.urls)
                                    .join("\n")}
                                  onChange={(v) =>
                                    updateAlternative(i, {
                                      datasets: lines(v).map((url) => ({
                                        ...blankIdentity(),
                                        urls: [url],
                                      })),
                                    })
                                  }
                                  multiline
                                  hint="Do not substitute extracted or approximated chart values for publisher data."
                                />
                                <Field
                                  label="Primary-source verification references"
                                  value={a.verification_urls.join("\n")}
                                  onChange={(v) =>
                                    updateAlternative(i, {
                                      verification_urls: lines(v),
                                    })
                                  }
                                  multiline
                                />
                                <Field
                                  label="Verification notes and alternative-answer rationale"
                                  value={a.verification_notes}
                                  onChange={(v) =>
                                    updateAlternative(i, {
                                      verification_notes: v,
                                    })
                                  }
                                  multiline
                                  hint="Explain what you inspected, why this answer satisfies the question, and what remains uncertain."
                                />
                                <details>
                                  <summary>
                                    Hashes, identifiers and additional
                                    requirements
                                  </summary>
                                  <div className="review-form-grid">
                                    {(["document", "visual"] as const).map(
                                      (kind) => (
                                        <IdentityFields
                                          key={kind}
                                          label={kind}
                                          value={a[kind]}
                                          change={(v) =>
                                            updateAlternative(i, { [kind]: v })
                                          }
                                        />
                                      ),
                                    )}
                                    <Field
                                      label="Accepted rights statements"
                                      value={a.accepted_rights.join("\n")}
                                      onChange={(v) =>
                                        updateAlternative(i, {
                                          accepted_rights: lines(v),
                                        })
                                      }
                                      multiline
                                    />
                                    <Field
                                      label="Methodology URLs"
                                      value={a.methodology.urls.join("\n")}
                                      onChange={(v) =>
                                        updateAlternative(i, {
                                          methodology: {
                                            ...a.methodology,
                                            urls: lines(v),
                                          },
                                        })
                                      }
                                      multiline
                                    />
                                    <Field
                                      label="Reproducibility URLs"
                                      value={a.reproducibility.urls.join("\n")}
                                      onChange={(v) =>
                                        updateAlternative(i, {
                                          reproducibility: {
                                            ...a.reproducibility,
                                            urls: lines(v),
                                          },
                                        })
                                      }
                                      multiline
                                    />
                                  </div>
                                </details>
                              </section>
                            ))}
                            <button
                              className="review-secondary add-answer"
                              onClick={() =>
                                update({
                                  alternatives: [
                                    ...draft.alternatives,
                                    blankAlternative(
                                      `${draft.query_id}-answer-${crypto.randomUUID().slice(0, 8)}`,
                                    ),
                                  ],
                                })
                              }
                            >
                              + Add acceptable answer
                            </button>
                            <details
                              className="review-panel"
                              open={draft.split === "evaluation"}
                            >
                              <summary>Index freeze & membership</summary>
                              <p>
                                New evaluation queries must follow a preserved
                                index freeze. A registry snapshot alone does not
                                prove non-ingestion.
                              </p>
                              <div className="review-form-grid">
                                <Field
                                  label="Index version"
                                  value={draft.attestation.index_version ?? ""}
                                  onChange={(v) =>
                                    update({
                                      attestation: {
                                        ...draft.attestation,
                                        index_version: v || null,
                                      },
                                    })
                                  }
                                />
                                <Field
                                  label="Freeze timestamp (UTC)"
                                  value={draft.attestation.frozen_at ?? ""}
                                  onChange={(v) =>
                                    update({
                                      attestation: {
                                        ...draft.attestation,
                                        frozen_at: v || null,
                                      },
                                    })
                                  }
                                  hint="ISO timestamp, for example 2026-10-01T12:00:00Z. Must precede task creation."
                                />
                                <Field
                                  label="Preserved freeze / membership evidence reference"
                                  value={
                                    draft.attestation.evidence_reference ?? ""
                                  }
                                  onChange={(v) =>
                                    update({
                                      attestation: {
                                        ...draft.attestation,
                                        evidence_reference: v || null,
                                      },
                                    })
                                  }
                                />
                                <label className="review-field">
                                  <span>Verified membership</span>
                                  <select
                                    value={draft.attestation.bucket}
                                    onChange={(e) =>
                                      update({
                                        attestation: {
                                          ...draft.attestation,
                                          bucket: e.target.value,
                                        },
                                      })
                                    }
                                  >
                                    {[
                                      "unknown",
                                      "indexed",
                                      "known_unindexed",
                                      "external_holdout",
                                    ].map((v) => (
                                      <option key={v} value={v}>
                                        {v.replaceAll("_", " ")}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                              </div>
                              <p className="muted">
                                Query created:{" "}
                                {new Date(draft.created_at).toISOString()}
                              </p>
                            </details>
                            <div className="review-bottom-actions">
                              <button
                                className="review-primary"
                                disabled={busy || !dirty}
                                onClick={() => void save()}
                              >
                                Save draft
                              </button>
                              <button
                                className="review-secondary"
                                onClick={() => setStep("decision")}
                              >
                                Continue to review →
                              </button>
                            </div>
                          </>
                        ) : (
                          <section className="review-panel">
                            <h3>Proposed task</h3>
                            <p>{draft.query || "No question recorded."}</p>
                            <p className="muted">
                              {draft.domain} · {draft.visual_type} ·{" "}
                              {draft.split} · Family:{" "}
                              {draft.family_id || "not recorded"}
                            </p>
                            <p>
                              Index membership:{" "}
                              {draft.attestation.bucket.replaceAll("_", " ")}
                            </p>
                            {role === "author" && (
                              <p>
                                Enter the task author's name to edit. Otherwise
                                switch to independent review.
                              </p>
                            )}
                          </section>
                        )}
                        <div className="evidence-grid">
                          {draft.alternatives.map((a, i) => (
                            <Evidence key={i} alternative={a} />
                          ))}
                        </div>
                        {!draft.alternatives.length && (
                          <p className="review-panel">
                            No acceptable evidence has been recorded yet.
                          </p>
                        )}
                        {!canEdit && (
                          <button
                            className="review-primary"
                            onClick={() => setStep("decision")}
                          >
                            Review this task →
                          </button>
                        )}
                      </>
                    ) : (
                      <div className="review-decision-layout">
                        <div className="decision-sources">
                          {draft.alternatives.map((a, i) => (
                            <Evidence key={i} alternative={a} />
                          ))}
                        </div>
                        <section className="review-panel decision-panel">
                          <h3>
                            {role === "author"
                              ? "Verify before sending for review"
                              : "Your independent decision"}
                          </h3>
                          <p>
                            Open the primary sources and inspect the evidence
                            yourself. These checks apply to every acceptable
                            answer.
                          </p>
                          {task.issues.length > 0 && (
                            <details className="readiness" open>
                              <summary>
                                Needs attention before approval (
                                {task.issues.length})
                              </summary>
                              <ul>
                                {task.issues.map((issue, i) => (
                                  <li key={i}>{issue}</li>
                                ))}
                              </ul>
                            </details>
                          )}
                          {!matchesRole && (
                            <p className="readiness">
                              {role === "independent"
                                ? "A different person must independently review this task. Enter that reviewer’s name."
                                : "Only the named task author can give author approval."}
                            </p>
                          )}
                          {role === "independent" &&
                            task.status === "draft" && (
                              <p className="readiness">
                                This version needs author approval before
                                independent review.
                              </p>
                            )}
                          <fieldset disabled={busy}>
                            <legend>Evidence checks</legend>
                            {checks.map(([key, label]) => (
                              <label className="review-check" key={key}>
                                <input
                                  type="checkbox"
                                  checked={selectedChecks.includes(key)}
                                  onChange={(e) =>
                                    setSelectedChecks(
                                      e.target.checked
                                        ? [...selectedChecks, key]
                                        : selectedChecks.filter(
                                            (v) => v !== key,
                                          ),
                                    )
                                  }
                                />
                                <span>{label}</span>
                              </label>
                            ))}
                          </fieldset>
                          <Field
                            label="Review notes / requested changes"
                            value={notes}
                            onChange={setNotes}
                            multiline
                            hint="Cite what you checked. For changes, identify the field or evidence that needs correction."
                          />
                          <label className="review-check human-check">
                            <input
                              type="checkbox"
                              checked={human}
                              onChange={(e) => setHuman(e.target.checked)}
                            />
                            <span>
                              I am {name.trim() || "the named reviewer"}, and I
                              personally made this decision after reviewing the
                              task.
                            </span>
                          </label>
                          <div className="review-bottom-actions">
                            <button
                              className="review-primary"
                              disabled={
                                busy ||
                                dirty ||
                                !decisionAllowed ||
                                !human ||
                                !notes.trim() ||
                                !name.trim() ||
                                selectedChecks.length !== checks.length ||
                                task.issues.length > 0
                              }
                              onClick={() => void decide("approved")}
                            >
                              {role === "author"
                                ? "Approve & send for second review"
                                : "Approve this version"}
                            </button>
                            <button
                              className="review-secondary"
                              disabled={
                                busy ||
                                dirty ||
                                !decisionAllowed ||
                                !human ||
                                !notes.trim() ||
                                !name.trim()
                              }
                              onClick={() => void decide("changes_requested")}
                            >
                              Request changes
                            </button>
                          </div>
                          <p className="muted">
                            Approvals apply to this exact content. Editing any
                            evidence or requirement makes earlier approvals
                            stale.
                          </p>
                          <h3 className="history-title">
                            Decision & revision history
                          </h3>
                          <p className="muted">
                            Past decisions remain visible here. The inbox status
                            reflects current approvals.
                          </p>
                          {!task.history.length && (
                            <p>No decisions recorded yet.</p>
                          )}
                          <ol className="review-history">
                            {[...task.history].reverse().map((event, i) => (
                              <li key={i}>
                                <strong>
                                  {event.kind.replaceAll("_", " ")}
                                </strong>
                                <span>
                                  {event.reviewer} ·{" "}
                                  {new Date(event.at).toLocaleString()}
                                </span>
                                {event.note && <p>{event.note}</p>}
                                <small>
                                  Content {event.content_sha256.slice(0, 12)}
                                </small>
                              </li>
                            ))}
                          </ol>
                          <details>
                            <summary>
                              Previous content versions (
                              {task.previous_versions.length})
                            </summary>
                            {task.previous_versions.map((r, i) => (
                              <details key={i}>
                                <summary>
                                  Revision snapshot {i + 1}:{" "}
                                  {r.query || "Untitled"}
                                </summary>
                                <pre>{JSON.stringify(r, null, 2)}</pre>
                                {canEdit && (
                                  <button
                                    className="review-secondary"
                                    disabled={
                                      busy ||
                                      JSON.stringify({ ...r, reviews: [] }) ===
                                        JSON.stringify({
                                          ...task.record,
                                          reviews: [],
                                        })
                                    }
                                    onClick={() =>
                                      void execute(async () => {
                                        if (!discard()) return;
                                        const w =
                                          await reviewRequest<Workspace>(
                                            "save",
                                            {
                                              reviewer: name,
                                              task_id: selectedId,
                                              revision: task.revision,
                                              record: r,
                                            },
                                          );
                                        accept(w);
                                        setStep("evidence");
                                        setNotice(
                                          "Earlier content restored as a draft. Verify it and obtain fresh approvals before scoring.",
                                        );
                                      })
                                    }
                                  >
                                    Restore as a new draft
                                  </button>
                                )}
                              </details>
                            ))}
                          </details>
                        </section>
                      </div>
                    )}
                  </>
                )}
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function IdentityFields({
  label,
  value,
  change,
}: {
  label: string;
  value: Identity;
  change: (v: Identity) => void;
}) {
  return (
    <div>
      <Field
        label={`${label} SHA-256 hashes`}
        value={value.sha256.join("\n")}
        onChange={(v) => change({ ...value, sha256: lines(v) })}
        multiline
        hint="Computed file hashes, one per line; not unverified provider assertions."
      />
      <Field
        label={`${label} stable IDs`}
        value={value.ids.join("\n")}
        onChange={(v) => change({ ...value, ids: lines(v) })}
        multiline
      />
    </div>
  );
}
function LocationFields({
  alternative,
  change,
}: {
  alternative: Alternative;
  change: (v: Partial<Alternative>) => void;
}) {
  const l = alternative.locations[0] ?? {
    page_index: null,
    page_label: null,
    figure: null,
    bbox: null,
    locator: null,
  };
  const set = (patch: Partial<typeof l>) =>
    change({
      locations: [{ ...l, ...patch }, ...alternative.locations.slice(1)],
    });
  return (
    <>
      <h4>Where is the evidence?</h4>
      <div className="review-form-grid">
        <Field
          label="Figure / table identifier"
          value={l.figure ?? ""}
          onChange={(v) => set({ figure: v || null })}
        />
        <Field
          label="Stable web locator"
          value={l.locator ?? ""}
          onChange={(v) => set({ locator: v || null })}
          hint="For example: page anchor or a precise chart identifier."
        />
        <Field
          label="PDF page index (starts at 0)"
          value={l.page_index === null ? "" : String(l.page_index)}
          type="number"
          onChange={(v) => set({ page_index: v === "" ? null : Number(v) })}
          hint="The first PDF page has index 0. This is separate from the printed label."
        />
        <Field
          label="Printed page label"
          value={l.page_label ?? ""}
          onChange={(v) => set({ page_label: v || null })}
        />
      </div>
    </>
  );
}
