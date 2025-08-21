#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import yaml

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

# --- Termini forti per binario (niente boost incrociato) ---
WINDOWS_STRONG = [
    r"(?i)\bwindows\s*11\b.*\b(24h2|major\s+update|moment|hudson\s+valley)\b",
    r"(?i)\bwindows\s*12\b.*\b(release\s+date|launch|rollout|general\s+availability|ga|rtm)\b",
]
THINKPAD_STRONG = [
    r"(?i)\bthinkpad\b",
    r"(?i)\b(t\s*-?\s*16|t16|t-?series)\b",
    r"(?i)\bgen\s?(5|6|7)\b",
    r"(?i)\b(announce|unveil|launch|availability|available)\b",
]

def compile_regex_list(patterns):
    return [re.compile(p) for p in patterns or []]

def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg or "news_sources" not in cfg:
        raise ValueError("config.yaml mancante o senza 'news_sources'.")
    return cfg

def parse_date(entry) -> dt.datetime:
    for key in ("published_parsed", "updated_parsed"):
        if getattr(entry, key, None):
            return dt.datetime(*getattr(entry, key)[:6], tzinfo=dt.timezone.utc)
    return dt.datetime.now(dt.timezone.utc)

def within_window(entry_dt_utc: dt.datetime, days: int, tz: dt.tzinfo) -> bool:
    now_utc = dt.datetime.now(dt.timezone.utc)
    delta = now_utc - entry_dt_utc
    return delta.days <= days

def text_matches(regex_list, text: str) -> int:
    return sum(1 for rx in regex_list if rx.search(text)) if text else 0

def text_matches_any(patterns, text: str) -> int:
    return sum(1 for p in (re.compile(x) for x in patterns) if p.search(text)) if text else 0

def compute_score(netloc: str, title: str, summary: str, include_rx, exclude_rx) -> int:
    blob = f"{title}\n{summary or ''}"

    if any(rx.search(blob) for rx in exclude_rx):
        return 0

    inc_hits = text_matches(include_rx, blob)
    if inc_hits == 0:
        return 0

    # Valutazione per binario (indipendente)
    win_hits = text_matches_any(WINDOWS_STRONG, blob)
    tp_hits  = text_matches_any(THINKPAD_STRONG, blob)

    # --- Regole WINDOWS ---
    win_score = 0
    if win_hits > 0:
        if netloc in OFFICIAL_DOMAINS:
            # Ufficiale + forte (bomba solo se davvero "release/major")
            if re.search(WINDOWS_STRONG[0], blob) or re.search(WINDOWS_STRONG[1], blob):
                win_score = 3
            else:
                win_score = 2
        elif netloc in RELIABLE_DOMAINS:
            win_score = 2
        else:
            win_score = 1

    # --- Regole THINKPAD ---
    tp_score = 0
    if tp_hits > 0:
        if netloc in OFFICIAL_DOMAINS and "news.lenovo.com" in netloc:
            has_model = re.search(THINKPAD_STRONG[0], blob) or re.search(THINKPAD_STRONG[1], blob)
            has_event = re.search(THINKPAD_STRONG[3], blob) or re.search(THINKPAD_STRONG[2], blob)
            if has_model and has_event:
                tp_score = 3
            else:
                tp_score = 2
        elif netloc in RELIABLE_DOMAINS:
            tp_score = 2 if tp_hits >= 1 or inc_hits >= 2 else 1
        else:
            tp_score = 1

    # Prendi solo il punteggio più alto tra i due binari (no boost combinato)
    return max(win_score, tp_score, 0)

def main():
    ap = argparse.ArgumentParser(description="Preview news/rumor Lenovo/Windows (Fase 1).")
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")), help="Path a config.yaml")
    ap.add_argument("--since-days", type=int, default=None, help="Override finestra giorni (es. 14)")
    ap.add_argument("--max", type=int, default=50, help="Limite massimo risultati mostrati (default: 50)")
    ap.add_argument(
    "--write-md",
    default=str(Path(__file__).parent.parent / "report" / "notebook-tracking.md"),
    help="Salva report in markdown (path)"
)
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
    entries_to_show = uniq[:args.max]
    for i, e in enumerate(entries_to_show, 1):
        date_str = e["date_utc"].astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
        stars = "*" * e["score"]  # <-- SOLO asterischi!
        print(f"[{stars}] {date_str} – {e['title']}")
        print(f"     Fonte: {e['source']}")
        print(f"     Link : {e['link']}")
        print("-" * 80)

    # --- Output markdown se richiesto ---
    if getattr(args, "write_md", None):
        md_path = Path(args.write_md)

        # Decidi quali voci finiscono nel report (rispetta --max)
        entries_to_write = uniq[:args.max]

        # Calcola il periodo del report per il sottotitolo
        if entries_to_write:
            date_start = min(e["date_utc"] for e in entries_to_write).astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
            date_end   = max(e["date_utc"] for e in entries_to_write).astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
        else:
            today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
            date_start = date_end = today

        # Raggruppa per punteggio
        grouped = {3: [], 2: [], 1: []}
        for e in entries_to_write:
            grouped[e["score"]].append(e)

        with md_path.open("w", encoding="utf-8") as f:
            # ---- YAML front matter (usato dal template .tex con $title$ e $subtitle$) ----
            f.write("---\n")
            f.write('title: "News e Rumor ThinkPad T16 & Windows"\n')
            f.write(f'subtitle: "Report dal {date_start} al {date_end}"\n')
            f.write("---\n\n")

            # helper per scrivere una sezione
            def write_section(score, items):
                if not items:
                    return
                # delimitatore marcato tra le sezioni
                f.write("\n---\n\n")
                header = {
                    3: "Notizie super",
                    2: "Notizie importanti",
                    1: "Notizie di contorno",
                }[score]
                f.write(f"## {header}\n\n")
                for e in items:
                    date_str = e["date_utc"].astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
                    stars = "*" * e["score"]  # solo asterischi
                    f.write(f"### [{e['title']}]({e['link']})\n")
                    f.write(f"- **Data**: {date_str}\n")
                    f.write(f"- **Fonte**: {e['source']}\n")
                    f.write(f"- **Score**: {stars}\n\n")

            # Ordine 3 → 2 → 1
            for s in (3, 2, 1):
                write_section(s, grouped[s])

            f.write("\n")
        print(f"[INFO] Markdown scritto in: {md_path}")

if __name__ == "__main__":
    main()