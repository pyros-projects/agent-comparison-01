import { useState } from 'react';
import { api } from '../api';
import { Link } from 'react-router-dom';
import './Theory.css';

export default function Theory() {
  const [theory, setTheory] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!theory.trim()) return;

    setLoading(true);
    try {
      const response = await api.analyzeTheory(theory);
      setResults(response.data);
    } catch (error) {
      console.error('Error analyzing theory:', error);
      alert('Error analyzing theory. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="theory-page">
      <h1>Theory Mode</h1>
      <p className="theory-description">
        Enter a theory or question to find supporting and opposing evidence from the catalog.
      </p>

      <form onSubmit={handleAnalyze} className="theory-form">
        <textarea
          value={theory}
          onChange={(e) => setTheory(e.target.value)}
          placeholder="Enter your theory or question here..."
          className="theory-input"
          rows={4}
        />
        <button type="submit" disabled={loading} className="theory-button">
          {loading ? 'Analyzing...' : 'Analyze Theory'}
        </button>
      </form>

      {results && (
        <div className="theory-results">
          <div className="theory-summary">
            <div className="summary-card supporting">
              <h3>Supporting</h3>
              <div className="summary-count">
                {results.supporting_papers.length + results.supporting_repos.length}
              </div>
              <div className="summary-breakdown">
                <span>{results.supporting_papers.length} papers</span>
                <span>{results.supporting_repos.length} repos</span>
              </div>
            </div>
            <div className="summary-card opposing">
              <h3>Opposing</h3>
              <div className="summary-count">
                {results.opposing_papers.length + results.opposing_repos.length}
              </div>
              <div className="summary-breakdown">
                <span>{results.opposing_papers.length} papers</span>
                <span>{results.opposing_repos.length} repos</span>
              </div>
            </div>
          </div>

          {results.supporting_papers.length > 0 && (
            <div className="results-group">
              <h2>Supporting Papers</h2>
              {results.supporting_papers.map((paper) => (
                <div key={paper.id} className="result-card">
                  <Link to={`/paper/${paper.id}`} className="result-title">
                    {paper.title}
                  </Link>
                  <p className="result-summary">{paper.summary}</p>
                </div>
              ))}
            </div>
          )}

          {results.supporting_repos.length > 0 && (
            <div className="results-group">
              <h2>Supporting Repositories</h2>
              {results.supporting_repos.map((repo) => (
                <div key={repo.id} className="result-card">
                  <Link to={`/repository/${repo.id}`} className="result-title">
                    {repo.name}
                  </Link>
                  <p className="result-summary">{repo.summary}</p>
                </div>
              ))}
            </div>
          )}

          {results.opposing_papers.length > 0 && (
            <div className="results-group">
              <h2>Opposing Papers</h2>
              {results.opposing_papers.map((paper) => (
                <div key={paper.id} className="result-card">
                  <Link to={`/paper/${paper.id}`} className="result-title">
                    {paper.title}
                  </Link>
                  <p className="result-summary">{paper.summary}</p>
                </div>
              ))}
            </div>
          )}

          {results.opposing_repos.length > 0 && (
            <div className="results-group">
              <h2>Opposing Repositories</h2>
              {results.opposing_repos.map((repo) => (
                <div key={repo.id} className="result-card">
                  <Link to={`/repository/${repo.id}`} className="result-title">
                    {repo.name}
                  </Link>
                  <p className="result-summary">{repo.summary}</p>
                </div>
              ))}
            </div>
          )}

          {results.related_theories && results.related_theories.length > 0 && (
            <div className="related-theories">
              <h2>Related Theories</h2>
              <ul>
                {results.related_theories.map((theory, idx) => (
                  <li key={idx}>{theory}</li>
                ))}
              </ul>
            </div>
          )}

          {results.suggestions && results.suggestions.length > 0 && (
            <div className="suggestions">
              <h2>Suggestions</h2>
              <ul>
                {results.suggestions.map((suggestion, idx) => (
                  <li key={idx}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {results.supporting_papers.length === 0 && 
           results.supporting_repos.length === 0 &&
           results.opposing_papers.length === 0 &&
           results.opposing_repos.length === 0 && (
            <div className="no-results">
              <p>No results found for this theory. Consider starting cataloguing mode to gather more data.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

