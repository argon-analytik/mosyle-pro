# Mosyle Pro – Knowledge & Assistant Toolkit

A complete, reproducible workflow to **extract Mosyle help-center articles as Markdown**
(for internal use), clean them up, **merge into a master file**, and feed them into an
**OpenAI Assistants Vector Store** for a focused “Mosyle Pro” bot.

> ⚠️ **Legal**: Mosyle text is © Mosyle. Keep raw content private inside your org.
> This repo ships scripts & guides only.

---

## 0. Prerequisites

- macOS / Linux
- Python 3.9+
- Chrome (for the console snippet)
- Your Mosyle tenant credentials

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the values.

---

## 1. Collect article IDs (Chrome)

Open Mosyle Help Center, then in **Console** paste:

```js
(async()=>{
  const a='.article.section > .arrow, span.chevron';
  for(;;){
    const c=[...document.querySelectorAll(a)]
      .filter(e=>!e.parentElement.classList.contains('showing_children')&&!e.closest('[data-open="true"]'));
    if(!c.length) break; c.forEach(e=>e.click());
    await new Promise(r=>setTimeout(r,200));
  }
  const ids=[...document.querySelectorAll('[data-article-id],[onclick*="viewArticle"]')]
    .map(el=>el.dataset.articleId||(el.getAttribute('onclick').match(/,\s*(\d+)\)/)||[])[1])
    .filter(Boolean);
  copy(JSON.stringify(ids,null,2));
})();
```

Then save the list:

```bash
cd mosyle-pro
mkdir -p articles_md
pbpaste > ids.json
python3 -m json.tool ids.json
```

Safari fallback (no clipboard):

```js
(()=>{const ids=[...document.querySelectorAll('[data-article-id],[onclick*="viewArticle"]')]
.map(el=>el.dataset.articleId||(el.getAttribute('onclick').match(/,\s*(\d+)\)/)||[])[1])
.filter(Boolean);console.log(JSON.stringify(ids,null,2));})();
```

---

## 2. Dump articles (Python, authenticated)

Set env in `.env`:

```
MDEVICE_PHPSESSID=put_your_cookie_here
MDEVICE_IDCOMPANY=your_company_id
MDEVICE_OS=mac
```

Run the downloader:

```bash
python scripts/dump_mosyle.py
```

Markdown goes into `articles_md/ID – Title.md`.

---

## 3. Clean up Markdown (optional but recommended)

```bash
bash scripts/clean_md.sh
```

What it does:

- removes the `Copy article link to clipboard` line
- removes a stray `Back` line right after the title
- moves category headers (like `3.01`, `3.03.2`, `7.`) into `_header_md/`
- moves ultra-short "brief sheets" into `_brief_md/`
- moves 3-liners (*Title / blank / Title*) into `_triple_md/`

---

## 4. Merge master + build index

```bash
bash scripts/merge_collection.sh
bash scripts/build_index_md.sh
```

- `mosyle_collection.md` – concatenation with YAML headers
- `index.tsv` / `index.md` – overview

---

## 5. Vector Store (OpenAI)

Suggested chunking for these short articles:

- **Chunk size:** 400
- **Overlap:** 40

Upload `mosyle_collection.md` to your Vector Store. Create an Assistant with
the system prompt from `assistant/system_prompt.md`.

---

## 6. Conversation starters

See `assistant/conversation_starters.md` for ready-to-use prompts.

---

## 7. Safety

- Keep the raw Markdown private.
- If you plan distribution, obtain written permission from Mosyle first.

---

MIT © Argon Analytik
