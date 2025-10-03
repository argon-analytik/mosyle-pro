# Mosyle Pro – Knowledge & Assistant Toolkit

A complete, reproducible workflow to **extract Mosyle help-center articles as Markdown**
(for internal use), clean them up, **merge into a master file**, and feed them into an
**OpenAI Assistants Vector Store** for a focused “Mosyle Pro” bot.

> ⚠️ Legal: Mosyle text is © Mosyle. Keep raw content private inside your org.
> This repo ships scripts & guides only.
>

---

## 0) Requirements

- macOS or Linux
- Google Chrome (for the Console step)
- Python 3.9+
- Your Mosyle tenant access (to obtain `PHPSESSID` and `idcompany`)

---

## 1) Collect article IDs in Chrome and download ids.json

1. Open Mosyle → Help Center.

2. `⌥⌘I` → **Console**. On first paste, type **Allow paste** and press Enter.

3. Paste and run:

```bash
js
(async ()=>{
  const sleep = ms => new Promise(r=>setTimeout(r,ms));
  const sc = document.querySelector('#helpcenter_box, .hc_window, #helpcenter_container') || document.scrollingElement;
  for(;;){
    const needOpen = [
      ...document.querySelectorAll('.article.section:not(.showing_children) > .infos'),
      ...document.querySelectorAll('div[data-open="false"] > .infos')
    ];
    if(!needOpen.length) break;
    for(const el of needOpen){ el.click(); if(sc){ sc.scrollTop = sc.scrollHeight; } await sleep(250); }
    if(sc){ sc.scrollTop = sc.scrollHeight; await sleep(200); }
  }
  const ids = [...new Set(
    [...document.querySelectorAll('.infos[onclick^="Support.viewArticle"], [onclick*="viewArticle"]')]
      .map(e => e.getAttribute('onclick')?.match(/,\s*(\d+)\)/)?.[1])
      .filter(Boolean)
  )];
  const blob = new Blob([JSON.stringify(ids,null,2)], {type:'application/json'});
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'ids.json' });
  document.body.appendChild(a); a.click(); URL.revokeObjectURL(a.href); a.remove();
  console.log(`downloaded ids.json with ${ids.length} IDs`);
})();

```

You get **`ids.json`** in your Downloads folder.

---

## 2) Create workspace and Python environment

```bash
mkdir -p ~/mosyle_dump
cd ~/mosyle_dump
python3 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 lxml tqdm
mv ~/Downloads/ids.json .
python3 -m json.tool ids.json

```

If the last command errors, repeat step 1 (the file was empty).

---

## 3) Get your Mosyle session and tenant values in **Chrome**

- **PHPSESSID**: DevTools → Application → Storage → Cookies → `PHPSESSID` (copy value)
- **idcompany**: DevTools → Network → click any article request → Payload shows `usertab_current_idcompany`

Export them in your shell:

```bash
export MOS_PHPSESSID='paste_your_cookie_here'
export MOS_IDCOMPANY='your_idcompany_here'

```

---

## 4) Create the downloader and run it

Create the script:

```bash
cat > dump_mosyle.py <<'PY'
#!/usr/bin/env python3
import os, json, time, pathlib, re, requests
from bs4 import BeautifulSoup
from tqdm import tqdm

API_URL = "https://mybusiness.mosyle.com/screens/scules/support/faq/article.php"
PAYLOAD_STATIC = {"usertab_current_os":"mac","usertab_current_idcompany":os.getenv("MOS_IDCOMPANY","")}
COOKIES = {"PHPSESSID": os.getenv("MOS_PHPSESSID","")}
HEADERS = {"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With":"XMLHttpRequest"}

out = pathlib.Path("articles_md"); out.mkdir(exist_ok=True)
ids = [str(x) for x in json.load(open("ids.json","r",encoding="utf-8"))]

for art_id in tqdm(ids, unit="article"):
    r = requests.post(API_URL, data={**PAYLOAD_STATIC,"idarticle":art_id}, headers=HEADERS, cookies=COOKIES, timeout=30)
    r.raise_for_status()
    html = r.json().get("html") if r.headers.get("content-type","").startswith("application/json") else r.text
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one(".title, h1, h2")
    title = title_el.get_text(strip=True) if title_el else f"Article {art_id}"
    body  = soup.get_text("\n", strip=True)
    safe  = re.sub(r'[<>:"/\\|?*]', '_', title)[:150]
    target = out / f"{art_id} – {safe}.md"
    if not target.exists():
        target.write_text(f"# {title}\n\n{body}", "utf-8")
    time.sleep(0.3)
print(out.resolve())
PY
chmod +x dump_mosyle.py

```

Run the dump:

```bash
source .venv/bin/activate
python3 dump_mosyle.py

```

Markdown files appear in `~/mosyle_dump/articles_md/`.

---

## 5) Clean up and merge (safe script, nothing is deleted)

This script removes boilerplate lines, moves very short files and numeric headers aside, and builds a single **`mosyle_collection.md`** with YAML front-matter per article plus `index.md`/`index.tsv`.

Create:

```bash
cat > ~/mosyle_dump/articles_md/cleanup_merge_safe.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
DIR="${1:-$HOME/mosyle_dump/articles_md}"
cd "$DIR"
shopt -s nullglob
mkdir -p _header_md _short_md

sed -i '' '/Copy article link to clipboard/d' *.md 2>/dev/null || true

for f in *.md; do
  awk '{gsub(/^[ \t]+|[ \t]+$/,"")} NR==2&&$0=="Back"{next} $0=="Copy article link to clipboard"{next} {print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

for f in *.md; do
  non=$(grep -cve '^\s*$' "$f"); [ "$non" -lt 8 ] && mv -v "$f" _short_md/
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
SH
chmod +x ~/mosyle_dump/articles_md/cleanup_merge_safe.sh

```

Run:

```bash
~/mosyle_dump/articles_md/cleanup_merge_safe.sh

```

Outputs:

- `mosyle_collection.md` (merged, YAML headers)
- `index.md` and `index.tsv` (overview)
- `_header_md/` (numeric headers only)
- `_short_md/` (very short files with < 8 non-blank lines)

---

## 6) Vector Store (OpenAI Assistants)

- Upload `mosyle_collection.md` to a Vector Store.
- Chunk settings recommended for these short articles:
    - Chunk size: **400**
    - Overlap: **40**
- Keep **Max results = 20** (default).

---

## 7) Troubleshooting

| Symptom | Fix |
| --- | --- |
| Chrome console shows `Unexpected token` for `cd`/`pbpaste` | Those are shell commands; use the macOS Terminal. Only JavaScript goes in Chrome Console. |
| `python3 -m json.tool ids.json` fails | Re-run step 1; use the snippet that **downloads** `ids.json`. Move the file into `~/mosyle_dump` and validate again. |
| 401/403 when running the downloader | Set a fresh `MOS_PHPSESSID` and `MOS_IDCOMPANY` (step 3) and retry. |
| 404 while downloading | Use the exact endpoint in this README: `/screens/scules/support/faq/article.php` with POST and `idarticle`. |
| `mosyle_collection.md` is empty | Run the safe cleanup script again; it now merges from `.`, `_header_md`, and `_short_md`. Ensure files exist after earlier filtering. |
| Filenames break on `? :` etc. | The script already sanitises titles; remove old broken files and rerun if needed. |

---

## 8) Updating later

- Re-run the Chrome snippet to download a fresh `ids.json`.
- `python3 dump_mosyle.py` downloads missing articles only.
- `~/mosyle_dump/articles_md/cleanup_merge_safe.sh` rebuilds the collection and index.

---

## 9) Optional: Build a focused Assistant

- System prompt: keep the bot scoped to Mosyle MDM answers, use File Search first, answer concisely, code blocks copy-ready, cite like `[1102 – How do I create a Push Certificate]`.
- Opening line suggestion: “I’m Mosyle Pro, your assistant for Mosyle MDM.”

---
