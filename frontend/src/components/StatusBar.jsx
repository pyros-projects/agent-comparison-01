import { useState, useEffect } from 'react';
import { StatusWebSocket } from '../websocket';
import './StatusBar.css';

export default function StatusBar() {
  const [status, setStatus] = useState({
    mode: 'idle',
    status: 'stopped',
    message: 'System idle',
    current_item: null
  });

  useEffect(() => {
    const ws = new StatusWebSocket((data) => {
      setStatus(data);
    });
    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, []);

  const getStatusColor = () => {
    if (status.status === 'running') return '#4CAF50';
    if (status.status === 'error') return '#f44336';
    return '#9E9E9E';
  };

  return (
    <div className="status-bar">
      <div className="status-indicator" style={{ backgroundColor: getStatusColor() }}></div>
      <div className="status-content">
        <span className="status-mode">{status.mode.toUpperCase()}</span>
        <span className="status-message">{status.message}</span>
        {status.current_item && (
          <span className="status-item">Processing: {status.current_item}</span>
        )}
      </div>
    </div>
  );
}

