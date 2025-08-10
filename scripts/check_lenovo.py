import sys
import re
import json
import datetime as dt
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

URL = "https://www.lenovo.com/it/it/p/laptops/thinkpad/thinkpadt/thinkpad-t16-gen-4-16-inch-intel/21qe004kix"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "close",
}

TIMEOUT = 25


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def from_json_ld(soup: BeautifulSoup) -> str | None:
    # Try to read availability from schema.org Offer in JSON-LD blocks
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue

        candidates = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for obj in candidates:
            offers = obj.get("offers")
            if not offers:
                continue
            if isinstance(offers, dict):
                avail = offers.get("availability")
                if isinstance(avail, str):
                    return avail
            elif isinstance(offers, list):
                for off in offers:
                    if isinstance(off, dict) and isinstance(off.get("availability"), str):
                        return off["availability"]
    return None


def extract_inventory_message(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    # 1) Known selector (if server-side rendered)
    node = soup.select_one(".inventory_message")
    if node and node.get_text(strip=True):
        return node.get_text(strip=True)

    # 2) JSON-LD availability (schema.org)
    avail = from_json_ld(soup)
    if avail:
        return avail  # e.g. "http://schema.org/InStock", "http://schema.org/PreOrder", "http://schema.org/OutOfStock"

    # 3) Heuristics over related classes
    candidates = soup.select(".inventory, .availability, [class*='inventory'], [class*='availability']")
    for c in candidates:
        txt = c.get_text(" ", strip=True)
        if txt and 5 <= len(txt) <= 200:
            return txt

    # 4) Fallback: keyword search in raw HTML
    hay = html.lower()
    if "preordine" in hay or "pre-ordine" in hay:
        return "PREORDINE (matched in raw HTML)"
    if "disponibile" in hay:
        return "DISPONIBILE (matched in raw HTML)"
    if "quasi esaurito" in hay:
        return "QUASI ESAURITO (matched in raw HTML)"
    if "esaurito" in hay:
        return "ESAURITO (matched in raw HTML)"

    return None


def classify_status(message: str) -> str:
    m = message.lower()
    if "schema.org/preorder" in m or "preordine" in m or "pre-ordine" in m:
        return "PREORDER"
    if "schema.org/instock" in m or "disponibil" in m:
        return "AVAILABLE"
    if "schema.org/outofstock" in m or "quasi esaurito" in m or "esaurito" in m:
        return "LOW_STOCK" if "quasi" in m else "OUT_OF_STOCK"
    return "UNKNOWN"


def sanitize_md_cell(text: str) -> str:
    """Make text safe for a Markdown table cell."""
    # Replace pipe with escaped version and collapse newlines
    return str(text).replace("|", r"\|").replace("\n", " ").strip()


def main():
    print("=== Lenovo T16 Availability Check ===")
    ts_rome = dt.datetime.now(ZoneInfo("Europe/Rome"))
    timestamp = ts_rome.isoformat()  # includes +01:00 or +02:00 depending on DST
    print("Timestamp (Europe/Rome):", timestamp)
    print("URL:", URL)

    try:
        html = fetch_html(URL)
    except Exception as e:
        print("ERROR: failed to fetch page:", repr(e))
        sys.exit(0)

    msg = extract_inventory_message(html)
    if not msg:
        print("WARNING: inventory message not found.")
        return

    status = classify_status(msg)
    print("Inventory message:", msg)
    print("Parsed status:", status)

    # Append to history.md (create header if missing)
    history_line = f"| {sanitize_md_cell(timestamp)} | {sanitize_md_cell(status)} | {sanitize_md_cell(msg)} |\n"
    header = "| Timestamp (Europe/Rome) | Status | Message |\n|---|---|---|\n"
    try:
        try:
            with open("history.md", "r", encoding="utf-8") as f:
                exists = bool(f.read().strip())
        except FileNotFoundError:
            exists = False
        with open("history.md", "a", encoding="utf-8") as f:
            if not exists:
                f.write(header)
            f.write(history_line)
    except Exception as e:
        print("ERROR: failed to write history.md:", repr(e))


if __name__ == "__main__":
    main()
