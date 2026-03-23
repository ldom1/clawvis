import { escapeHtml } from "../src/utils.js";

test("escapeHtml escapes &, < and >", () => {
  expect(escapeHtml("&<>")).toBe("&amp;&lt;&gt;");
});

