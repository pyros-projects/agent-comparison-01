/** API service for backend communication */
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const api = {
  // Status
  getStatus: () => axios.get(`${API_BASE}/status`),
  
  // Cataloguing
  startPaperCataloguing: () => axios.post(`${API_BASE}/cataloguing/papers/start`),
  stopPaperCataloguing: () => axios.post(`${API_BASE}/cataloguing/papers/stop`),
  startRepoCataloguing: () => axios.post(`${API_BASE}/cataloguing/repos/start`),
  stopRepoCataloguing: () => axios.post(`${API_BASE}/cataloguing/repos/stop`),
  
  // Search
  search: (query, limit = 50) => axios.post(`${API_BASE}/search`, { query, limit }),
  
  // Papers
  getPaper: (id) => axios.get(`${API_BASE}/papers/${id}`),
  listPapers: (limit = 100) => axios.get(`${API_BASE}/papers`, { params: { limit } }),
  
  // Repositories
  getRepository: (id) => axios.get(`${API_BASE}/repositories/${id}`),
  listRepositories: (limit = 100) => axios.get(`${API_BASE}/repositories`, { params: { limit } }),
  
  // Process URL
  processURL: (url) => axios.post(`${API_BASE}/process-url`, { url }),
  
  // Similar items
  getSimilar: (id) => axios.get(`${API_BASE}/similar/${id}`),
  
  // Theory
  analyzeTheory: (theory) => axios.post(`${API_BASE}/theory`, { theory }),
  
  // Stats
  getStats: () => axios.get(`${API_BASE}/stats`),
  
  // Graph
  getGraph: () => axios.get(`${API_BASE}/graph`),
};

