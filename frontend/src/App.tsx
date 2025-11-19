import { useEffect, useMemo, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import './App.css'
import type { CatalogItem, DashboardStats, GraphData, GraphResponse, StatusPayload } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type View = 'dashboard' | 'search' | 'theory' | 'graph' | 'papers' | 'repos' | 'ingestion'

const palettes = {
  bg: '#0f172a',
  panel: '#182235',
  accent: '#f3ae2c',
  text: '#e8edf5',
  subtle: '#9fb1d1',
}

const kindColor = (k: string) => (k === 'paper' ? '#50c4f5' : '#9f71ff')

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${path} failed`)
  return res.json()
}

function StatusBar({ status }: { status: StatusPayload[] }) {
  return (
    <div className="status-bar">
      {status.length === 0 ? (
        <span className="muted">Idle — start cataloguing to fill the graph.</span>
      ) : (
        status.map((s) => (
          <span key={s.mode}>
            <strong>{s.mode}</strong>: {s.message}
          </span>
        ))
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
    </div>
  )
}

function ItemCard({ item }: { item: CatalogItem }) {
  return (
    <article className="item-card">
      <div className="item-meta">
        <span className="pill" style={{ background: kindColor(item.kind) }}>
          {item.kind}
        </span>
        <a href={item.source_url} target="_blank" rel="noreferrer">
          open
        </a>
      </div>
      <h3>{item.title}</h3>
      <p className="muted">{item.analysis.summary}</p>
      <div className="tag-row">
        {item.analysis.tags.slice(0, 5).map((t) => (
          <span key={t.tag} className="tag">
            {t.tag}
          </span>
        ))}
      </div>
      <div className="score-row">
        <span>Relevance {item.analysis.relevance_score.toFixed(1)}/10</span>
        <span>Interesting {item.analysis.interesting_score.toFixed(1)}/10</span>
      </div>
    </article>
  )
}

function Dashboard({
  stats,
  onStart,
  onStop,
}: {
  stats: DashboardStats | null
  onStart: (kind: 'paper' | 'repo') => void
  onStop: (kind: 'paper' | 'repo') => void
}) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Dashboard</h2>
          <p className="muted">
            High level signal of how full the catalog is. Use the controls to
            keep ingestion running.
          </p>
        </div>
        <div className="actions">
          <button onClick={() => onStart('paper')}>Start papers</button>
          <button onClick={() => onStart('repo')}>Start repos</button>
          <button className="ghost" onClick={() => onStop('paper')}>
            Stop all
          </button>
        </div>
      </div>
      <div className="metric-grid">
        <Metric label="Total items" value={stats?.total_items ?? 0} />
        <Metric label="Papers" value={stats?.papers ?? 0} />
        <Metric label="Repositories" value={stats?.repos ?? 0} />
        <Metric
          label="Avg relevance"
          value={(stats?.avg_relevance ?? 0).toFixed(2)}
        />
        <Metric
          label="Avg interesting"
          value={(stats?.avg_interesting ?? 0).toFixed(2)}
        />
        <Metric
          label="Last ingested"
          value={stats?.last_ingested ? stats.last_ingested.slice(0, 19) : '—'}
        />
      </div>
    </div>
  )
}

function SearchView() {
  const [query, setQuery] = useState('agentic research')
  const [results, setResults] = useState<CatalogItem[]>([])
  const [loading, setLoading] = useState(false)

  const runSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const payload = { query, limit: 10 }
      const data = await api<CatalogItem[]>('/search', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setResults(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    runSearch().catch(console.error)
  }, [])

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Search</h2>
          <p className="muted">
            Query the catalog for papers and repositories. Results are ranked by
            semantic similarity and tags.
          </p>
        </div>
        <div className="search-box">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for?"
          />
          <button onClick={runSearch} disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
      </div>
      <div className="grid">
        {results.map((item) => (
          <ItemCard key={item.id} item={item} />
        ))}
        {!loading && results.length === 0 && (
          <p className="muted">No matches yet. Start cataloguing mode.</p>
        )}
      </div>
    </div>
  )
}

function TheoryView() {
  const [theory, setTheory] = useState('LLMs enable autonomous research agents')
  const [support, setSupport] = useState<CatalogItem[]>([])
  const [oppose, setOppose] = useState<CatalogItem[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const runTheory = async () => {
    setLoading(true)
    try {
      const data = await api<{
        support: CatalogItem[]
        oppose: CatalogItem[]
        suggestions: string[]
      }>('/theory', {
        method: 'POST',
        body: JSON.stringify({ theory }),
      })
      setSupport(data.support)
      setOppose(data.oppose)
      setSuggestions(data.suggestions)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Theory Mode</h2>
          <p className="muted">
            Enter a hypothesis; we surface supporting and opposing evidence.
          </p>
        </div>
        <div className="search-box">
          <input
            value={theory}
            onChange={(e) => setTheory(e.target.value)}
            placeholder="Your theory or question"
          />
          <button onClick={runTheory} disabled={loading}>
            {loading ? 'Analyzing…' : 'Run'}
          </button>
        </div>
      </div>
      <div className="two-col">
        <div>
          <h4>Support ({support.length})</h4>
          <div className="stack">
            {support.map((i) => (
              <ItemCard key={i.id} item={i} />
            ))}
          </div>
        </div>
        <div>
          <h4>Oppose ({oppose.length})</h4>
          <div className="stack">
            {oppose.map((i) => (
              <ItemCard key={i.id} item={i} />
            ))}
          </div>
        </div>
      </div>
      {suggestions.length > 0 && (
        <div className="suggestions">
          <h4>Try next</h4>
          <ul>
            {suggestions.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function GraphView() {
  const [graph, setGraph] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(false)

  const loadGraph = async () => {
    setLoading(true)
    try {
      const data = await api<GraphResponse>('/graph')
      setGraph(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadGraph().catch(console.error)
  }, [])

  const fgData = useMemo(() => {
    if (!graph) return { nodes: [], links: [] }
    return {
      nodes: graph.nodes.map((n) => ({
        id: n.id,
        name: n.title,
        kind: n.kind,
        val: n.score,
      })),
      links: graph.edges.map((e) => ({ source: e.source, target: e.target, value: e.weight })),
    }
  }, [graph])

  return (
    <div className="panel graph-panel">
      <div className="panel-head">
        <div>
          <h2>Graph View</h2>
          <p className="muted">
            Visual clusters of related papers and repos (based on cosine
            similarity).
          </p>
        </div>
        <button onClick={loadGraph} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      <div className="graph">
        <ForceGraph2D
          graphData={fgData}
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.name.slice(0, 60)
            const fontSize = 10 / globalScale
            ctx.fillStyle = palettes.text
            ctx.font = `${fontSize}px 'Space Grotesk'`
            ctx.fillText(label, node.x + 6, node.y + 4)
          }}
          nodeRelSize={6}
          nodeLabel={(n: any) => n.name}
          nodeColor={(n: any) => kindColor(n.kind)}
          linkColor={() => '#334155'}
          backgroundColor={palettes.panel}
        />
      </div>
    </div>
  )
}

function ListView({
  kind,
}: {
  kind: 'paper' | 'repo'
}) {
  const [items, setItems] = useState<CatalogItem[]>([])
  const [selected, setSelected] = useState<CatalogItem | null>(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const data = await api<CatalogItem[]>(`/items?kind=${kind}`)
      setItems(data)
      if (selected) {
        const updated = data.find((i) => i.id === selected.id)
        setSelected(updated ?? null)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load().catch(console.error)
  }, [kind])

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>{kind === 'paper' ? 'Papers' : 'Repositories'}</h2>
          <p className="muted">All ingested {kind === 'paper' ? 'papers' : 'repositories'}.</p>
        </div>
        <button onClick={load} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
      <div className="two-col">
        <div className="stack list-scroll">
          {items.map((i) => (
            <button
              key={i.id}
              className={`list-row ${selected?.id === i.id ? 'active' : ''}`}
              onClick={() => setSelected(i)}
            >
              <span className="pill" style={{ background: kindColor(i.kind) }}>
                {i.kind}
              </span>
              <span className="list-title">{i.title}</span>
            </button>
          ))}
          {!loading && items.length === 0 && <p className="muted">No items yet.</p>}
        </div>
        <div>
          {selected ? (
            <ItemCard item={selected} />
          ) : (
            <p className="muted">Select an item to view details.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function IngestionView({ status }: { status: StatusPayload[] }) {
  const [history, setHistory] = useState<StatusPayload[]>([])

  const load = async () => {
    const data = await api<StatusPayload[]>('/ingestion/history?limit=100')
    setHistory(data)
  }

  useEffect(() => {
    load().catch(console.error)
  }, [])

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Ingestion</h2>
          <p className="muted">Live state plus recent events.</p>
        </div>
        <button onClick={load}>Refresh history</button>
      </div>
      <h4>Current</h4>
      {status.length === 0 ? (
        <p className="muted">Idle</p>
      ) : (
        <div className="stack">
          {status.map((s) => (
            <div key={s.timestamp} className="history-card">
              <strong>{s.mode}</strong> — {s.message} ({new Date(s.timestamp).toLocaleTimeString()})
            </div>
          ))}
        </div>
      )}
      <h4>History</h4>
      <div className="stack list-scroll">
        {history.map((h, idx) => (
          <div key={`${h.timestamp}-${idx}`} className="history-card">
            <strong>{h.mode}</strong> — {h.message}{' '}
            <span className="muted">{new Date(h.timestamp).toLocaleString()}</span>
          </div>
        ))}
        {history.length === 0 && <p className="muted">No history recorded yet.</p>}
      </div>
    </div>
  )
}

function App() {
  const [view, setView] = useState<View>('dashboard')
  const [status, setStatus] = useState<StatusPayload[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)

  const refresh = async () => {
    try {
      const [s, d] = await Promise.all([
        api<StatusPayload[]>('/status').catch(() => []),
        api<DashboardStats>('/dashboard').catch(() => null),
      ])
      setStatus(s)
      if (d) setStats(d)
    } catch (err) {
      console.error(err)
    }
  }

  const start = async (kind: 'paper' | 'repo') => {
    await api(`/ingest/${kind}/start`, { method: 'POST' })
    refresh()
  }
  const stop = async (_kind: 'paper' | 'repo') => {
    await api(`/ingest/${_kind}/stop`, { method: 'POST' })
    refresh()
  }

  useEffect(() => {
    refresh().catch(console.error)
    const id = setInterval(refresh, 8000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="app">
      <header>
        <div>
          <p className="eyebrow">AI Research Catalog</p>
          <h1>Graph-first explorer for papers & repositories</h1>
          <p className="muted">
            Runs cataloguing loops, summarizes with GPT-5 via LiteLLM, and lets
            you triangulate support or criticism for your theories.
          </p>
        </div>
        <nav>
          {(['dashboard', 'search', 'theory', 'graph', 'papers', 'repos', 'ingestion'] as View[]).map((v) => (
            <button
              key={v}
              className={view === v ? 'active' : 'ghost'}
              onClick={() => setView(v)}
            >
              {v}
            </button>
          ))}
        </nav>
      </header>

      <StatusBar status={status} />

      {view === 'dashboard' && (
        <Dashboard stats={stats} onStart={start} onStop={stop} />
      )}
      {view === 'search' && <SearchView />}
      {view === 'theory' && <TheoryView />}
      {view === 'graph' && <GraphView />}
      {view === 'papers' && <ListView kind="paper" />}
      {view === 'repos' && <ListView kind="repo" />}
      {view === 'ingestion' && <IngestionView status={status} />}
    </div>
  )
}

export default App
