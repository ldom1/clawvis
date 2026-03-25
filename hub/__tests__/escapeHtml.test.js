import {
  escapeHtml,
  projectInitials,
  projectAvatarHue,
} from "../src/utils.js";

test("escapeHtml escapes &, < and >", () => {
  expect(escapeHtml("&<>")).toBe("&amp;&lt;&gt;");
});

test("projectInitials / projectAvatarHue", () => {
  expect(projectInitials("E2E Project x")).toBe("EP");
  expect(projectAvatarHue("ab")).toBe(projectAvatarHue("ab"));
  expect(projectAvatarHue("a")).not.toBe(projectAvatarHue("b"));
});

