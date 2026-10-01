export type Identity = { urls: string[]; sha256: string[]; ids: string[] };
export type Location = {
  page_index: number | null;
  page_label: string | null;
  figure: string | null;
  bbox: number[] | null;
  locator: string | null;
};
export type Alternative = {
  evidence_id: string;
  document: Identity;
  visual: Identity;
  authoritative_urls: string[];
  locations: Location[];
  datasets: Identity[];
  data_available: boolean;
  original_required: boolean;
  version: string | null;
  accepted_rights: string[];
  methodology: Identity;
  reproducibility: Identity;
  required: string[];
  verification_urls: string[];
  verification_notes: string;
};
export type Review = {
  reviewer: string;
  role: string;
  decision: string;
  reviewed_at: string;
  notes: string;
  content_sha256: string;
};
export type Draft = {
  query_id: string;
  query: string;
  family_id: string;
  domain: string;
  visual_type: string;
  query_type: string;
  split: string;
  created_at: string;
  synthetic: boolean;
  alternatives: Alternative[];
  reviews: Review[];
  attestation: {
    bucket: string;
    provider: string;
    frozen_at: string | null;
    index_version: string | null;
    evidence_reference: string | null;
  };
};
export type Task = {
  record: Draft;
  author: string;
  revision: number;
  status: string;
  issues: string[];
  history: {
    at: string;
    kind: string;
    reviewer: string;
    note: string;
    content_sha256: string;
    checks: string[];
  }[];
  previous_versions: Draft[];
};
export type Workspace = {
  schema_version: string;
  version: number;
  tasks: Task[];
};
export const domains = [
  "economics",
  "finance",
  "energy",
  "ai",
  "climate",
  "demographics",
  "labor",
  "housing",
  "science",
  "policy",
];
export const checks = [
  [
    "source",
    "I opened the primary publisher's source and checked its provenance.",
  ],
  [
    "identity",
    "I verified the exact visual, location and version, including original versus generated status.",
  ],
  ["query", "The question is realistic, answerable and sufficiently specific."],
  [
    "alternatives",
    "Each proposed answer matches the question. I found no other valid answer that needs adding.",
  ],
  [
    "requirements",
    "I verified every required item. If data is required, its download contains the data for this visual.",
  ],
] as const;
export function reviewGuidance(key: string, alternatives: Alternative[]) {
  if (key === "alternatives") return {
    check: `${alternatives.length} proposed answer${alternatives.length === 1 ? " is" : "s are"} shown. Check when every proposed answer satisfies the question and you have not identified another valid answer that is missing. One answer is enough; you do not need to invent another.`,
    leave: "Leave unchecked if a proposed answer is wrong, you found a missing valid answer, or you are unsure. Describe the issue in review notes and request changes.",
  };
  if (key === "requirements") {
    const needsData = alternatives.some(a => a.required.includes("data"));
    return {
      check: needsData
        ? "Check when every required item under ‘Required for success’ is appropriate and obtainable. This task requires data: open each required Dataset link and confirm it provides the numbers for the corresponding visual, with matching measures and series."
        : "Check when every required item under ‘Required for success’ is appropriate and obtainable. This task does not require data; you do not need to find a dataset to pass this check.",
      leave: "Leave unchecked if a required item is missing, unrelated, unnecessarily demanded, or you cannot verify it. Record what failed and request changes.",
    };
  }
  return null;
}
export function approvalBlockers(state: {
  name: string; prepared: boolean; matchesRole: boolean; decisionAllowed: boolean;
  dirty: boolean; human: boolean; notes: string; selectedChecks: string[];
  issues: string[]; busy: boolean;
}) {
  const reasons: string[] = [];
  if (state.busy) reasons.push("Wait for the current save to finish.");
  if (!state.name.trim()) reasons.push("Enter your reviewer name.");
  if (state.prepared) reasons.push("Click Start first review to claim this task before recording a decision.");
  else if (!state.matchesRole) reasons.push("Use the name and role assigned to this review.");
  else if (!state.decisionAllowed) reasons.push("The first reviewer must approve this version before independent review.");
  if (state.dirty) reasons.push("Save your task edits first.");
  const titles: Record<string, string> = {source: "Publisher source", identity: "Exact visual", query: "Question", alternatives: "Valid answers", requirements: "Required evidence"};
  for (const [key] of checks) if (!state.selectedChecks.includes(key)) reasons.push(`Complete the ‘${titles[key]}’ check after verifying it.`);
  if (!state.notes.trim()) reasons.push("Add review notes describing what you checked.");
  if (!state.human) reasons.push("Confirm that you personally reviewed this task.");
  if (state.issues.length) reasons.push("Resolve the task issues listed above.");
  return reasons;
}
export const statusNames: Record<string, string> = {
  draft: "Draft",
  awaiting_review: "Needs second review",
  changes_requested: "Changes requested",
  approved: "Approved",
};
export const blankIdentity = (): Identity => ({
  urls: [],
  sha256: [],
  ids: [],
});
export const blankAlternative = (id: string): Alternative => ({
  evidence_id: id,
  document: blankIdentity(),
  visual: blankIdentity(),
  authoritative_urls: [],
  locations: [],
  datasets: [],
  data_available: false,
  original_required: true,
  version: null,
  accepted_rights: [],
  methodology: blankIdentity(),
  reproducibility: blankIdentity(),
  required: ["document", "visual", "primary", "localization"],
  verification_urls: [],
  verification_notes: "",
});
export const lines = (value: string) => value.split(/\r?\n/);

export function cleanDraft(value: Draft): Draft {
  const record = structuredClone(value);
  const clean = (values: string[]) =>
    values.map((v) => v.trim()).filter(Boolean);
  const cleanIdentity = (identity: Identity): Identity => ({
    urls: clean(identity.urls),
    ids: clean(identity.ids),
    sha256: clean(identity.sha256),
  });
  for (const answer of record.alternatives) {
    answer.document = cleanIdentity(answer.document);
    answer.visual = cleanIdentity(answer.visual);
    answer.methodology = cleanIdentity(answer.methodology);
    answer.reproducibility = cleanIdentity(answer.reproducibility);
    answer.datasets = answer.datasets
      .map(cleanIdentity)
      .filter((d) => d.urls.length || d.ids.length || d.sha256.length);
    answer.authoritative_urls = clean(answer.authoritative_urls);
    answer.verification_urls = clean(answer.verification_urls);
    answer.accepted_rights = clean(answer.accepted_rights);
  }
  return record;
}
export const samePerson = (a: string, b: string) =>
  a.trim().replace(/\s+/g, " ").toLowerCase() ===
  b.trim().replace(/\s+/g, " ").toLowerCase();
export const safeSource = (value: string | undefined): string | undefined => {
  try {
    const u = new URL(value ?? "");
    return ["http:", "https:"].includes(u.protocol) &&
      !u.username &&
      !u.password
      ? u.href
      : undefined;
  } catch {
    return undefined;
  }
};
export async function reviewRequest<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(
    `/api/review/${path}`,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  if (!response.headers.get("Content-Type")?.includes("application/json"))
    throw Error(
      "Start the private review workspace to use this screen: uv run vessel review-ui",
    );
  const result = await response.json();
  if (!response.ok)
    throw Error(result.error ?? "The workspace could not save this change.");
  return result as T;
}
export async function downloadReview(path: "packet" | "dataset") {
  const saved = await reviewRequest<{
    file_path: string;
    filename: string;
    download_url: string;
  }>("export", { kind: path });
  const response = await fetch(saved.download_url);
  if (!response.ok) {
    const result = await response.json();
    throw Error(result.error);
  }
  const blob = new Blob([await response.text()], {
    type: path === "packet" ? "application/json" : "application/x-ndjson",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = saved.filename;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return saved.file_path;
}
