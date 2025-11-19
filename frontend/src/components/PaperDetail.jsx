import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import './Detail.css';

export default function PaperDetail() {
  const { id } = useParams();
  const [paper, setPaper] = useState(null);
  const [similar, setSimilar] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPaper();
    loadSimilar();
  }, [id]);

  const loadPaper = async () => {
    try {
      const response = await api.getPaper(id);
      setPaper(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading paper:', error);
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

  if (!paper) {
    return <div className="detail-page">Paper not found</div>;
  }

  return (
    <div className="detail-page">
      <Link to="/search" className="back-link">← Back to Search</Link>
      
      <div className="detail-header">
        <h1>{paper.title}</h1>
        <div className="detail-meta">
          <div className="meta-item">
            <strong>Authors:</strong> {paper.authors.join(', ')}
          </div>
          {paper.published_date && (
            <div className="meta-item">
              <strong>Published:</strong> {new Date(paper.published_date).toLocaleDateString()}
            </div>
          )}
          <div className="meta-item">
            <strong>Relevancy Score:</strong> {paper.relevancy_score}/10
          </div>
          <div className="meta-item">
            <strong>Interesting Score:</strong> {paper.interesting_score}/10
          </div>
          <div className="meta-item">
            <a href={paper.url} target="_blank" rel="noopener noreferrer" className="external-link">
              View on arXiv →
            </a>
          </div>
        </div>
      </div>

      <div className="detail-section">
        <h2>Summary</h2>
        <p>{paper.summary}</p>
      </div>

      <div className="detail-section">
        <h2>Abstract</h2>
        <p>{paper.abstract}</p>
      </div>

      {paper.tags.length > 0 && (
        <div className="detail-section">
          <h2>Tags</h2>
          <div className="tags">
            {paper.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
        </div>
      )}

      {paper.questions_answered.length > 0 && (
        <div className="detail-section">
          <h2>Questions Answered</h2>
          <ul>
            {paper.questions_answered.map((question, idx) => (
              <li key={idx}>{question}</li>
            ))}
          </ul>
        </div>
      )}

      {paper.key_findings.length > 0 && (
        <div className="detail-section">
          <h2>Key Findings</h2>
          <ul>
            {paper.key_findings.map((finding, idx) => (
              <li key={idx}>{finding}</li>
            ))}
          </ul>
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

