// notebook-dashboard/src/App.tsx
import React from "react";

type NewsItem = { date: string; score: 1|2|3; title: string; link: string };

const Score = ({ s }: { s: number }) => <span>{"★".repeat(s)}</span>;
const hostOf = (url: string) => { try { return new URL(url).hostname.replace(/^www\./,""); } catch { return ""; } };
const favUrl = (url: string) => { const h = hostOf(url); return h ? `https://icons.duckduckgo.com/ip3/${h}.ico` : ""; };

// ——— util
const useLocal = <T,>(key: string, init: T) => {
  const [v, setV] = React.useState<T>(() => {
    const raw = localStorage.getItem(key); return raw ? (JSON.parse(raw) as T) : init;
  });
  React.useEffect(() => { localStorage.setItem(key, JSON.stringify(v)); }, [key, v]);
  return [v, setV] as const;
};
const useDebounced = <T,>(value: T, ms: number) => {
  const [v, setV] = React.useState(value);
  React.useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
};
const normTitle = (t: string) =>
  t.toLowerCase().replace(/\([^)]*\)/g,"").replace(/\d+/g,"").replace(/\s+/g," ").trim();

function groupByDay(items: NewsItem[]) {
  const map = new Map<string, NewsItem[]>();
  for (const it of items) { const day = it.date.slice(0,10); if (!map.has(day)) map.set(day, []); map.get(day)!.push(it); }
  return Array.from(map.entries()).sort((a,b)=>b[0].localeCompare(a[0]));
}

export default function App() {
  const [items, setItems] = React.useState<NewsItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string|null>(null);

  const [query, setQuery] = useLocal("q", "");
  const q = useDebounced(query, 160);

  const [score, setScore] = useLocal<1|2|3|null>("exactScore", null);
  const [theme, setTheme] = useLocal<"light"|"dark">("theme", "light");
  const [collapseSimilar, setCollapseSimilar] = useLocal<boolean>("collapse", true);
  const [pinned, setPinned] = useLocal<Record<string, true>>("pinned", {}); // key: link
  const [hostFilter, setHostFilter] = useLocal<string[]>("hosts", []); // vuoto = tutte

  React.useEffect(() => { document.documentElement.setAttribute("data-theme", theme); }, [theme]);

  async function load() {
    setLoading(true); setError(null);
    try {
      const base = (import.meta as any).env.BASE_URL || "/";
      const url = (base.endsWith("/") ? base : base + "/") + "news.json";
      const r = await fetch(url, { cache: "no-store" });
      const data = (await r.json()) as NewsItem[];
      data.sort((a,b)=> (b.score-a.score) || b.date.localeCompare(a.date));
      setItems(data);
    } catch(e:any){ setError(String(e?.message||e)); } finally{ setLoading(false); }
  }
  React.useEffect(()=>{ load(); }, []);
  React.useEffect(()=>{ const t = setInterval(load, 60000); return ()=>clearInterval(t); }, []);

  // hotkeys: 1/2/3/0/r
  React.useEffect(()=>{
    const on = (e:KeyboardEvent)=>{ const k=e.key.toLowerCase();
      if(k==="1") setScore(1); else if(k==="2") setScore(2); else if(k==="3") setScore(3);
      else if(k==="0") setScore(null); else if(k==="r"){ setScore(null); setQuery(""); }
    };
    window.addEventListener("keydown", on); return ()=>window.removeEventListener("keydown", on);
  }, [setScore, setQuery]);

  // numeri per contatori stelle
  const countByScore = React.useMemo(()=>{
    const c = {1:0,2:0,3:0} as Record<1|2|3, number>;
    for(const it of items) c[it.score]++; return c;
  }, [items]);

  // filtri base
  let filtered = items
    .filter(it => (score ? it.score === score : true))
    .filter(it => it.title.toLowerCase().includes(q.toLowerCase()));

  // filtro per fonti (se selezionate)
  if (hostFilter.length) {
    filtered = filtered.filter(it => hostFilter.includes(hostOf(it.link)));
  }

  // collapse simili (per titolo normalizzato)
  if (collapseSimilar) {
    const seen = new Set<string>();
    filtered = filtered.filter(it => { const k = normTitle(it.title); if (seen.has(k)) return false; seen.add(k); return true; });
  }

  // pins in cima
  const pinnedSet = new Set(Object.keys(pinned));
  const pinnedItems = filtered.filter(it => pinnedSet.has(it.link));
  const normalItems = filtered.filter(it => !pinnedSet.has(it.link));

  const groupsPinned = groupByDay(pinnedItems);
  const groups = groupByDay(normalItems);

  // fonti rapide (5 comuni)
  const QUICK_HOSTS = [
    "blogs.windows.com",
    "news.lenovo.com",
    "www.notebookcheck.net",
    "www.windowscentral.com",
    "www.neowin.net"
  ];
  const toggleHost = (h: string) => {
    setHostFilter(h === "__all__" ? [] :
      hostFilter.includes(h) ? hostFilter.filter(x=>x!==h) : [...hostFilter, h]
    );
  };

  const mark = (text: string, ql: string) => {
    if (!ql) return text;
    const re = new RegExp(`(${ql.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\$&")})`,"ig");
    return text.split(re).map((part,i)=>
      re.test(part) ? <mark key={i}>{part}</mark> : <span key={i}>{part}</span>
    );
  };

  const copy = async (s: string) => { try { await navigator.clipboard.writeText(s); } catch {} };
  const pinToggle = (link: string) => {
    setPinned(p => { const n = {...p}; if (n[link]) delete n[link]; else n[link]=true; return n; });
  };

  return (
    <div className="app">
      <h1 style={{ margin: 0 }}>Notebook & Windows News</h1>

      {/* barra comandi */}
      <div className="toolbar">
        <div className="controls">
          <input className="search" placeholder="cerca titolo…" value={query} onChange={e=>setQuery(e.target.value)}/>
          {[1,2,3].map(s=>(
            <button key={s} className={"btn"+(score===s?" active":"")} onClick={()=>setScore(s as 1|2|3)} title={`solo ${s}★ (tasto ${s})`}>
              {"★".repeat(s)} <span style={{opacity:.7}}>({countByScore[s as 1|2|3]})</span>
            </button>
          ))}
          <button className={"btn"+(score===null?" active":"")} onClick={()=>setScore(null)} title="tutti (0)">tutti</button>
          <button className="btn reset" onClick={()=>{ setScore(null); setQuery(""); setHostFilter([]); }} title="reset (R)">reset</button>
          <button className="btn theme" onClick={()=>setTheme(theme==="light"?"dark":"light")} title="tema">
            {theme==="light"?"🌙":"☀️"}
          </button>
          <button className={"btn"+(collapseSimilar?" active":"")} onClick={()=>setCollapseSimilar(!collapseSimilar)} title="raggruppa titoli simili">
            simili {collapseSimilar?"ON":"OFF"}
          </button>
        </div>
        <div className="counter">{filtered.length} / {items.length}{loading?" · loading…":""}{error?" · errore":""}</div>
      </div>

      {/* chips fonti */}
      <div className="chips" style={{marginBottom:10}}>
        <span className={"chip"+(hostFilter.length===0?" active":"")} onClick={()=>toggleHost("__all__")}>tutte le fonti</span>
        {QUICK_HOSTS.map(h=>(
          <span key={h} className={"chip"+(hostFilter.includes(h)?" active":"")} onClick={()=>toggleHost(h)}>
            {h.replace(/^www\./,"")}
          </span>
        ))}
      </div>

      {error && <div className="card" style={{ borderColor:"#c00", color:"#c00" }}>Errore: {error}</div>}
      {loading && <><div className="skeleton"/><div className="skeleton"/><div className="skeleton"/></>}

      {/* Pinned (se presenti) */}
      {groupsPinned.length>0 && (
        <section>
          <div className="day">📌 Pinned</div>
          <div style={{display:"grid",gap:8}}>
            {groupsPinned.map(([day, rows])=>rows.map(it=>(
              <article className="card" key={"p"+it.link}>
                <div className="row" title={`${it.score}★`}><b><Score s={it.score}/></b></div>
                <div>
                  <div className="row" style={{marginBottom:4}}>
                    <img className="fav" src={favUrl(it.link)} alt=""/>
                    <a href={it.link} target="_blank" rel="noreferrer">{mark(it.title, q)}</a>
                  </div>
                  <div className="meta">{day} · {hostOf(it.link)}</div>
                </div>
                <div className="actions">
                  <button className={"iconbtn pin active"} onClick={()=>pinToggle(it.link)} title="unpin">📌</button>
                  <button className="iconbtn" onClick={()=>copy(it.link)} title="copia link">🔗</button>
                  <button className="iconbtn" onClick={()=>copy(`${it.title} — ${it.link}`)} title="copia titolo+link">📝</button>
                </div>
              </article>
            )))}
          </div>
        </section>
      )}

      {/* Lista normale */}
      {!loading && groups.map(([day, rows])=>(
        <section key={day}>
          <div className="day">{day}</div>
          <div style={{display:"grid",gap:8}}>
            {rows.map(it=>(
              <article className="card" key={it.link}>
                <div className="row" title={`${it.score}★`}><b><Score s={it.score}/></b></div>
                <div>
                  <div className="row" style={{marginBottom:4}}>
                    <img className="fav" src={favUrl(it.link)} alt=""/>
                    <a href={it.link} target="_blank" rel="noreferrer">{mark(it.title, q)}</a>
                  </div>
                  <div className="meta">{hostOf(it.link)}</div>
                </div>
                <div className="actions">
                  <button className={"iconbtn pin"+(pinned[it.link]?" active":"")} onClick={()=>pinToggle(it.link)} title="pin/unpin">📌</button>
                  <button className="iconbtn" onClick={()=>copy(it.link)} title="copia link">🔗</button>
                  <button className="iconbtn" onClick={()=>copy(`${it.title} — ${it.link}`)} title="copia titolo+link">📝</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
