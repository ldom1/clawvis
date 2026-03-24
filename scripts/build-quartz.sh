#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${ROOT_DIR}/scripts/lifecycle.sh"
load_env_file

MEM_DIR="${ROOT_DIR}/${MEMORY_ROOT:-instances/${INSTANCE_NAME:-example}/memory}"
QUARTZ_DIR="${ROOT_DIR}/quartz"

if [ -z "${CLAWVIS_QUIET_START:-}" ]; then
  echo "Quartz build: preparing brain display..."
fi

QUARTZ_AVAILABLE=0
# If a real Quartz workspace exists, build it.
if [ -d "${QUARTZ_DIR}" ] && [ -f "${QUARTZ_DIR}/package.json" ] && [ -f "${QUARTZ_DIR}/quartz.config.ts" ]; then
  QUARTZ_AVAILABLE=1
  (
    cd "${QUARTZ_DIR}"
    npm install --silent >/dev/null 2>&1
    # npx quartz build: output lands in quartz/public/
    npx quartz build >/dev/null 2>&1
  )
  if [ -z "${CLAWVIS_QUIET_START:-}" ]; then
    echo "Quartz build: completed (output: ${QUARTZ_DIR}/public/)"
  fi
fi

# Python fallback: run ONLY when Quartz is not available.
# When Quartz is present, it owns the display layer.
# The Python renderer is kept for edit-preview in the Hub Brain editor.
if [ "${QUARTZ_AVAILABLE}" -eq 0 ]; then
  if [ -z "${CLAWVIS_QUIET_START:-}" ]; then
    echo "Quartz not found — using Python HTML renderer (edit-only fallback)."
    echo "  To install Quartz: clawvis setup quartz"
  fi
fi

mkdir -p "${MEM_DIR}/projects"
# Always run the Python renderer for edit-preview HTML alongside .md files.
# When Quartz IS available, these files are used by the edit modal only (not display).
python3 - "${MEM_DIR}/projects" <<'PY'
import html
import re
import sys
from pathlib import Path

CSS = """
:root{color-scheme:dark}
body{margin:0;background:#0d1117;color:#e6edf3;font-family:Georgia,"Times New Roman",serif;font-size:18px;line-height:1.65}
article{max-width:42rem;margin:0 auto;padding:2rem 1.25rem 3rem}
h1{font-family:system-ui,sans-serif;font-size:2rem;font-weight:700;margin:0 0 1rem;letter-spacing:-.02em;color:#f0f6fc;border-bottom:1px solid #30363d;padding-bottom:.5rem}
h2{font-family:system-ui,sans-serif;font-size:1.35rem;margin:2rem 0 .75rem;color:#58a6ff}
h3{font-size:1.15rem;margin:1.5rem 0 .5rem;color:#c9d1d9}
p{margin:.85rem 0}
ul,ol{margin:.75rem 0;padding-left:1.35rem}
li{margin:.35rem 0}
a{color:#58a6ff;text-decoration:none}
code{font-family:ui-monospace,Menlo,monospace;font-size:.88em;background:#161b22;padding:.15em .4em;border-radius:4px;color:#ff7b72}
pre{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;overflow:auto;font-size:.85rem;line-height:1.45}
pre code{background:none;padding:0;color:#e6edf3}
.wiki{color:#a5d6ff}
"""


def render_md_simple(text: str) -> str:
    out: list[str] = []
    lines = text.splitlines()
    i = 0
    in_ul = False
    in_code = False
    code_buf: list[str] = []

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            close_ul()
            if in_code:
                out.append(
                    "<pre><code>"
                    + html.escape("\n".join(code_buf))
                    + "</code></pre>"
                )
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()
        if not stripped:
            close_ul()
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_ul()
            level = min(len(m.group(1)), 6)
            tag = f"h{level}"
            out.append(f"<{tag}>{html.escape(m.group(2).strip())}</{tag}>")
            i += 1
            continue

        if re.match(r"^[-*]\s+", stripped):
            if not in_ul:
                close_ul()
                in_ul = True
                out.append("<ul>")
            item = re.sub(r"^[-*]\s+", "", stripped)
            item = re.sub(
                r"\[\[([^\]]+)\]\]",
                r'<span class="wiki">[[\1]]</span>',
                html.escape(item),
            )
            out.append(f"<li>{item}</li>")
            i += 1
            continue

        close_ul()
        seg = html.escape(stripped)
        seg = re.sub(
            r"\[\[([^\]]+)\]\]",
            r'<span class="wiki">[[\1]]</span>',
            seg,
        )
        out.append(f"<p>{seg}</p>")
        i += 1

    close_ul()
    if in_code and code_buf:
        out.append(
            "<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>"
        )
    return "\n".join(out)


projects = Path(sys.argv[1])
md_files = sorted(projects.glob("*.md"))
for md in md_files:
    out = projects / f"{md.stem}.html"
    text = md.read_text(encoding="utf-8")
    title = md.stem
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    if first.startswith("# "):
        title = first[2:].strip() or md.stem
    body = render_md_simple(text)
    if not body.lstrip().startswith("<h1"):
        body = f"<h1>{html.escape(title)}</h1>\n" + body
    page = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>{CSS}</style></head><body><article class="markdown-body">{body}</article></body></html>"""
    out.write_text(page, encoding="utf-8")

if md_files:
    links = []
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        t = md.stem
        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        if first.startswith("# "):
            t = first[2:].strip() or md.stem
        links.append((t, f"{md.stem}.html"))
    idx_items = "\n".join(
        f"<li><a href='{html.escape(name)}'>{html.escape(t)}</a></li>"
        for t, name in links
    )
    index_html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Brain</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:2rem}}
.card{{max-width:42rem;margin:0 auto;border:1px solid #30363d;background:#161b22;border-radius:12px;padding:1.5rem}}
h1{{margin:0 0 .5rem;font-size:1.5rem}} p{{color:#8b949e;margin:0 0 1rem}} li{{margin:.4rem 0}} a{{color:#58a6ff}}
</style></head><body><div class="card"><h1>Brain</h1><p>Pages projets (HTML généré depuis les .md)</p><ul>{idx_items}</ul></div></body></html>"""
    (projects / "index.html").write_text(index_html, encoding="utf-8")
PY

# Keep UX stable: ensure at least one displayable HTML page exists.
if ! ls "${MEM_DIR}/projects"/*.html >/dev/null 2>&1; then
  cat > "${MEM_DIR}/projects/index.html" <<'EOF'
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Brain</title>
  <style>
    body{font-family:Inter,system-ui,sans-serif;background:#0b1020;color:#eef2ff;margin:0;padding:32px}
    .card{max-width:900px;margin:0 auto;border:1px solid #2d3b66;background:#151c31;border-radius:16px;padding:24px}
    h1{margin:0 0 10px;font-size:28px}
    p{color:#9aa6cf}
  </style>
</head>
<body>
  <div class="card">
    <h1>Brain</h1>
    <p>Le Brain est pret. Ajoute des notes dans memory/projects puis relance "clawvis restart".</p>
  </div>
</body>
</html>
EOF
fi

if [ -z "${CLAWVIS_QUIET_START:-}" ]; then
  echo "Quartz build: done."
fi
