import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import './Detail.css';

export default function RepositoryDetail() {
  const { id } = useParams();
  const [repo, setRepo] = useState(null);
  const [similar, setSimilar] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRepository();
    loadSimilar();
  }, [id]);

  const loadRepository = async () => {
    try {
      const response = await api.getRepository(id);
      setRepo(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading repository:', error);
      setLoading(false);
    }
  };

  const loadSimilar = async () => {
    try {
      const response = await api.getSimilar(id);
      setSimilar(response.data);
    } catch (error) {
      console.error('Error loading similar items:', error);
    }
  };

  if (loading) {
    return <div className="detail-page loading">Loading...</div>;
  }

  if (!repo) {
    return <div className="detail-page">Repository not found</div>;
  }

  return (
    <div className="detail-page">
      <Link to="/search" className="back-link">← Back to Search</Link>
      
      <div className="detail-header">
        <h1>{repo.name}</h1>
        <div className="detail-meta">
          <div className="meta-item">
            <strong>Owner:</strong> {repo.owner}
          </div>
          {repo.language && (
            <div className="meta-item">
              <strong>Language:</strong> {repo.language}
            </div>
          )}
          <div className="meta-item">
            <strong>Stars:</strong> {repo.stars}
          </div>
          <div className="meta-item">
            <strong>Relevancy Score:</strong> {repo.relevancy_score}/10
          </div>
          <div className="meta-item">
            <strong>Interesting Score:</strong> {repo.interesting_score}/10
          </div>
          <div className="meta-item">
            <a href={repo.url} target="_blank" rel="noopener noreferrer" className="external-link">
              View on GitHub →
            </a>
          </div>
        </div>
      </div>

      <div className="detail-section">
        <h2>Description</h2>
        <p>{repo.description}</p>
      </div>

      <div className="detail-section">
        <h2>Summary</h2>
        <p>{repo.summary}</p>
      </div>

      {repo.tags.length > 0 && (
        <div className="detail-section">
          <h2>Tags</h2>
          <div className="tags">
            {repo.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
        </div>
      )}

      {repo.questions_answered.length > 0 && (
        <div className="detail-section">
          <h2>Questions Answered</h2>
          <ul>
            {repo.questions_answered.map((question, idx) => (
              <li key={idx}>{question}</li>
            ))}
          </ul>
        </div>
      )}

      {repo.key_findings.length > 0 && (
        <div className="detail-section">
          <h2>Key Findings</h2>
          <ul>
            {repo.key_findings.map((finding, idx) => (
              <li key={idx}>{finding}</li>
            ))}
          </ul>
        </div>
      )}

      {repo.readme_content && (
        <div className="detail-section">
          <h2>README</h2>
          <pre className="readme-content">{repo.readme_content}</pre>
        </div>
      )}

      {similar && (similar.papers.length > 0 || similar.repositories.length > 0) && (
        <div className="detail-section">
          <h2>Similar Items</h2>
          
          {similar.papers.length > 0 && (
            <div className="similar-group">
              <h3>Similar Papers</h3>
              {similar.papers.map((p) => (
                <div key={p.id} className="similar-item">
                  <Link to={`/paper/${p.id}`} className="similar-title">
                    {p.title}
                  </Link>
                  <p className="similar-summary">{p.summary}</p>
                </div>
              ))}
            </div>
          )}

          {similar.repositories.length > 0 && (
            <div className="similar-group">
              <h3>Similar Repositories</h3>
              {similar.repositories.map((r) => (
                <div key={r.id} className="similar-item">
                  <Link to={`/repository/${r.id}`} className="similar-title">
                    {r.name}
                  </Link>
                  <p className="similar-summary">{r.summary}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

