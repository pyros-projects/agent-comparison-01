export type Tag = { tag: string; weight: number }

export type Analysis = {
  summary: string
  tags: Tag[]
  questions_answered: string[]
  key_findings: string[]
  relevance_score: number
  interesting_score: number
}

export type CatalogItem = {
  id: string
  kind: 'paper' | 'repo'
  source_url: string
  title: string
  abstract?: string
  created_at: string
  analysis: Analysis
}

export type StatusPayload = {
  mode: string
  message: string
  progress: number
  timestamp: string
}

export type DashboardStats = {
  total_items: number
  papers: number
  repos: number
  avg_relevance: number
  avg_interesting: number
  last_ingested?: string | null
}

export type StatusHistory = StatusPayload[]

export type GraphData = {
  nodes: { id: string; title: string; kind: 'paper' | 'repo'; score: number }[]
  edges: { source: string; target: string; weight: number }[]
}

export type GraphResponse = {
  nodes: { id: string; title: string; kind: 'paper' | 'repo'; score: number }[]
  edges: { source: string; target: string; weight: number }[]
}
