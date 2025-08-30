#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notebook 2026 — Tracker (Fase 1 pre-CES)
- Nessun filtro prezzo.
- Target: rumor/news notebook business/office/scripting, display 2560x1600/QHD+,
  luminanza 300–400 nit, Wi-Fi 7 nice-to-have, fingerprint nice-to-have,
  RAM/SSD espandibili, webcam decente, pannello opaco, build solida stile ThinkPad.
- Windows: major patch 11, rumor Windows 12 (Hudson Valley / 24H2 / Copilot).
Output: public/news.json
"""

import re
import sys
import json
import time
import yaml
import hashlib
import argparse
import datetime as dt
from urllib.parse import urlparse

import feedparser
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

# ---------- Helpers

DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"

def norm_host(url: str) -> str:
    try:
        h = urlparse(url).hostname or ""
        return re.sub(r"^www\.", "", h)
    except Exception:
        return ""

def iso_date(entry) -> str:
    # prefer published_parsed, altrimenti oggi in UTC
    try:
        t = entry.get("published_parsed") or entry.get("updated_parsed")
        if t:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)
    except Exception:
        pass
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def sha_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def clamp_score(n: int) -> int:
    return 3 if n >= 3 else 2 if n == 2 else 1

def looks_like_url(s: str) -> bool:
    return bool(re.match(r"^https?://", s or ""))

# ---------- Loading config

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg

# ---------- Scoring / filters

def compile_patterns(patterns):
    return [re.compile(p, re.IGNORECASE) for p in patterns]

def any_match(text: str, regs) -> bool:
    return any(r.search(text) for r in regs)

def compute_score(title: str, summary: str, host: str, cfg: dict) -> int:
    t = f"{title} {summary}".lower()

    score = 1
    if any_match(t, cfg["_kw_positive"]):
        score = 2
    if any_match(t, cfg["_kw_strong"]):
        score = 3

    if any_match(host, cfg["_host_trusted"]):
        score += 1
    if any_match(host, cfg["_host_low"]):
        score -= 1

    score = clamp_score(score)
    return score

def extract_keywords_kwbert(model, text: str, topk: int = 5):
    if not text:
        return []
    try:
        kw = model.extract_keywords(text, top_n=topk)
        return [k for k, _ in kw]
    except Exception:
        return []

# ---------- Main

def run(config_path: str, out_json: str):
    cfg = load_config(config_path)

    # compile regex buckets
    cfg["_kw_positive"]   = compile_patterns(cfg["include_keywords_positive"])
    cfg["_kw_strong"]     = compile_patterns(cfg["include_keywords_strong"])
    cfg["_kw_exclude"]    = compile_patterns(cfg["exclude_keywords"])
    cfg["_host_trusted"]  = compile_patterns(cfg["trusted_hosts"])
    cfg["_host_low"]      = compile_patterns(cfg["low_quality_hosts"])

    feeds = cfg["feeds"]
    items = []

    # Keyword model (fast, CPU only)
    sbert = SentenceTransformer("all-MiniLM-L6-v2")
    kw_model = KeyBERT(model=sbert)

    for feed in feeds:
        url = feed["url"]
        tag = feed.get("tag", "")
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"[warn] feed error {url}: {e}", file=sys.stderr)
            continue

        for e in parsed.entries:
            title = (e.get("title") or "").strip()
            summary = (e.get("summary") or e.get("description") or "").strip()
            link = (e.get("link") or "").strip()
            host = norm_host(link)
            date_iso = iso_date(e)

            if not title or not looks_like_url(link):
                continue

            # prelim exclude
            fulltext = f"{title} {summary}"
            if any_match(fulltext, cfg["_kw_exclude"]):
                continue

            # hardware/OS gates (broad but targeted)
            gates = cfg["must_match_any"]
            if gates:
                gates_re = compile_patterns(gates)
                if not any_match(fulltext, gates_re) and not any_match(title, gates_re):
                    # allow FCC/regulatory even senza gate hardware
                    if not any_match(fulltext, cfg["_kw_strong"]):
                        continue

            score = compute_score(title, summary, host, cfg)

            # keywords (KeyBERT)
            text_for_kw = f"{title}. {summary}".strip()
            keywords = extract_keywords_kwbert(kw_model, text_for_kw, topk=5)

            # cluster (very naive: normalized title hash)
            norm = re.sub(r"\([^)]*\)", "", title.lower())
            norm = re.sub(r"\d+", "", norm)
            norm = re.sub(r"\s+", " ", norm).strip()
            cluster_id = int(sha_id(norm), 16) % 100000

            items.append({
                "id": sha_id(link),
                "date": date_iso,
                "score": score,
                "title": title,
                "link": link,
                "host": host,
                "keywords": keywords,
                "cluster_id": cluster_id,
                "tag": tag
            })

    # sort & unique by link
    seen = set()
    result = []
    for it in sorted(items, key=lambda x: ( -x["score"], x["host"], -int(x["date"].replace("-","").replace(":","").replace("T","").replace("Z","") or "0") )):
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        result.append({
            "date": it["date"],
            "score": it["score"],
            "title": it["title"],
            "link": it["link"],
            # opzionali per debug/estensioni future:
            "keywords": it["keywords"],
            "cluster_id": it["cluster_id"]
        })

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[ok] wrote {out_json} ({len(result)} items)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="public/news.json")
    args = ap.parse_args()
    run(args.config, args.out)
