from datetime import date

# Parametri fittizi
data_inizio = "2025-08-01"
data_fine   = date.today().strftime("%Y-%m-%d")
filename    = "report/notebook-tracking.md"

markdown = f"""---
title: "News e Rumor ThinkPad T16 & Windows"
subtitle: "Report dal {data_inizio} al {data_fine}"
---

## Announcing Windows 11 Insider Preview Build 27928 (Canary Channel)
- **Data**: 2025-08-20
- **Fonte**: blogs.windows.com
- **Score**: ***

## Announcing Windows 11 Insider Preview Build 26200.5751 (Dev Channel)
- **Data**: 2025-08-15
- **Fonte**: blogs.windows.com
- **Score**: ***

## Announcing Windows 11 Insider Preview Build 26120.5751 (Beta Channel)
- **Data**: 2025-08-15
- **Fonte**: blogs.windows.com
- **Score**: ***
"""

with open(filename, "w", encoding="utf-8") as f:
    f.write(markdown)

print(f"Markdown scritto in: {filename}")