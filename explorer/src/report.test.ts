import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";
import { loadDefaultReport, parseReport, percent } from "./report";
const fixture = () =>
  JSON.parse(
    readFileSync(
      new URL("../public/demo-report.json", import.meta.url),
      "utf8",
    ),
  );
describe("artifact contract", () => {
  it("loads the explicit offline demo", () => {
    const r = parseReport(fixture());
    expect(r.manifest.mode).toBe("replay");
    expect(r.cells).toHaveLength(80);
  });
  it("rejects missing report fields", () =>
    expect(() => parseReport({})).toThrow());
  it("rejects unsafe source links", () => {
    const r = fixture();
    r.cells[0].response.results[0].url = "javascript:alert(1)";
    expect(() => parseReport(r)).toThrow();
  });
  it("rejects a fixture claiming publication eligibility", () => {
    const r = fixture();
    r.manifest.publication_eligible = true;
    expect(() => parseReport(r)).toThrow();
  });
  it("formats absent data without implying zero", () =>
    expect(percent(null)).toBe("—"));
});

describe("default report loading", () => {
  it("falls back when the dev server returns an HTML shell for missing JSON", async () => {
    const request = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response("<!doctype html>", {
          headers: { "content-type": "text/html" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(fixture()), {
          headers: { "content-type": "application/json" },
        }),
      );
    expect((await loadDefaultReport(request)).manifest.mode).toBe("replay");
    expect(request).toHaveBeenNthCalledWith(2, "/demo-report.json");
  });
  it("reports an empty artifact directory cleanly", async () => {
    const request = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response("missing", { status: 404 }));
    await expect(loadDefaultReport(request)).rejects.toThrow(
      "No report available",
    );
  });
});

it("rejects partial depth summaries instead of crashing the explorer", () => {
  const r = fixture();
  delete r.summary.evidence8["10"];
  expect(() => parseReport(r)).toThrow();
});
it("rejects missing per-query scores", () => {
  const r = fixture();
  delete r.cells[0].scores["5"];
  expect(() => parseReport(r)).toThrow();
});
it("rejects duplicate result cells", () => {
  const r = fixture();
  r.cells.push(r.cells[0]);
  expect(() => parseReport(r)).toThrow();
});
