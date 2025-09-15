#!/usr/bin/env python3
import os, json, time, pathlib, re, requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://mybusiness.mosyle.com/screens/scules/support/faq/article.php"
PAYLOAD_STATIC = {
    "usertab_current_os":        os.getenv("MDEVICE_OS", "mac"),
    "usertab_current_idcompany": os.getenv("MDEVICE_IDCOMPANY", "").strip()
}
COOKIES = {"PHPSESSID": os.getenv("MDEVICE_PHPSESSID", "").strip()}
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
}

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART_DIR = ROOT / "articles_md"
ART_DIR.mkdir(exist_ok=True)

ids_path = ROOT / "ids.json"
if not ids_path.exists():
    raise SystemExit("ids.json not found. Create it from the browser console first.")

ids = json.load(open(ids_path, "r", encoding="utf-8"))
ids = [str(x) for x in ids]

def fetch_one(art_id, tries=5, backoff=0.8):
    for i in range(tries):
        r = requests.post(API_URL,
                          data={**PAYLOAD_STATIC, "idarticle": art_id},
                          headers=HEADERS, cookies=COOKIES, timeout=30)
        if r.status_code not in (429, 500, 502, 503, 504):
            return r
        time.sleep(backoff * (2 ** i))
    r.raise_for_status()
    return r

for art_id in tqdm(ids, unit="article"):
    r = fetch_one(art_id)
    ct = r.headers.get("content-type", "")
    html = r.json().get("html") if ct.startswith("application/json") else r.text

    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one(".title, h1, h2")
    title = title_el.get_text(strip=True) if title_el else f"Article {art_id}"
    body  = soup.get_text("\n", strip=True)

    safe = re.sub(r'[<>:"/\\|?*]', '_', title)[:150]
    target = ART_DIR / f"{art_id} – {safe}.md"
    if target.exists():
        continue
    target.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    time.sleep(0.3)

print(str(ART_DIR.resolve()))
