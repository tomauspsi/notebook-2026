import sys
import re
import datetime as dt
import requests
from bs4 import BeautifulSoup

URL = "https://www.lenovo.com/it/it/p/laptops/thinkpad/thinkpadt/thinkpad-t16-gen-4-16-inch-intel/21qe004kix"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}

TIMEOUT = 20

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def extract_inventory_message(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    # 1) target noto
    node = soup.select_one(".inventory_message")
    if node and node.get_text(strip=True):
        return node.get_text(strip=True)

    # 2) fallback
    candidates = soup.select(".inventory, .availability, [class*='inventory'], [class*='availability']")
    for c in candidates:
        txt = c.get_text(" ", strip=True)
        if txt and 5 <= len(txt) <= 160:
            return txt

    return None

def classify_status(message: str) -> str:
    m = message.lower()
    if re.search(r"\bpre.?ordine\b", m):
        return "PREORDER"
    if re.search(r"\bdisponibil", m):
        return "AVAILABLE"
    if "quasi esaurito" in m or "esaurito" in m:
        return "LOW_STOCK"
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
