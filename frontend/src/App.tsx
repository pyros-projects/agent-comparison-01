import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import './App.css'

const API_BASE = '/api'

type Kind = 'paper' | 'repo'

interface IngestStatus {
  running: boolean
  last_error: string | null
  last_message: string | null
}

interface Stats {
  total_nodes: number
  papers: number
  repositories: number
}

interface StatusResponse {
  ingest: {
    papers: IngestStatus
    repositories: IngestStatus
  }
  stats: Stats
}

interface SearchResultItem {
  id: string
  kind: Kind
  title: string
  source_url: string
  summary: string
  tags: string[]
  questions_answered: string[]
  key_findings: string[]
  real_world_relevancy: number
  interestingness: number
  score: number
}

interface SearchResponse {
  query: string
  results: SearchResultItem[]
}

interface TheoryItem {
  id: string
  kind: Kind
  title: string
  source_url: string
  summary: string
  stance: 'agree' | 'disagree' | 'uncertain'
  score: number
}

interface TheoryResponse {
  theory: string
  totals: {
    agree: number
    disagree: number
    uncertain: number
  }
  items: TheoryItem[]
  suggestions: string[]
}

interface GraphNode {
  id: string
  kind: Kind
  title: string
  source_url: string
  real_world_relevancy: number
  interestingness: number
}

interface GraphEdge {
  source: string
  target: string
  weight: number
}

interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface AnalyzeNode {
  id: string
  kind: Kind
  title: string
  source_url: string
  summary: string
  tags: string[]
  questions_answered: string[]
  key_findings: string[]
  real_world_relevancy: number
  interestingness: number
}

interface AnalyzeSimilarItem {
  id: string
  kind: Kind
  title: string
  source_url: string
  summary: string
  score: number
}

interface AnalyzeResponse {
  node: AnalyzeNode
  similar: AnalyzeSimilarItem[]
}

type TabKey = 'dashboard' | 'search' | 'theory' | 'graph'

function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)

  const papersRunning = status?.ingest.papers.running ?? false
  const reposRunning = status?.ingest.repositories.running ?? false

  useEffect(() => {
    let cancelled = false

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/status`)
        if (!res.ok) throw new Error(await res.text())
        const data: StatusResponse = await res.json()
        if (!cancelled) {
          setStatus(data)
          setStatusError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setStatusError('Backend unavailable or misconfigured')
        }
      }
    }

    fetchStatus()
    const id = setInterval(fetchStatus, 5000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const handleCatalogToggle = async (
    target: 'papers' | 'repos',
    action: 'start' | 'stop',
  ) => {
    try {
      await fetch(`${API_BASE}/catalog/${target}/${action}`, {
        method: 'POST',
      })
      const res = await fetch(`${API_BASE}/status`)
      if (res.ok) {
        const data: StatusResponse = await res.json()
        setStatus(data)
      }
    } catch (err) {
      // Surface via status bar only
      setStatusError('Failed to update cataloguing mode')
    }
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <div>
          <h1 className="app-title">AI Research Catalog</h1>
          <p className="app-subtitle">
            Discover, cluster, and reason over AI papers and repositories.
          </p>
        </div>
        <div className="app-controls">
          <button
            className={`btn ${
              papersRunning ? 'btn-primary' : 'btn-secondary'
            }`}
            onClick={() => handleCatalogToggle('papers', 'start')}
          >
            Start papers
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => handleCatalogToggle('papers', 'stop')}
          >
            Stop papers
          </button>
          <span className="divider" />
          <button
            className={`btn ${
              reposRunning ? 'btn-primary' : 'btn-secondary'
            }`}
            onClick={() => handleCatalogToggle('repos', 'start')}
          >
            Start repos
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => handleCatalogToggle('repos', 'stop')}
          >
            Stop repos
          </button>
        </div>
      </header>

      <nav className="app-tabs">
        <TabButton
          label="Dashboard"
          tabKey="dashboard"
          activeTab={activeTab}
          onClick={setActiveTab}
        />
        <TabButton
          label="Search"
          tabKey="search"
          activeTab={activeTab}
          onClick={setActiveTab}
        />
        <TabButton
          label="Theory"
          tabKey="theory"
          activeTab={activeTab}
          onClick={setActiveTab}
        />
        <TabButton
          label="Graph"
          tabKey="graph"
          activeTab={activeTab}
          onClick={setActiveTab}
        />
      </nav>

      <main className="app-main">
        {activeTab === 'dashboard' && <DashboardView status={status} />}
        {activeTab === 'search' && <SearchView />}
        {activeTab === 'theory' && <TheoryView />}
        {activeTab === 'graph' && <GraphView stats={status?.stats ?? null} />}
      </main>

      <footer className="status-bar">
        <StatusBar status={status} error={statusError} />
      </footer>
    </div>
  )
}

interface TabButtonProps {
  label: string
  tabKey: TabKey
  activeTab: TabKey
  onClick: (tab: TabKey) => void
}

function TabButton({ label, tabKey, activeTab, onClick }: TabButtonProps) {
  const active = activeTab === tabKey
  return (
    <button
      className={active ? 'tab-button tab-button-active' : 'tab-button'}
      onClick={() => onClick(tabKey)}
    >
      {label}
    </button>
  )
}

function DashboardView({ status }: { status: StatusResponse | null }) {
  const stats = status?.stats

  return (
    <div className="panel">
      <h2>Catalog overview</h2>
      {!stats ? (
        <p className="muted">
          Waiting for backend status. Make sure the Python server is running on
          port 8000.
        </p>
      ) : (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total items</h3>
              <p className="stat-value">{stats.total_nodes}</p>
            </div>
            <div className="stat-card">
              <h3>Papers</h3>
              <p className="stat-value">{stats.papers}</p>
            </div>
            <div className="stat-card">
              <h3>Repositories</h3>
              <p className="stat-value">{stats.repositories}</p>
            </div>
          </div>
          <p className="muted">
            Use the controls above to start cataloguing papers and repositories.
            As items are ingested, Search, Theory, and Graph views will light
            up.
          </p>
        </>
      )}
    </div>
  )
}

function SearchView() {
  const [query, setQuery] = useState('')
  const [kind, setKind] = useState<'all' | Kind>('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<SearchResponse | null>(null)

  const [linkUrl, setLinkUrl] = useState('')
  const [linkLoading, setLinkLoading] = useState(false)
  const [linkError, setLinkError] = useState<string | null>(null)
  const [linkData, setLinkData] = useState<AnalyzeResponse | null>(null)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!query.trim()) {
      setError('Enter a query to search.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const body: any = { query, limit: 25 }
      if (kind !== 'all') {
        body.kind = kind
      }
      const res = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        throw new Error(await res.text())
      }
      const json: SearchResponse = await res.json()
      setData(json)
    } catch (err) {
      setError('Search failed. Ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const suggestions: string[] = useMemo(() => {
    if (!data) return []
    if (data.results.length >= 3) return []
    return [
      'Try a broader or related query.',
      'If the catalog is mostly empty, start cataloguing mode for papers and repos.',
    ]
  }, [data])

  const handleAnalyzeLink = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!linkUrl.trim()) {
      setLinkError('Paste an arXiv or GitHub URL to analyze.')
      return
    }
    setLinkLoading(true)
    setLinkError(null)
    try {
      const res = await fetch(`${API_BASE}/analyze/link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: linkUrl }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || 'Analysis failed')
      }
      const json: AnalyzeResponse = await res.json()
      setLinkData(json)
    } catch (err) {
      setLinkError(
        'Link analysis failed. Ensure the URL is a valid arXiv or GitHub link and the backend is running.',
      )
    } finally {
      setLinkLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Semantic search</h2>
      <form className="search-form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          placeholder="Ask about topics, methods, benchmarks, or code..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="select"
          value={kind}
          onChange={(e) => setKind(e.target.value as 'all' | Kind)}
        >
          <option value="all">Papers + repositories</option>
          <option value="paper">Papers only</option>
          <option value="repo">Repositories only</option>
        </select>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {data && (
        <>
          <p className="muted">
            Found {data.results.length}{' '}
            {data.results.length === 1 ? 'result' : 'results'} for "
            {data.query}".
          </p>
          <div className="results-list">
            {data.results.map((item) => (
              <article key={item.id} className="result-card">
                <div className="result-header">
                  <span className="kind-pill">{item.kind}</span>
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="result-title-link"
                  >
                    <h3 className="result-title">{item.title}</h3>
                  </a>
                </div>
                <p className="result-summary">{item.summary}</p>
                {item.tags.length > 0 && (
                  <div className="tag-row">
                    {item.tags.slice(0, 6).map((tag) => (
                      <span key={tag} className="tag-pill">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <div className="score-row">
                  <span>Relevancy: {item.real_world_relevancy.toFixed(1)}/10</span>
                  <span>Interesting: {item.interestingness.toFixed(1)}/10</span>
                  <span>Match: {(item.score * 100).toFixed(0)}%</span>
                </div>
              </article>
            ))}
          </div>
          {suggestions.length > 0 && (
            <div className="suggestions">
              <h4>Suggestions</h4>
              <ul>
                {suggestions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      <div className="link-section">
        <h3>Analyze a single link</h3>
        <form className="search-form" onSubmit={handleAnalyzeLink}>
          <input
            className="input"
            type="url"
            placeholder="Paste an arXiv or GitHub URL..."
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
          />
          <button
            className="btn btn-secondary"
            type="submit"
            disabled={linkLoading}
          >
            {linkLoading ? 'Analyzing...' : 'Analyze link'}
          </button>
        </form>
        {linkError && <p className="error">{linkError}</p>}
        {linkData && (
          <div className="link-results">
            <article className="result-card">
              <div className="result-header">
                <span className="kind-pill">{linkData.node.kind}</span>
                <a
                  href={linkData.node.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="result-title-link"
                >
                  <h3 className="result-title">{linkData.node.title}</h3>
                </a>
              </div>
              <p className="result-summary">{linkData.node.summary}</p>
              {linkData.node.tags.length > 0 && (
                <div className="tag-row">
                  {linkData.node.tags.slice(0, 6).map((tag) => (
                    <span key={tag} className="tag-pill">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <div className="score-row">
                <span>
                  Relevancy:{' '}
                  {linkData.node.real_world_relevancy.toFixed(1)}/10
                </span>
                <span>
                  Interesting:{' '}
                  {linkData.node.interestingness.toFixed(1)}/10
                </span>
              </div>
            </article>
            {linkData.similar.length > 0 && (
              <div className="link-similar">
                <h4>Similar items</h4>
                <div className="results-list">
                  {linkData.similar.map((sim) => (
                    <article key={sim.id} className="result-card">
                      <div className="result-header">
                        <span className="kind-pill">{sim.kind}</span>
                        <a
                          href={sim.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="result-title-link"
                        >
                          <h3 className="result-title">{sim.title}</h3>
                        </a>
                      </div>
                      <p className="result-summary">{sim.summary}</p>
                      <div className="score-row">
                        <span>Similarity: {(sim.score * 100).toFixed(0)}%</span>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function TheoryView() {
  const [theory, setTheory] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<TheoryResponse | null>(null)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!theory.trim()) {
      setError('Enter a theory or question to analyze.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/theory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theory, max_items: 25 }),
      })
      if (!res.ok) throw new Error(await res.text())
      const json: TheoryResponse = await res.json()
      setData(json)
    } catch (err) {
      setError('Theory analysis failed. Ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const totals = data?.totals

  return (
    <div className="panel">
      <h2>Theory mode</h2>
      <form className="search-form" onSubmit={handleSubmit}>
        <textarea
          className="input textarea"
          rows={3}
          placeholder="Example: Scaling laws predict that small models trained on curated data can match much larger general-purpose models."
          value={theory}
          onChange={(e) => setTheory(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze theory'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {data && (
        <>
          <div className="theory-summary">
            <h3>Stance distribution</h3>
            <div className="stats-grid">
              <div className="stat-card agree">
                <h4>Agree</h4>
                <p className="stat-value">{totals?.agree ?? 0}</p>
              </div>
              <div className="stat-card disagree">
                <h4>Disagree</h4>
                <p className="stat-value">{totals?.disagree ?? 0}</p>
              </div>
              <div className="stat-card neutral">
                <h4>Uncertain</h4>
                <p className="stat-value">{totals?.uncertain ?? 0}</p>
              </div>
            </div>
          </div>
          <div className="results-list">
            {data.items.map((item) => (
              <article key={item.id} className="result-card">
                <div className="result-header">
                  <span className="kind-pill">{item.kind}</span>
                  <span className={`stance-pill stance-${item.stance}`}>
                    {item.stance}
                  </span>
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="result-title-link"
                  >
                    <h3 className="result-title">{item.title}</h3>
                  </a>
                </div>
                <p className="result-summary">{item.summary}</p>
              </article>
            ))}
          </div>
          {data.suggestions.length > 0 && (
            <div className="suggestions">
              <h4>Suggestions</h4>
              <ul>
                {data.suggestions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function GraphView({ stats }: { stats: Stats | null }) {
  const [graphData, setGraphData] = useState<{
    nodes: (GraphNode & { group: string })[]
    links: { source: string; target: string; weight: number }[]
  }>({ nodes: [], links: [] })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    const fetchGraph = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE}/graph`)
        if (!res.ok) throw new Error(await res.text())
        const data: GraphResponse = await res.json()
        if (!cancelled) {
          setGraphData({
            nodes: data.nodes.map((n) => ({ ...n, group: n.kind })),
            links: data.edges,
          })
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError('Failed to load graph view.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    fetchGraph()
    return () => {
      cancelled = true
    }
  }, [stats?.total_nodes])

  return (
    <div className="panel graph-panel">
      <h2>Graph view</h2>
      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Loading graph...</p>}
      {!loading && graphData.nodes.length === 0 && (
        <p className="muted">
          No nodes yet. Start cataloguing mode to ingest papers and repositories.
        </p>
      )}
      {graphData.nodes.length > 0 && (
        <div className="graph-container">
          <ForceGraph2D
            graphData={graphData}
            nodeLabel={(node) =>
              `${(node as any).title} (${(node as any).kind})`
            }
            nodeAutoColorBy="group"
            nodeRelSize={6}
            linkWidth={1}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
          />
        </div>
      )}
    </div>
  )
}

function StatusBar({
  status,
  error,
}: {
  status: StatusResponse | null
  error: string | null
}) {
  if (error) {
    return <div className="status status-error">{error}</div>
  }
  if (!status) {
    return <div className="status">Connecting to backend...</div>
  }
  const { ingest, stats } = status
  return (
    <div className="status">
      <span>
        Papers:{' '}
        <strong>{ingest.papers.running ? 'running' : 'idle'}</strong>{' '}
        {ingest.papers.last_message && (
          <span className="status-detail">({ingest.papers.last_message})</span>
        )}
      </span>
      <span className="status-divider">|</span>
      <span>
        Repos:{' '}
        <strong>{ingest.repositories.running ? 'running' : 'idle'}</strong>{' '}
        {ingest.repositories.last_message && (
          <span className="status-detail">
            ({ingest.repositories.last_message})
          </span>
        )}
      </span>
      <span className="status-divider">|</span>
      <span>
        Catalog: {stats.papers} papers, {stats.repositories} repos
      </span>
      {(ingest.papers.last_error || ingest.repositories.last_error) && (
        <span className="status-detail status-warning">
          {' '}
          Ingest error – check backend logs.
        </span>
      )}
    </div>
  )
}

export default App
