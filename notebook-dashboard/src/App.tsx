import React from "react";

type NewsItem = { date: string; score: number; title: string; link: string };

export default function App() {
  const [items, setItems] = React.useState<NewsItem[]>([]);
  const [q, setQ] = React.useState("");
  const [minScore, setMinScore] = React.useState<number>(1);

  React.useEffect(() => {
    // Carica il JSON statico dal /public (copiato dalla pipeline)
    // fetch + response.json() per ottenere i dati
    fetch("/news.json")
      .then((r) => r.json())
      .then((data: NewsItem[]) => setItems(data))
      .catch(() => setItems([]));
  }, []);

  const filtered = items.filter((it) => {
    const okScore = it.score >= minScore;
    const okQ = q
      ? (it.title + " " + new Date(it.date).toISOString()).toLowerCase().includes(q.toLowerCase())
      : true;
    return okScore && okQ;
  });

  return (
    <div style={{ padding: 16, maxWidth: 1000, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>Notebook & Windows News</h1>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
        <input
          placeholder="Cerca titolo o data..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ padding: 8, flex: 1 }}
        />
        <label>
          Min ★
          <select value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} style={{ marginLeft: 6 }}>
            <option value={1}>★+</option>
            <option value={2}>★★+</option>
            <option value={3}>★★★</option>
          </select>
        </label>
      </div>

      <ul style={{ listStyle: "none", paddingLeft: 0 }}>
        {filtered.map((it) => (
          <li key={it.link} style={{ padding: "10px 0", borderBottom: "1px solid #ddd" }}>
            <div aria-label="score" title={`score: ${it.score}`}>{"★".repeat(it.score)}</div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>{new Date(it.date).toLocaleString()}</div>
            <a href={it.link} target="_blank" rel="noreferrer" style={{ fontWeight: 600 }}>
              {it.title}
            </a>
          </li>
        ))}
        {filtered.length === 0 && <li>Nessun risultato.</li>}
      </ul>
      <p style={{ marginTop: 24, fontSize: 12, opacity: 0.7 }}>
        Fonte: <code>/news.json</code> (copiato dall'azione). Build locale con Vite.
      </p>
    </div>
  );
}
