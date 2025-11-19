/** WebSocket service for realtime status updates */
export class StatusWebSocket {
  constructor(onMessage) {
    this.onMessage = onMessage;
    this.ws = null;
    this.reconnectInterval = null;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      if (this.reconnectInterval) {
        clearInterval(this.reconnectInterval);
        this.reconnectInterval = null;
      }
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (this.onMessage) {
          this.onMessage(data);
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 3 seconds
      if (!this.reconnectInterval) {
        this.reconnectInterval = setInterval(() => {
          this.connect();
        }, 3000);
      }
    };
  }

  disconnect() {
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval);
      this.reconnectInterval = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

