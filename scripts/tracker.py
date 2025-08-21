#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fase 1 – SOLO NEWS/RUMOR (no prezzi, no file output):
- Legge 'config.yaml'
- Scarica feed RSS/Atom dalle fonti
- Applica filtri include/exclude (regex, case-insensitive)
- Assegna punteggio 0/1/2/3
- Mostra una preview in console ordinata per data (desc) e score (desc)

Punteggio:
  3 = UFFICIALE (Lenovo Newsroom, Windows Blog) + match forte
  2 = Rumor/News forti (Notebookcheck, WindowsCentral, HDBlog, Neowin, TechReport, Slashdot) + match sufficiente
  1 = Match debole / tangenziale (una sola keyword forte o contesto poco centrato)
  0 = irrilevante / escluso

Avvio:
  python scripts/tracker.py --config scripts/config.yaml
Opzioni:
  --since-days N   (override della finestra temporale)
  --max N          (limite risultati mostrati in console)
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import yaml

# -----------------------
# Helpers & Config
# -----------------------

OFFICIAL_DOMAINS = {
    "news.lenovo.com",
    "blogs.windows.com",
}

RELIABLE_DOMAINS = {
    "www.notebookcheck.net",
    "www.windowscentral.com",
    "www.hdblog.it",
    "www.neowin.net",
    "techreport.com",
    "slashdot.org",
}

# Subset di parole/regex considerate "forti" per scoring
STRONG_TERMS = [
    r"(?i)\bthinkpad\b",
    r"(?i)\bwindows\s*12\b",
    r"(?i)\bwindows\s*11\b",
    r"(?i)\bmajor\s+update\b|\bpatch\b|\baggiornamento\b|\b24h2\b|\bhudson\s+valley\b",
]

def compile_regex_list(patterns):
    out = []
    for p in patterns or []:
        out.append(re.compile(p))
    return out

def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg or "news_sources" not in cfg:
        raise ValueError("config.yaml mancante o senza 'news_sources'.")
    return cfg

def parse_date(entry) -> dt.datetime:
    # Prova diversi campi data presenti nei feed
    for key in ("published_parsed", "updated_parsed"):
        if getattr(entry, key, None):
            return dt.datetime(*getattr(entry, key)[:6], tzinfo=dt.timezone.utc)
    # Fallback: ora
    return dt.datetime.now(dt.timezone.utc)

def within_window(entry_dt_utc: dt.datetime, days: int, tz: dt.tzinfo) -> bool:
    now_utc = dt.datetime.now(dt.timezone.utc)
    delta = now_utc - entry_dt_utc
    return delta.days <= days

def source_base_score(netloc: str) -> int:
    if netloc in OFFICIAL_DOMAINS:
        return 3
    if netloc in RELIABLE_DOMAINS:
        return 2
    return 1  # default prudente

def text_matches(regex_list, text: str) -> int:
    """Restituisce il numero di pattern che matchano nel testo."""
    if not text:
        return 0
    count = 0
    for rx in regex_list:
        if rx.search(text):
            count += 1
    return count

def compute_score(netloc: str, title: str, summary: str, include_rx, exclude_rx) -> int:
    blob = f"{title}\n{summary or ''}"
    # Esclusioni hard
    if any(rx.search(blob) for rx in exclude_rx):
        return 0

    inc_hits = text_matches(include_rx, blob)
    strong_hits = text_matches([re.compile(p) for p in STRONG_TERMS], blob)

    base = source_base_score(netloc)

    # Logica semplice e leggibile:
    # - zero match = 0 (irrilevante)
    if inc_hits == 0 and strong_hits == 0:
        return 0

    # Official con match forte = 3
    if netloc in OFFICIAL_DOMAINS and strong_hits >= 1:
        return 3

    # Fonti affidabili con >=2 match (o 1 strong) = 2
    if netloc in RELIABLE_DOMAINS and (inc_hits >= 2 or strong_hits >= 1):
        return 2

    # Qualsiasi altra fonte con almeno 1 match = 1
    return 1

# -----------------------
# Main
# -----------------------

def main():
    ap = argparse.ArgumentParser(description="Preview news/rumor Lenovo/Windows (Fase 1).")
    ap.add_argument("--config", default="scripts/config.yaml", help="Path a config.yaml")
    ap.add_argument("--since-days", type=int, default=None, help="Override finestra giorni (es. 14)")
    ap.add_argument("--max", type=int, default=50, help="Limite risultati mostrati")
    ap.add_argument("--write-md", default=None, help="Salva report in markdown (path)")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    meta = cfg.get("meta", {})
    window_days = args.since_days or meta.get("window_days", 14)

    include_rx = compile_regex_list(cfg.get("include_keywords", []))
    exclude_rx = compile_regex_list(cfg.get("exclude_keywords", []))

    entries = []

    for src in cfg.get("news_sources", []):
        url = src.get("url")
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[WARN] Impossibile leggere il feed: {url} – {e}", file=sys.stderr)
            continue

        for item in feed.entries:
            title = getattr(item, "title", "").strip()
            link = getattr(item, "link", "").strip()
            summary = getattr(item, "summary", "") or getattr(item, "description", "") or ""
            if not title or not link:
                continue

            dt_utc = parse_date(item)
            if not within_window(dt_utc, window_days, dt.timezone.utc):
                continue

            netloc = urlparse(link).netloc
            score = compute_score(netloc, title, summary, include_rx, exclude_rx)
            if score == 0:
                continue

            entries.append({
                "score": score,
                "date_utc": dt_utc,
                "title": title,
                "link": link,
                "source": netloc,
            })

    # De-dup per link
    seen = set()
    uniq = []
    for e in entries:
        if e["link"] in seen:
            continue
        seen.add(e["link"])
        uniq.append(e)

    # Ordina: score desc, data desc
    uniq.sort(key=lambda x: (x["score"], x["date_utc"]), reverse=True)

    # Stampa preview console
    if not uniq:
        print("Nessun risultato nella finestra selezionata.")
        return

    print(f"=== Preview news/rumor (ultimi {window_days} giorni) ===")
    for i, e in enumerate(uniq[: args.max], 1):
        date_str = e["date_utc"].astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
        print(f"[{e['score']}] {date_str} – {e['title']}")
        print(f"     Fonte: {e['source']}")
        print(f"     Link : {e['link']}")
        if i < min(len(uniq), args.max):
            print("-" * 80)
          
    # --- Output markdown se richiesto ---
    if getattr(args, "write_md", None):
        md_path = Path(args.write_md)
        with md_path.open("w", encoding="utf-8") as f:
            f.write(f"# News e Rumor ThinkPad T16 & Windows (ultimi {window_days} giorni)\n\n")
            for e in uniq[: args.max]:
                date_str = e["date_utc"].astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
                score_str = "*" * e["score"] 
                f.write(f"## [{e['title']}]({e['link']})\n")
                f.write(f"- **Data**: {date_str}\n")
                f.write(f"- **Fonte**: {e['source']}\n")
                f.write(f"- **Score**: {score_str}\n\n")
            f.write("\n\n")
        print(f"[INFO] Markdown scritto in: {md_path}")

if __name__ == "__main__":
    main()
