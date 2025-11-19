import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export interface ResearchItem {
  id: string;
  type: 'paper' | 'repository';
  title: string;
  url: string;
  source: string;
  summary: string;
  tags: string[];
  questions_answered: string[];
  key_findings: string[];
  relevancy_score: number;
  interesting_score: number;
  authors: string[];
  published_date?: string;
  ingested_date: string;
}

export interface GraphData {
  nodes: ResearchItem[];
  links: {
    source: string;
    target: string;
    type: string;
    weight: number;
  }[];
}

export interface Stats {
  total_items: number;
  total_papers: number;
  total_repos: number;
  total_relationships: number;
}

export interface TheoryResponse {
  answer: string;
  related_items: ResearchItem[];
}

export const api = {
  getStats: async () => {
    const res = await axios.get<Stats>(`${API_BASE}/stats`);
    return res.data;
  },
  getStatus: async () => {
    const res = await axios.get<{ingesting: boolean}>(`${API_BASE}/status`);
    return res.data;
  },
  controlIngest: async (enable: boolean) => {
    const res = await axios.post<{ingesting: boolean}>(`${API_BASE}/control/ingest`, null, { params: { enable } });
    return res.data;
  },
  getItems: async (skip = 0, limit = 50) => {
    const res = await axios.get<ResearchItem[]>(`${API_BASE}/items`, { params: { skip, limit } });
    return res.data;
  },
  getGraph: async () => {
    const res = await axios.get<GraphData>(`${API_BASE}/graph`);
    return res.data;
  },
  search: async (query: string, mode: 'text' | 'semantic' = 'text') => {
    const res = await axios.post<ResearchItem[]>(`${API_BASE}/search`, { query, mode });
    return res.data;
  },
  analyzeTheory: async (theory: string) => {
    const res = await axios.post<TheoryResponse>(`${API_BASE}/theory`, { theory });
    return res.data;
  }
};
