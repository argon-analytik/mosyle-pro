#!/usr/bin/env bash
set -euo pipefail
DIR="${1:-$HOME/mosyle_dump/articles_md}"
cd "$DIR"
shopt -s nullglob
mkdir -p _header_md _short_md

if command -v gsed >/dev/null 2>&1; then
  gsed -i "/Copy article link to clipboard/d" *.md 2>/dev/null || true
else
  sed -i'' '/Copy article link to clipboard/d' *.md 2>/dev/null || true
fi

for f in *.md; do
  awk '{gsub(/^[ \t]+|[ \t]+$/,"")} NR==2&&$0=="Back"{next} $0=="Copy article link to clipboard"{next} {print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

for f in *.md; do
  non=$(grep -cve '^\s*$' "$f")
  if [ "$non" -lt 8 ]; then
    mv -v "$f" _short_md/
  fi
done

grep -lE '^#{1,4}[[:space:]]+[0-9]{1,2}(\.[0-9]{1,2}){0,2}[[:space:]]' *.md 2>/dev/null \
  | grep -vE '^#{1,4}[[:space:]]+[12][0-9]{3}[[:space:]]' 2>/dev/null \
  | xargs -I{} mv -v "{}" _header_md/ 2>/dev/null || true

rm -f mosyle_collection.md index.tsv index.md

find . _header_md _short_md -type f -name '*.md' \
  ! -name 'mosyle_collection.md' \
  ! -name 'index.md' \
  -print0 | sort -z | while IFS= read -r -d '' f; do
  id=$(basename "$f" | cut -d' ' -f1)
  title=$(sed -n '1s/^# //p' "$f")
  printf '%s\t%s\t%s\n' "$id" "$title" "$f" >> index.tsv
  printf -- '---\nid: %s\ntitle: %s\n---\n' "$id" "$title" >> mosyle_collection.md
  cat "$f" >> mosyle_collection.md
  printf -- '\n\n' >> mosyle_collection.md
done

awk -F'\t' 'BEGIN{print "# Mosyle Index\n"} {printf "* **%s** — %s  \\n", $1,$2}' index.tsv > index.md

printf "Done\n"
printf "Kept (root): %s\n" "$(find . -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
printf "Headers: %s\n" "$(find _header_md -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
printf "Short: %s\n" "$(find _short_md -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
printf "Collection lines: %s\n" "$(wc -l < mosyle_collection.md 2>/dev/null || echo 0)"
