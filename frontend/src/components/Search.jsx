import { useState } from 'react';
import { api } from '../api';
import { Link } from 'react-router-dom';
import './Search.css';

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingUrl, setProcessingUrl] = useState(false);
  const [urlInput, setUrlInput] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await api.search(query);
      setResults(response.data);
    } catch (error) {
      console.error('Error searching:', error);
      alert('Error searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessURL = async (e) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setProcessingUrl(true);
    try {
      const response = await api.processURL(urlInput);
      alert(`Successfully processed ${response.data.type}: ${response.data.item.title || response.data.item.name}`);
      setUrlInput('');
      // Refresh search if we have results
      if (query) {
        handleSearch(e);
      }
    } catch (error) {
      console.error('Error processing URL:', error);
      alert('Error processing URL. Please check the URL and try again.');
    } finally {
      setProcessingUrl(false);
    }
  };

  return (
    <div className="search-page">
      <h1>Search</h1>

      <div className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search papers and repositories..."
            className="search-input"
          />
          <button type="submit" disabled={loading} className="search-button">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      <div className="url-section">
        <h2>Process URL</h2>
        <form onSubmit={handleProcessURL} className="url-form">
          <input
            type="text"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="Enter arXiv or GitHub URL..."
            className="url-input"
          />
          <button type="submit" disabled={processingUrl} className="url-button">
            {processingUrl ? 'Processing...' : 'Process'}
          </button>
        </form>
      </div>

      {results && (
        <div className="results-section">
          <h2>Results ({results.total})</h2>

          {results.papers.length > 0 && (
            <div className="results-group">
              <h3>Papers ({results.papers.length})</h3>
              {results.papers.map((paper) => (
                <div key={paper.id} className="result-card">
                  <Link to={`/paper/${paper.id}`} className="result-title">
                    {paper.title}
                  </Link>
                  <div className="result-meta">
                    <span>Authors: {paper.authors.join(', ')}</span>
                    <span>Relevancy: {paper.relevancy_score}/10</span>
                    <span>Interesting: {paper.interesting_score}/10</span>
                  </div>
                  <p className="result-summary">{paper.summary}</p>
                  <div className="result-tags">
                    {paper.tags.map((tag) => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {results.repositories.length > 0 && (
            <div className="results-group">
              <h3>Repositories ({results.repositories.length})</h3>
              {results.repositories.map((repo) => (
                <div key={repo.id} className="result-card">
                  <Link to={`/repository/${repo.id}`} className="result-title">
                    {repo.name}
                  </Link>
                  <div className="result-meta">
                    <span>Owner: {repo.owner}</span>
                    <span>Stars: {repo.stars}</span>
                    <span>Relevancy: {repo.relevancy_score}/10</span>
                    <span>Interesting: {repo.interesting_score}/10</span>
                  </div>
                  <p className="result-summary">{repo.summary}</p>
                  <div className="result-tags">
                    {repo.tags.map((tag) => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {results.total === 0 && (
            <div className="no-results">
              <p>No results found. Try a different search query or start cataloguing mode to gather more data.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

