#!/usr/bin/env bash
# Sync docs/ → flat tree for GitHub Wiki (no subfolders). Source of truth: repo docs/.
set -euo pipefail

DOCS_ROOT="${1:?usage: sync-docs-to-wiki.sh <docs_dir> <wiki_clone_dir>}"
WIKI_ROOT="${2:?usage: sync-docs-to-wiki.sh <docs_dir> <wiki_clone_dir>}"

if [ ! -d "$DOCS_ROOT" ]; then
  echo "docs directory missing: $DOCS_ROOT" >&2
  exit 1
fi
if [ ! -d "$WIKI_ROOT/.git" ]; then
  echo "wiki clone missing .git: $WIKI_ROOT" >&2
  exit 1
fi

md_count=$(find "$DOCS_ROOT" -type f -name '*.md' ! -path '*/.git/*' | wc -l)
if [ "$md_count" -eq 0 ]; then
  echo "No .md files under $DOCS_ROOT — nothing to sync."
  exit 0
fi

find "$WIKI_ROOT" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

if [ -f "$DOCS_ROOT/README.md" ]; then
  cp "$DOCS_ROOT/README.md" "$WIKI_ROOT/Home.md"
elif [ -f "$DOCS_ROOT/index.md" ]; then
  cp "$DOCS_ROOT/index.md" "$WIKI_ROOT/Home.md"
fi

while IFS= read -r -d '' f; do
  rel="${f#"$DOCS_ROOT"/}"
  case "$rel" in
    README.md | index.md) continue ;;
    *)
      flat=$(printf '%s' "$rel" | tr '/' '-')
      cp "$f" "$WIKI_ROOT/$flat"
      ;;
  esac
done < <(find "$DOCS_ROOT" -type f -name '*.md' ! -path '*/.git/*' -print0)

echo "Synced markdown from $DOCS_ROOT → $WIKI_ROOT (flat names, Home.md from README or index)."
