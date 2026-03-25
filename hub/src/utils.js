export function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

/** Two-letter initials for default project avatar (no uploaded logo). */
export function projectInitials(name) {
  const s = String(name || "").trim();
  if (!s) return "?";
  const parts = s.split(/\s+/).filter(Boolean);
  if (parts.length >= 2)
    return (parts[0][0] + (parts[1][0] || "")).toUpperCase().slice(0, 2) || "?";
  return s.slice(0, 2).toUpperCase() || "?";
}

/** Stable hue 0–359 from slug or name for avatar gradient. */
export function projectAvatarHue(slug) {
  const s = String(slug || "");
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h) % 360;
}
