#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
cd articles_md

sed -i '' '/Copy article link to clipboard/d' *.md || true

for f in *.md; do
  awk '
    {gsub(/^[ \t]+|[ \t]+$/, "")}
    NR==2 && $0=="Back" {next}
    $0=="Copy article link to clipboard" {next}
    1
  ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

mkdir -p _header_md _brief_md _triple_md

printf '%s\n' *.md \
| grep -E '^[0-9]+ – [0-9]{1,2}(\.[0-9]{1,2}){0,2}[[:space:]]' \
| grep -vE ' – [12][0-9]{3}[[:space:]]' \
| xargs -I{} mv -v "{}" _header_md/ || true

for f in *.md; do
  lines=$(wc -l <"$f")
  if [ "$lines" -le 6 ] && grep -q "^Last Update:" "$f"; then
    mv -v "$f" _brief_md/
  fi
done

for f in *.md; do
  t=$(sed -n '1s/^# //p' "$f")
  [ -z "$t" ] && continue
  [ -z "$(sed -n '2p' "$f")" ] || continue
  [ "$(sed -n '3p' "$f")" = "$t" ] || continue
  [ "$(grep -cv '^$' "$f")" -eq 2 ] || continue
  mv -v "$f" _triple_md/
done
