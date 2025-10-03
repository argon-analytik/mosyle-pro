#!/usr/bin/env python3
"""Download Mosyle Help Center articles as Markdown files."""
import argparse
import json
import os
import pathlib
import re
import sys
import time
from typing import Iterable, List

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

API_URL = "https://mybusiness.mosyle.com/screens/scules/support/faq/article.php"
USER_AGENT = "Mozilla/5.0"
DEFAULT_SLEEP = 0.3


def read_ids(path: pathlib.Path) -> List[str]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse {path}: {exc}") from exc
    if not isinstance(data, Iterable):
        raise SystemExit(f"Expected a list of IDs in {path}")
    return [str(item) for item in data if str(item).strip()]


def build_session() -> requests.Session:
    phpsessid = os.getenv("MOS_PHPSESSID", "").strip()
    idcompany = os.getenv("MOS_IDCOMPANY", "").strip()
    if not phpsessid or not idcompany:
        raise SystemExit("Set MOS_PHPSESSID and MOS_IDCOMPANY environment variables before running.")
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    })
    session.cookies.set("PHPSESSID", phpsessid)
    session.params = {}
    session_payload = {
        "usertab_current_os": "mac",
        "usertab_current_idcompany": idcompany,
    }
    session.session_payload = session_payload  # type: ignore[attr-defined]
    return session


def sanitize_title(title: str) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*]", "_", title)
    return cleaned[:150]


def write_markdown(output_dir: pathlib.Path, article_id: str, title: str, body: str) -> pathlib.Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{article_id} – {sanitize_title(title)}.md"
    path = output_dir / filename
    if path.exists():
        return path
    path.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    return path


def extract_article_content(html: str, fallback_title: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one(".title, h1, h2")
    title = title_el.get_text(strip=True) if title_el else fallback_title
    body = soup.get_text("\n", strip=True)
    return title or fallback_title, body


def download_articles(ids: List[str], output_dir: pathlib.Path, sleep: float) -> None:
    session = build_session()
    payload_static = session.session_payload  # type: ignore[attr-defined]

    for article_id in tqdm(ids, unit="article"):
        payload = dict(payload_static, idarticle=article_id)
        response = session.post(API_URL, data=payload, timeout=30)
        response.raise_for_status()
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            html = data.get("html", "") if isinstance(data, dict) else ""
        else:
            html = response.text
        title, body = extract_article_content(html, f"Article {article_id}")
        write_markdown(output_dir, article_id, title, body)
        time.sleep(sleep)



def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", type=pathlib.Path, help="Path to ids.json")
    parser.add_argument("--output", "-o", type=pathlib.Path, default=pathlib.Path("articles_md"),
                        help="Directory to write Markdown files")
    parser.add_argument("--sleep", type=float, default=DEFAULT_SLEEP,
                        help="Delay between requests in seconds (default: %(default)s)")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    ids = read_ids(args.ids)
    if not ids:
        raise SystemExit(f"No article IDs found in {args.ids}")
    download_articles(ids, args.output, args.sleep)
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
