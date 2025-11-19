import { useState, useEffect } from 'react';
import { api } from '../api';
import { Link } from 'react-router-dom';
import './GraphView.css';

export default function GraphView() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    loadGraph();
    const interval = setInterval(loadGraph, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadGraph = async () => {
    try {
      const response = await api.getGraph();
      setGraphData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading graph:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="graph-view loading">Loading graph...</div>;
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="graph-view">
        <h1>Graph View</h1>
        <div className="no-graph">
          <p>No graph data available. Start cataloguing to build the graph.</p>
        </div>
      </div>
    );
  }

  // Simple force-directed layout simulation
  const nodes = graphData.nodes.map((node, idx) => {
    const angle = (idx / graphData.nodes.length) * 2 * Math.PI;
    const radius = 200;
    return {
      ...node,
      x: 400 + radius * Math.cos(angle),
      y: 300 + radius * Math.sin(angle)
    };
  });

  return (
    <div className="graph-view">
      <h1>Graph View</h1>
      <div className="graph-info">
        <span>Nodes: {graphData.nodes.length}</span>
        <span>Edges: {graphData.edges.length}</span>
      </div>

      <div className="graph-container">
        <svg width="800" height="600" className="graph-svg">
          {/* Draw edges */}
          {graphData.edges.map((edge, idx) => {
            const sourceNode = nodes.find(n => n.id === edge.source);
            const targetNode = nodes.find(n => n.id === edge.target);
            if (!sourceNode || !targetNode) return null;
            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke="#ccc"
                strokeWidth="1"
              />
            );
          })}

          {/* Draw nodes */}
          {nodes.map((node) => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={node.type === 'paper' ? 8 : 6}
                fill={node.type === 'paper' ? '#2196F3' : '#4CAF50'}
                className="graph-node"
                onClick={() => setSelectedNode(node)}
              />
              {selectedNode?.id === node.id && (
                <text
                  x={node.x}
                  y={node.y - 15}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#333"
                  className="node-label"
                >
                  {node.label}
                </text>
              )}
            </g>
          ))}
        </svg>

        {selectedNode && (
          <div className="node-details">
            <h3>{selectedNode.label}</h3>
            <p>Type: {selectedNode.type}</p>
            <Link
              to={`/${selectedNode.type}/${selectedNode.id}`}
              className="view-link"
            >
              View Details
            </Link>
            <button onClick={() => setSelectedNode(null)} className="close-button">
              Close
            </button>
          </div>
        )}
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-color paper"></span>
          <span>Papers</span>
        </div>
        <div className="legend-item">
          <span className="legend-color repo"></span>
          <span>Repositories</span>
        </div>
      </div>
    </div>
  );
}

