# scripts/tracker.py
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORT_DIR = ROOT / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def compile_patterns(patterns):
    return [re.compile(p, flags=re.IGNORECASE) for p in (patterns or [])]

def matches_any(text: str, regexes) -> bool:
    return any(r.search(text) for r in regexes)

def norm_dt(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def source_score(url: str) -> int:
    host = (urlparse(url).hostname or "").lower()
    tier3 = ("news.lenovo.com", "blogs.windows.com")
    tier2 = ("www.notebookcheck.net", "www.windowscentral.com", "www.neowin.net", "techreport.com", "laptopmedia.com")
    if any(h in host for h in tier3):
        return 3
    if any(h in host for h in tier2):
        return 2
    return 1

def to_markdown(groups):
    lines = ["# Notebook & Windows News\n"]
    for score in (3, 2, 1):
        items = groups.get(score, [])
        if not items:
            continue
        title = {3:"Notizie super (***)",2:"Notizie importanti (**)",1:"Notizie di contorno (*)"}[score]
        lines.append(f"\n## {title}\n")
        for it in items:
            date_str = it["date"][:10]
            lines.append(f"- {'★'*score} **{date_str}** — [{it['title']}]({it['link']})")
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser(description="Lenovo/Windows News Tracker (MD+JSON)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--since-days", type=int, default=14)
    ap.add_argument("--no-copy", action="store_true", help="non copiare news.json nel browser")
    ap.add_argument("--dashboard-path", default="notebook-dashboard/public/news.json")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    include_re = compile_patterns(cfg.get("include_keywords"))
    exclude_re = compile_patterns(cfg.get("exclude_keywords"))
    sources = [s["url"] for s in cfg.get("news_sources", []) if s.get("url")]

    since_dt = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    items, seen = [], set()
    for url in sources:
        feed = feedparser.parse(url)  # RSS parsing
        for e in feed.entries:
            link = e.get("link") or ""
            title = e.get("title") or ""
            text = f"{title}\n{e.get('summary','')}"
            if matches_any(text, exclude_re):
                continue
            if not matches_any(text, include_re):
                continue
            dt = norm_dt(e)
            if dt < since_dt:
                continue
            if link in seen:
                continue
            seen.add(link)
            items.append({
                "date": dt.astimezone(timezone.utc).isoformat(),
                "score": source_score(link),
                "title": title.strip(),
                "link": link,
            })

    # sort per score desc poi data desc
    items.sort(key=lambda x: (x["score"], x["date"]), reverse=True)

    # group per markdown
    grouped = {1: [], 2: [], 3: []}
    for it in items:
        grouped[it["score"]].append(it)

    # write JSON
    news_json = REPORT_DIR / "news.json"
    news_json.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    # write manifest
    manifest = {
        "mode": "LIVE",
        "since_days": args.since_days,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "count_total": len(items),
        "count_by_score": {str(k): len(v) for k, v in grouped.items()},
        "git_commit": os.environ.get("GITHUB_SHA", "")[:7],
    }
    (REPORT_DIR / "run-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # write Markdown
    md_path = REPORT_DIR / "notebook-tracking.md"
    md_path.write_text(to_markdown(grouped), encoding="utf-8")

    # copia nel browser locale
    if not args.no_copy:
        dest = (ROOT / args.dashboard_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(news_json.read_text(encoding="utf-8"), encoding="utf-8")

if __name__ == "__main__":
    main()
