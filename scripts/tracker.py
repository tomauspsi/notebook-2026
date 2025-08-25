# scripts/tracker.py
# News tracker: RSS -> filter -> score -> MD/JSON + manifest (+ copy to dashboard)
# deps: feedparser, PyYAML

from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional
import feedparser  # type: ignore
import yaml        # type: ignore

# --------------------------
# utils
# --------------------------

def utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def to_date_yyyy_mm_dd(entry: Any) -> str:
    # prova published_parsed -> updated_parsed -> now UTC
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None)
        if t:
            try:
                return dt.datetime(*t[:6], tzinfo=dt.timezone.utc).date().isoformat()
            except Exception:
                pass
    return dt.datetime.now(dt.timezone.utc).date().isoformat()

def hostname(url: str) -> str:
    try:
        from urllib.parse import urlparse
        h = urlparse(url).hostname or ""
        return h.lower()
    except Exception:
        return ""

def short_git_sha() -> str:
    # preferisci GITHUB_SHA in CI
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:7]
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return ""

def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

# --------------------------
# data types
# --------------------------

@dataclass
class Item:
    date: str
    score: int
    title: str
    link: str
    host: str

# --------------------------
# config
# --------------------------

@dataclass
class Config:
    include_patterns: List[re.Pattern]
    exclude_patterns: List[re.Pattern]
    sources: List[str]
    domain_blocklist: List[str]
    exclude_cjk: bool
    window_days: int

CJK_RE = re.compile(r"[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]")

def compile_patterns(patterns: Iterable[str]) -> List[re.Pattern]:
    out = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error:
            # ignora pattern rotti
            pass
    return out

def load_config(path: Path) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    include = compile_patterns(raw.get("include_keywords", []))
    exclude = compile_patterns(raw.get("exclude_keywords", []))
    sources = [s.get("url") if isinstance(s, dict) else str(s) for s in raw.get("news_sources", [])]
    block = [d.lower() for d in raw.get("domain_blocklist", [])]
    exclude_cjk = bool(raw.get("exclude_cjk", False))
    window_days = int((raw.get("meta", {}) or {}).get("window_days", 14))

    return Config(
        include_patterns=include,
        exclude_patterns=exclude,
        sources=sources,
        domain_blocklist=block,
        exclude_cjk=exclude_cjk,
        window_days=window_days,
    )

# --------------------------
# core
# --------------------------

HIGH_SOURCES = {
    "blogs.windows.com",  # Microsoft
    "news.lenovo.com",    # Lenovo
}
MID_SOURCES = {
    "www.notebookcheck.net",
    "notebookcheck.net",
    "www.windowscentral.com",
    "windowscentral.com",
    "www.neowin.net",
    "neowin.net",
    "techreport.com",
    "slashdot.org",
    "laptopmedia.com",
}

def score_for_host(h: str) -> int:
    if h in HIGH_SOURCES:
        return 3
    if h in MID_SOURCES:
        return 2
    return 1

def matches_any(patterns: List[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in patterns)

def fetch_feed(url: str) -> List[Any]:
    parsed = feedparser.parse(url)
    return list(parsed.entries or [])

def unique_by_link(items: List[Item]) -> List[Item]:
    best: Dict[str, Item] = {}
    for it in items:
        if it.link not in best or it.score > best[it.link].score:
            best[it.link] = it
    return list(best.values())

def within_window(date_str: str, since_days: int) -> bool:
    try:
        d = dt.date.fromisoformat(date_str)
    except Exception:
        return True
    return d >= (dt.date.today() - dt.timedelta(days=since_days))

def normalize_title(t: str) -> str:
    return t.strip()

# --------------------------
# pipeline
# --------------------------

def run_pipeline(cfg: Config, since_days: int) -> List[Item]:
    collected: List[Item] = []

    for url in cfg.sources:
        try:
            entries = fetch_feed(url)
        except Exception:
            entries = []
        for e in entries:
            title = normalize_title(getattr(e, "title", "") or "")
            link = getattr(e, "link", "") or ""
            if not title or not link:
                continue

            h = hostname(link)

            # blocklist dominio
            if h in cfg.domain_blocklist:
                continue

            # lingua cinese/giapponese/coreano (se richiesto)
            if cfg.exclude_cjk and CJK_RE.search(title):
                continue

            # filtro include/exclude
            text = title  # puoi estendere a summary se vuoi
            if cfg.exclude_patterns and matches_any(cfg.exclude_patterns, text):
                continue
            if cfg.include_patterns and not matches_any(cfg.include_patterns, text):
                continue

            date = to_date_yyyy_mm_dd(e)
            if not within_window(date, since_days):
                continue

            s = score_for_host(h)
            collected.append(Item(date=date, score=s, title=title, link=link, host=h))

    # dedup + sort
    deduped = unique_by_link(collected)
    deduped.sort(key=lambda x: (x.score, x.date, x.title), reverse=True)
    return deduped

# --------------------------
# outputs
# --------------------------

def write_markdown(items: List[Item], out_path: Path) -> None:
    ensure_dir(out_path)
    # gruppi per score
    g3 = [it for it in items if it.score == 3]
    g2 = [it for it in items if it.score == 2]
    g1 = [it for it in items if it.score == 1]

    def render(group: List[Item]) -> str:
        lines = []
        for it in group:
            stars = "★" * it.score
            lines.append(f"- {stars} **{it.date}** — [{it.title}]({it.link})")
        return "\n".join(lines)

    md = [
        "# Notebook & Windows News",
        "",
        "## Notizie super (***)",
        "",
        render(g3),
        "",
        "## Notizie importanti (**)",
        "",
        render(g2),
        "",
        "## Notizie di contorno (*)",
        "",
        render(g1),
        "",
    ]
    out_path.write_text("\n".join(md), encoding="utf-8")

def write_json(items: List[Item], out_path: Path) -> None:
    ensure_dir(out_path)
    data = [dict(date=it.date, score=it.score, title=it.title, link=it.link) for it in items]
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def write_manifest(items: List[Item], since_days: int, out_path: Path) -> None:
    ensure_dir(out_path)
    by = {"1": 0, "2": 0, "3": 0}
    for it in items:
        by[str(it.score)] += 1
    manifest = {
        "mode": "LIVE",
        "since_days": since_days,
        "generated_utc": utcnow_iso(),
        "count_total": len(items),
        "count_by_score": by,
        "git_commit": short_git_sha(),
    }
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# --------------------------
# cli
# --------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Lenovo/Windows news tracker")
    ap.add_argument("--config", required=True, help="Percorso file YAML config")
    ap.add_argument("--since-days", type=int, default=14, help="Finestra temporale (giorni)")
    ap.add_argument("--no-pdf", action="store_true", help="Ignora generazione PDF (placeholder, non usato)")
    ap.add_argument("--no-copy", action="store_true", help="Non copiare news.json nel dashboard")
    ap.add_argument("--dashboard-path", default="notebook-dashboard/public/news.json",
                    help="Dove copiare news.json per il browser")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    cfg = load_config(Path(args.config))

    since_days = int(args.since_days or cfg.window_days)
    print(f"[tracker] fetching {len(cfg.sources)} feed(s), window={since_days}d")

    items = run_pipeline(cfg, since_days=since_days)
    print(f"[tracker] items kept: {len(items)}")

    # output paths
    report_dir = Path("report")
    md_path = report_dir / "notebook-tracking.md"
    json_path = report_dir / "news.json"
    manifest_path = report_dir / "run-manifest.json"

    write_markdown(items, md_path)
    write_json(items, json_path)
    write_manifest(items, since_days, manifest_path)

    print(f"[tracker] wrote: {md_path}, {json_path}, {manifest_path}")

    # optional copy to dashboard
    if not args.no_copy:
        dst = Path(args.dashboard_path)
        ensure_dir(dst)
        try:
            dst.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"[tracker] copied news.json -> {dst}")
        except Exception as e:
            print(f"[tracker] copy failed: {e}", file=sys.stderr)

    # PDF non gestito (placeholder per compatibilità flag)
    if args.no_pdf:
        print("[tracker] --no-pdf: skipping PDF (not implemented)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[tracker] aborted by user", file=sys.stderr)
        sys.exit(130)
