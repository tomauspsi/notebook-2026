import sys
import re
import json
import datetime as dt
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
    # Cerca availability nello schema.org/Offer
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue

        # Normalizza: a volte è un dict, altre una lista
        candidates = []
        if isinstance(data, dict):
            candidates = [data]
        elif isinstance(data, list):
            candidates = data

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

    # 1) Selettore noto (se mai presente in SSR)
    node = soup.select_one(".inventory_message")
    if node and node.get_text(strip=True):
        return node.get_text(strip=True)

    # 2) JSON-LD availability (schema.org)
    avail = from_json_ld(soup)
    if avail:
        return avail  # es. "http://schema.org/InStock", "http://schema.org/PreOrder", "http://schema.org/OutOfStock"

    # 3) Heuristics su classi affini
    candidates = soup.select(".inventory, .availability, [class*='inventory'], [class*='availability']")
    for c in candidates:
        txt = c.get_text(" ", strip=True)
        if txt and 5 <= len(txt) <= 200:
            return txt

    # 4) Regex sulle parole chiave direttamente nell'HTML (ultima spiaggia)
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

def main():
    print("=== Lenovo T16 Availability Check ===")
    print("Timestamp (UTC):", dt.datetime.now(dt.UTC).isoformat())
    print("URL:", URL)

    try:
        html = fetch_html(URL)
    except Exception as e:
        print("ERROR: failed to fetch page:", repr(e))
        sys.exit(0)

    msg = extract_inventory_message(html)
    if not msg:
        print("WARNING: inventory message not found.")
        sys.exit(0)

    status = classify_status(msg)
    print("Inventory message:", msg)
    print("Parsed status:", status)

if __name__ == "__main__":
    main()


def main():
    print("=== Lenovo T16 Availability Check ===")
    timestamp = dt.datetime.now(dt.UTC).isoformat()
    print("Timestamp (UTC):", timestamp)
    print("URL:", URL)

    try:
        html = fetch_html(URL)
    except Exception as e:
        print("ERROR: failed to fetch page:", repr(e))
        sys.exit(0)

    msg = extract_inventory_message(html)
    if not msg:
        print("WARNING: inventory message not found.")
        sys.exit(0)

    status = classify_status(msg)
    print("Inventory message:", msg)
    print("Parsed status:", status)

    # Append result to history.md
    history_line = f"| {timestamp} | {status} | {msg} |\n"
    header = "| Timestamp (UTC) | Status | Message |\n|---|---|---|\n"
    try:
        # If file doesn't exist, create it with header
        with open("history.md", "a+", encoding="utf-8") as f:
            f.seek(0)
            if not f.read().strip():
                f.write(header)
            f.write(history_line)
    except Exception as e:
        print("ERROR: failed to write history.md:", repr(e))
