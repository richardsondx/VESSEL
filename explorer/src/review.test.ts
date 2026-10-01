import { describe, expect, it } from "vitest";
import {
  blankAlternative,
  checks,
  cleanDraft,
  lines,
  safeSource,
  samePerson,
} from "./review";

describe("human review browser contracts", () => {
  it("blocks unsafe preview URLs and retains primary source links", () => {
    expect(safeSource("javascript:alert(1)")).toBeUndefined();
    expect(safeSource("https://secret@example.org/chart.svg")).toBeUndefined();
    expect(safeSource("https://example.org/chart.svg")).toBe(
      "https://example.org/chart.svg",
    );
  });
  it("normalizes reviewer identity and multiline evidence references", () => {
    expect(samePerson(" Alice  Example ", "alice example")).toBe(true);
    expect(samePerson("Alice", "Bob")).toBe(false);
    expect(
      lines("https://example.org/a\n\n https://example.org/b "),
    ).toHaveLength(3); // Preserve blank lines while the person is still typing.
  });
  it("starts with unverified evidence and five explicit human checks", () => {
    const answer = blankAlternative("a1");
    expect(answer.data_available).toBe(false);
    expect(answer.verification_urls).toEqual([]);
    expect(answer.visual.urls).toEqual([]);
    expect(answer.original_required).toBe(true);
    expect(checks).toHaveLength(5);
  });
  it("cleans blank evidence lines only when saving, without losing reviewed identities", () => {
    const alternative = blankAlternative("a1");
    alternative.document.urls = [
      " https://example.org/a ",
      "",
      "https://example.org/b",
    ];
    alternative.document.ids = ["publisher-id"];
    const result = cleanDraft({ alternatives: [alternative] } as Parameters<
      typeof cleanDraft
    >[0]);
    expect(result.alternatives[0].document.urls).toEqual([
      "https://example.org/a",
      "https://example.org/b",
    ]);
    expect(result.alternatives[0].document.ids).toEqual(["publisher-id"]);
    expect(alternative.document.urls[1]).toBe("");
  });
});

it("explains when checks pass or fail, including tasks that do not require data", async () => {
  const { reviewGuidance } = await import("./review");
  const answer = blankAlternative("one");
  const alternatives = reviewGuidance("alternatives", [answer])!;
  expect(alternatives.check).toContain("1 proposed answer is shown");
  expect(alternatives.check).toContain("One answer is enough");
  expect(alternatives.leave).toContain("Leave unchecked");
  expect(reviewGuidance("requirements", [answer])!.check).toContain("does not require data");
  answer.required.push("data");
  expect(reviewGuidance("requirements", [answer])!.check).toContain("open each required Dataset link");
  expect(reviewGuidance("requirements", [answer])!.leave).toContain("cannot verify");
});
