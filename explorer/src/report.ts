import { z } from "zod";
const components = z.record(z.string(), z.boolean());
const url = z
  .string()
  .refine((v) => /^https?:\/\//.test(v), "Expected an HTTP(S) URL");
const source = z
  .object({
    document_url: url.nullable().optional(),
    document_title: z.string().nullable().optional(),
    publisher: z.string().nullable().optional(),
    published_at: z.string().nullable().optional(),
    version: z.string().nullable().optional(),
  })
  .passthrough();
const identity = z.object({
  urls: z.array(url),
  sha256: z.array(z.string()),
  ids: z.array(z.string()),
});
const score = z.object({
  full_support: z.boolean(),
  reciprocal_rank: z.number(),
  failure: z.string().nullable(),
  components,
  diagnostics: z.array(
    z
      .object({
        rank: z.number(),
        bundle: z.number(),
        evidence_id: z.string(),
        full_support: z.boolean(),
        missing: z.array(z.string()),
        components,
      })
      .passthrough(),
  ),
});
const metric = z
  .object({
    queries: z.number(),
    statuses: z.record(z.string(), z.number()),
    full_support: z.number().nullable(),
    full_support_ci95: z.array(z.number()).nullable(),
    components: z.record(z.string(), z.number().nullable()),
    data_recall: z.number().nullable(),
    data_denominator: z.number(),
    supplemental: z
      .record(
        z.string(),
        z.object({ denominator: z.number(), recall: z.number().nullable() }),
      )
      .optional(),
    mrr: z.number().nullable(),
    median_latency_ms: z.number().nullable(),
    reserved_cost_usd: z.number(),
    failures: z.record(z.string(), z.number()),
  })
  .passthrough();
export const reportSchema = z
  .object({
    schema_version: z.literal("vessel.report.v1"),
    notice: z.string(),
    manifest: z
      .object({
        run_id: z.string(),
        mode: z.enum(["live", "replay"]),
        status: z.enum(["running", "complete", "incomplete"]),
        publication_eligible: z.boolean(),
        dataset_release_ready: z.boolean(),
        benchmark_version: z.string(),
        dataset_sha256: z.string(),
        config_sha256: z.string(),
        code_sha256: z.string(),
        requests: z.number(),
        reserved_cost_usd: z.number(),
        started_at: z.string(),
        config: z
          .object({
            protocol: z.enum(["search", "search_fetch", "evidence"]),
            k: z.number().min(1).max(10),
          })
          .passthrough(),
      })
      .passthrough(),
    summary: z.record(z.string(), z.record(z.string(), metric)),
    breakdowns: z.record(
      z.string(),
      z.record(z.string(), z.record(z.string(), metric)),
    ),
    paired: z.array(
      z.object({
        first: z.string(),
        second: z.string(),
        k: z.number(),
        difference: z.number(),
        ci95: z.array(z.number()).nullable(),
      }),
    ),
    cells: z.array(
      z.object({
        provider: z.string(),
        query_id: z.string(),
        gold: z
          .object({
            query: z.string(),
            domain: z.string(),
            visual_type: z.string(),
            query_type: z.string(),
            family_id: z.string(),
            synthetic: z.boolean(),
            attestation: z.object({ bucket: z.string() }),
            alternatives: z.array(
              z
                .object({
                  evidence_id: z.string(),
                  document: identity,
                  visual: identity,
                  required: z.array(z.string()),
                  locations: z.array(z.unknown()),
                  data_available: z.boolean(),
                  original_required: z.boolean(),
                  verification_notes: z.string(),
                })
                .passthrough(),
            ),
          })
          .passthrough(),
        response: z
          .object({
            status: z.string(),
            reason: z.string().nullable().optional(),
            replay: z.boolean(),
            results: z.array(
              z
                .object({
                  rank: z.number(),
                  title: z.string(),
                  url: url.nullable(),
                  bundles: z.array(
                    z
                      .object({
                        source,
                        visual: z
                          .object({
                            url: url.nullable().optional(),
                            sha256: z.string().nullable().optional(),
                            rendition: z.string(),
                          })
                          .nullable(),
                        location: z.unknown(),
                        datasets: z.array(
                          z
                            .object({ url: url.nullable().optional() })
                            .passthrough(),
                        ),
                        rights: z.string().nullable(),
                      })
                      .passthrough(),
                  ),
                })
                .passthrough(),
            ),
            observations: z.array(z.unknown()),
          })
          .passthrough(),
        scores: z.record(z.string(), score),
      }),
    ),
  })
  .superRefine((r, ctx) => {
    if (
      r.manifest.publication_eligible &&
      (r.manifest.mode === "replay" ||
        r.manifest.status !== "complete" ||
        !r.manifest.dataset_release_ready ||
        r.cells.some(
          (c) =>
            c.gold.synthetic || !["ok", "no_match"].includes(c.response.status),
        ))
    )
      ctx.addIssue({
        code: "custom",
        message: "Inconsistent publication eligibility",
      });
    if (!r.cells.length)
      ctx.addIssue({ code: "custom", message: "Report has no query results" });
    const depths = [1, 5, 10]
      .filter((k) => k <= r.manifest.config.k)
      .map(String);
    const systems = Object.keys(r.summary);
    if (!systems.length)
      ctx.addIssue({ code: "custom", message: "Report has no summary" });
    for (const system of systems) {
      if (depths.some((k) => !r.summary[system][k]))
        ctx.addIssue({ code: "custom", message: "Missing summary depth" });
    }
    const identities = new Set<string>();
    for (const cell of r.cells) {
      if (
        !systems.includes(cell.provider) ||
        depths.some((k) => !cell.scores[k])
      )
        ctx.addIssue({
          code: "custom",
          message: "Missing provider or score depth",
        });
      const identity = JSON.stringify([cell.provider, cell.query_id]);
      if (identities.has(identity))
        ctx.addIssue({ code: "custom", message: "Duplicate result cell" });
      identities.add(identity);
    }
  });
export type Report = z.infer<typeof reportSchema>;
export type Cell = Report["cells"][number];
export const percent = (n: number | null | undefined) =>
  n == null ? "—" : `${(n * 100).toFixed(1)}%`;
export const displayName = (name: string) =>
  ({
    evidence8: "Evidence8",
    keenable: "Keenable",
    exa: "Exa",
    serper: "Google / Serper",
    keenable_evidence8: "Keenable + Evidence8",
  })[name] ?? name;
export function parseReport(raw: unknown): Report {
  return reportSchema.parse(raw);
}

export async function loadDefaultReport(
  fetcher: typeof fetch = fetch,
): Promise<Report> {
  for (const path of ["/report.json", "/demo-report.json"]) {
    const response = await fetcher(path);
    if (response.ok && response.headers.get("content-type")?.includes("json")) {
      return parseReport(await response.json());
    }
  }
  throw Error(
    "No report available. Import an exported VESSEL report to begin.",
  );
}
