#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

rm -f mosyle_collection.md index.tsv

find . -type f -name '*.md' ! -name 'mosyle_collection.md' | while read -r f; do
  id=$(basename "$f" | cut -d' ' -f1)
  title=$(sed -n '1s/^# //p' "$f")
  printf '%s\t%s\t%s\n' "$id" "$title" "$f" >> index.tsv
  {
    printf '---\nid: %s\ntitle: %s\n---\n' "$id" "$title"
    cat "$f"
    printf '\n\n'
  } >> mosyle_collection.md
done
