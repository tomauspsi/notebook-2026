# Notebook e Windows 12 – News e Rumor Tracking

Repository per il monitoraggio periodico delle notizie su notebook Lenovo ThinkPad (generazione 2026), aggiornamenti Windows 12 e patch principali Windows 11/12.
La pipeline automatizza la raccolta e la sintesi delle notizie rilevanti in un report PDF.

---

Struttura della repository

notebook_2026/
├─ scripts/
│    ├─ tracker.py
│    ├─ config.yaml
│    └─ report-template.tex
├─ report/
│    └─ notebook-tracking.pdf
├─ .github/
│    └─ workflows/
│          └─ build-report.yml
├─ .gitignore
└─ README.md

---

Funzionamento

- Un workflow GitHub Actions avvia periodicamente lo script Python
- Lo script cerca e filtra notizie dai feed RSS e dai principali siti di riferimento (Lenovo, Microsoft, NotebookCheck, ecc.)
- Viene assegnato un punteggio a ogni notizia, che viene ordinata e inclusa nel PDF finale

---

Frequenza e output

- La pipeline viene eseguita automaticamente ogni 14 giorni
- Ogni report PDF contiene le notizie raccolte nei 14 giorni precedenti
- Il file PDF viene salvato e aggiornato nella cartella report/ con nome notebook-tracking.pdf

---

Configurazione e personalizzazione

- Tutti i parametri (parole chiave, feed RSS, filtri, finestra temporale) sono modificabili nel file scripts/config.yaml
- Il template grafico del PDF è personalizzabile in scripts/report-template.tex
- Puoi lanciare la pipeline manualmente dalla sezione Actions di GitHub

---

Requisiti locali (opzionale, per test manuali)

- Python 3.8 o superiore
- Installare i moduli necessari con pip install feedparser PyYAML
- Installare Pandoc e una distribuzione LaTeX (es. TeX Live o MiKTeX)

---

Note

- Il progetto non utilizza dati personali né API private
- Pensato per archiviazione e consultazione personale delle novità di settore
