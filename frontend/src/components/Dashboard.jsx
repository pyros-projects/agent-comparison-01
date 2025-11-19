import { useState, useEffect } from 'react';
import { api } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cataloguingStatus, setCataloguingStatus] = useState({
    papers: false,
    repos: false
  });

  useEffect(() => {
    loadData();
    loadStatus();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const response = await api.getStats();
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading stats:', error);
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const response = await api.getStatus();
      setCataloguingStatus(response.data);
    } catch (error) {
      console.error('Error loading status:', error);
    }
  };

  const togglePaperCataloguing = async () => {
    try {
      if (cataloguingStatus.papers_running) {
        await api.stopPaperCataloguing();
      } else {
        await api.startPaperCataloguing();
      }
      await loadStatus();
    } catch (error) {
      console.error('Error toggling paper cataloguing:', error);
    }
  };

  const toggleRepoCataloguing = async () => {
    try {
      if (cataloguingStatus.repos_running) {
        await api.stopRepoCataloguing();
      } else {
        await api.startRepoCataloguing();
      }
      await loadStatus();
    } catch (error) {
      console.error('Error toggling repo cataloguing:', error);
    }
  };

  if (loading) {
    return <div className="dashboard loading">Loading...</div>;
  }

  const chartData = [
    {
      name: 'Papers',
      Relevancy: stats?.avg_relevancy_papers || 0,
      Interesting: stats?.avg_interesting_papers || 0
    },
    {
      name: 'Repos',
      Relevancy: stats?.avg_relevancy_repos || 0,
      Interesting: stats?.avg_interesting_repos || 0
    }
  ];

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Papers</h3>
          <div className="stat-value">{stats?.total_papers || 0}</div>
        </div>
        
        <div className="stat-card">
          <h3>Total Repositories</h3>
          <div className="stat-value">{stats?.total_repositories || 0}</div>
        </div>
        
        <div className="stat-card">
          <h3>Graph Nodes</h3>
          <div className="stat-value">{stats?.graph_nodes || 0}</div>
        </div>
        
        <div className="stat-card">
          <h3>Graph Edges</h3>
          <div className="stat-value">{stats?.graph_edges || 0}</div>
        </div>
      </div>

      <div className="cataloguing-controls">
        <h2>Cataloguing Controls</h2>
        <div className="control-buttons">
          <button
            className={cataloguingStatus.papers_running ? 'active' : ''}
            onClick={togglePaperCataloguing}
          >
            {cataloguingStatus.papers_running ? 'Stop' : 'Start'} Paper Cataloguing
          </button>
          <button
            className={cataloguingStatus.repos_running ? 'active' : ''}
            onClick={toggleRepoCataloguing}
          >
            {cataloguingStatus.repos_running ? 'Stop' : 'Start'} Repository Cataloguing
          </button>
        </div>
      </div>

      <div className="chart-section">
        <h2>Average Scores</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="Relevancy" fill="#8884d8" />
            <Bar dataKey="Interesting" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

