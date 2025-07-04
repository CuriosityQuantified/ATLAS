interface WebSocketMessage {
  event_type: string;
  task_id: string;
  agent_id?: string;
  data: any;
  timestamp: string;
}

export class TaskWebSocketClient {
  private ws: WebSocket | null = null;
  private taskId: string;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(taskId: string) {
    this.taskId = taskId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Connect to the dedicated Global Supervisor WebSocket endpoint
        const wsUrl = `ws://localhost:8000/api/agui/agents/global_supervisor/${this.taskId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log(`WebSocket connected for task ${this.taskId}`);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log(`WebSocket closed for task ${this.taskId}:`, event.code, event.reason);
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error(`WebSocket error for task ${this.taskId}:`, error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('Received WebSocket message:', message);
    
    // Call specific handler for this event type
    const handler = this.messageHandlers.get(message.event_type);
    if (handler) {
      handler(message);
    }

    // Call global handler if registered
    const globalHandler = this.messageHandlers.get('*');
    if (globalHandler) {
      globalHandler(message);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached for WebSocket');
    }
  }

  onMessage(eventType: string, handler: (message: WebSocketMessage) => void) {
    this.messageHandlers.set(eventType, handler);
  }

  onAnyMessage(handler: (message: WebSocketMessage) => void) {
    this.messageHandlers.set('*', handler);
  }

  sendMessage(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers.clear();
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export default TaskWebSocketClient;