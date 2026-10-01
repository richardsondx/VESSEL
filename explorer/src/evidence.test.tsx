import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Evidence } from "./ReviewApp";
import { blankAlternative } from "./review";

describe("visual-first human review", () => {
  it("renders the visual immediately, before notes, with full-size access", () => {
    const answer = blankAlternative("chart");
    answer.visual.urls = ["https://publisher.example/chart.svg"];
    answer.document.urls = ["https://publisher.example/report.pdf"];
    answer.verification_notes = "Verify the units and population.";
    const html = renderToStaticMarkup(createElement(Evidence, { alternative: answer }));
    expect(html).toContain('<img');
    expect(html).toContain('src="https://publisher.example/chart.svg"');
    expect(html.indexOf('<img')).toBeLessThan(html.indexOf(answer.verification_notes));
    expect(html).toContain('aria-label="Enlarge visual chart"');
    expect(html).not.toContain('<iframe');
    expect(html).not.toContain('Show source preview');
  });
  it("opens the recorded PDF page automatically when no separate visual exists", () => {
    const answer = blankAlternative("pdf");
    answer.document.urls = ["https://publisher.example/report.pdf"];
    answer.locations = [{page_index: 3, page_label: "ii", figure: null, bbox: null, locator: null}];
    const html = renderToStaticMarkup(createElement(Evidence, { alternative: answer }));
    expect(html).toContain('report.pdf#page=4');
    expect(html).toContain('<iframe');
    expect(html).not.toContain('<img');
  });
  it("explains missing previews while retaining the publisher link", () => {
    const answer = blankAlternative("missing");
    answer.document.urls = ["https://publisher.example/article"];
    const html = renderToStaticMarkup(createElement(Evidence, { alternative: answer }));
    expect(html).toContain('No previewable visual has been recorded');
    expect(html).toContain('href="https://publisher.example/article"');
    expect(html).not.toContain('<img');
  });
});
