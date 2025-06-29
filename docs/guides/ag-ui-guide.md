# AG-UI Protocol Comprehensive Guide for ATLAS (2025)

## Overview

AG-UI (Agent-User Interaction Protocol) is a lightweight, event-based protocol that standardizes how AI agents connect to frontend applications. This guide covers implementation for ATLAS multi-agent system with real-time communication, bidirectional interaction, and seamless agent-user synchronization.

## AG-UI Protocol Architecture

### Core Concepts

AG-UI creates a live, bidirectional stream of events between agent backends and frontend interfaces, maintaining perfect real-time synchronization through:

- **Event-Driven Communication**: 16 standardized event types covering the full agent lifecycle
- **Transport Flexibility**: Works with SSE, WebSockets, webhooks, or any HTTP-based transport
- **Bidirectional Interaction**: Users can interrupt, modify, or add input while maintaining session context
- **Framework Agnostic**: Compatible with LangGraph, CrewAI, Mastra, AG2, and custom implementations

### Event System Structure

```typescript
// Core AG-UI event structure
interface AGUIEvent {
  type: AGUIEventType;
  id?: string;
  timestamp?: string;
  data?: Record<string, any>;
}

// 16 Standard Event Types
enum AGUIEventType {
  // Lifecycle Events
  RUN_STARTED = "RUN_STARTED",
  RUN_FINISHED = "RUN_FINISHED",
  
  // Text Message Events
  TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT",
  TEXT_MESSAGE_START = "TEXT_MESSAGE_START",
  TEXT_MESSAGE_END = "TEXT_MESSAGE_END",
  
  // Tool Call Events
  TOOL_CALL_START = "TOOL_CALL_START",
  TOOL_CALL_END = "TOOL_CALL_END",
  TOOL_CALL_RESULT = "TOOL_CALL_RESULT",
  
  // State Management Events
  STATE_DELTA = "STATE_DELTA",
  STATE_SYNC = "STATE_SYNC",
  
  // User Interaction Events
  USER_INPUT = "USER_INPUT",
  USER_INTERRUPT = "USER_INTERRUPT",
  
  // System Events
  ERROR = "ERROR",
  WARNING = "WARNING",
  SYSTEM_MESSAGE = "SYSTEM_MESSAGE",
  AGENT_STATUS = "AGENT_STATUS"
}
```

## Frontend Implementation

### 1. React Frontend with AG-UI Integration

```typescript
// frontend/src/components/AtlasInterface.tsx

import React, { useState, useEffect, useRef } from 'react';
// Note: AG-UI is a custom protocol - implement AGUIClient class below
import { 
  AGUIEvent, 
  AGUIEventType, 
  ATLASTask, 
  AgentStatus 
} from '../types/atlas';

interface AtlasInterfaceProps {
  apiEndpoint: string;
  userId: string;
  taskId?: string;
}

export const AtlasInterface: React.FC<AtlasInterfaceProps> = ({
  apiEndpoint,
  userId,
  taskId
}) => {
  const [messages, setMessages] = useState<AGUIEvent[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle');
  const [currentTask, setCurrentTask] = useState<ATLASTask | null>(null);
  const [toolCalls, setToolCalls] = useState<any[]>([]);
  const [systemState, setSystemState] = useState<any>({});
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  
  const clientRef = useRef<AGUIClient | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize AG-UI client
    clientRef.current = new AGUIClient({
      endpoint: `${apiEndpoint}/ag-ui/stream`,
      userId,
      taskId,
      transport: 'sse', // Server-Sent Events
      reconnectAttempts: 5,
      reconnectDelay: 1000
    });

    // Set up event handlers
    setupEventHandlers();

    // Connect to backend
    clientRef.current.connect().then(() => {
      setIsConnected(true);
    });

    return () => {
      clientRef.current?.disconnect();
    };
  }, [apiEndpoint, userId, taskId]);

  const setupEventHandlers = () => {
    const client = clientRef.current;
    if (!client) return;

    // Lifecycle Events
    client.on(AGUIEventType.RUN_STARTED, (event: AGUIEvent) => {
      setAgentStatus('running');
      setCurrentTask(event.data.task);
      addMessage(event);
    });

    client.on(AGUIEventType.RUN_FINISHED, (event: AGUIEvent) => {
      setAgentStatus('completed');
      addMessage(event);
    });

    // Text Message Events
    client.on(AGUIEventType.TEXT_MESSAGE_CONTENT, (event: AGUIEvent) => {
      updateLastMessage(event);
    });

    client.on(AGUIEventType.TEXT_MESSAGE_START, (event: AGUIEvent) => {
      addMessage({
        ...event,
        data: { ...event.data, content: '', streaming: true }
      });
    });

    client.on(AGUIEventType.TEXT_MESSAGE_END, (event: AGUIEvent) => {
      finalizeLastMessage(event);
    });

    // Tool Call Events
    client.on(AGUIEventType.TOOL_CALL_START, (event: AGUIEvent) => {
      setToolCalls(prev => [...prev, {
        id: event.data.toolCallId,
        name: event.data.toolName,
        args: event.data.args,
        status: 'running',
        timestamp: event.timestamp
      }]);
      addMessage(event);
    });

    client.on(AGUIEventType.TOOL_CALL_END, (event: AGUIEvent) => {
      setToolCalls(prev => prev.map(call => 
        call.id === event.data.toolCallId 
          ? { ...call, status: 'completed', result: event.data.result }
          : call
      ));
      addMessage(event);
    });

    // State Management Events
    client.on(AGUIEventType.STATE_DELTA, (event: AGUIEvent) => {
      setSystemState(prev => ({
        ...prev,
        ...event.data.delta
      }));
    });

    client.on(AGUIEventType.STATE_SYNC, (event: AGUIEvent) => {
      setSystemState(event.data.state);
    });

    // Agent Status Events
    client.on(AGUIEventType.AGENT_STATUS, (event: AGUIEvent) => {
      setAgentStatus(event.data.status);
      addMessage(event);
    });

    // Error Events
    client.on(AGUIEventType.ERROR, (event: AGUIEvent) => {
      addMessage(event);
      setAgentStatus('error');
    });

    // Connection Events
    client.on('connected', () => {
      setIsConnected(true);
    });

    client.on('disconnected', () => {
      setIsConnected(false);
    });
  };

  const addMessage = (event: AGUIEvent) => {
    setMessages(prev => [...prev, event]);
    scrollToBottom();
  };

  const updateLastMessage = (event: AGUIEvent) => {
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage && lastMessage.data?.streaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            data: {
              ...lastMessage.data,
              content: (lastMessage.data.content || '') + event.data.content
            }
          }
        ];
      }
      return [...prev, event];
    });
    scrollToBottom();
  };

  const finalizeLastMessage = (event: AGUIEvent) => {
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage && lastMessage.data?.streaming) {
        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            data: {
              ...lastMessage.data,
              streaming: false,
              final: true
            }
          }
        ];
      }
      return prev;
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendUserInput = async () => {
    if (!inputValue.trim() || !clientRef.current) return;

    const userEvent: AGUIEvent = {
      type: AGUIEventType.USER_INPUT,
      id: `user_${Date.now()}`,
      timestamp: new Date().toISOString(),
      data: {
        content: inputValue,
        userId,
        taskId: currentTask?.id
      }
    };

    // Send to backend
    await clientRef.current.send(userEvent);
    
    // Add to local messages
    addMessage(userEvent);
    setInputValue('');
  };

  const interruptAgent = async () => {
    if (!clientRef.current) return;

    const interruptEvent: AGUIEvent = {
      type: AGUIEventType.USER_INTERRUPT,
      id: `interrupt_${Date.now()}`,
      timestamp: new Date().toISOString(),
      data: {
        reason: 'user_requested',
        userId,
        taskId: currentTask?.id
      }
    };

    await clientRef.current.send(interruptEvent);
    setAgentStatus('interrupted');
  };

  const startNewTask = async (taskDescription: string, taskType: string) => {
    if (!clientRef.current) return;

    const taskEvent: AGUIEvent = {
      type: 'START_TASK',
      id: `task_${Date.now()}`,
      timestamp: new Date().toISOString(),
      data: {
        description: taskDescription,
        type: taskType,
        userId,
        priority: 'normal'
      }
    };

    await clientRef.current.send(taskEvent);
  };

  return (
    <div className="atlas-interface">
      {/* Header with connection status */}
      <div className="header">
        <h1>ATLAS Multi-Agent System</h1>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>
        <div className={`agent-status ${agentStatus}`}>
          Agent: {agentStatus}
        </div>
      </div>

      {/* Task Information */}
      {currentTask && (
        <div className="current-task">
          <h3>Current Task: {currentTask.description}</h3>
          <div className="task-metadata">
            <span>Type: {currentTask.type}</span>
            <span>Priority: {currentTask.priority}</span>
            <span>Teams: {currentTask.teams?.join(', ')}</span>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="messages-container">
        {messages.map((message, index) => (
          <MessageComponent 
            key={`${message.id}_${index}`} 
            event={message} 
            isLast={index === messages.length - 1}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Active Tool Calls */}
      {toolCalls.length > 0 && (
        <div className="tool-calls">
          <h4>Active Tool Calls</h4>
          {toolCalls.map(call => (
            <ToolCallComponent key={call.id} toolCall={call} />
          ))}
        </div>
      )}

      {/* System State Visualization */}
      <div className="system-state">
        <h4>System State</h4>
        <SystemStateComponent state={systemState} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-controls">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendUserInput()}
            placeholder="Type your message or instruction..."
            disabled={!isConnected}
          />
          <button onClick={sendUserInput} disabled={!isConnected || !inputValue.trim()}>
            Send
          </button>
          <button 
            onClick={interruptAgent} 
            disabled={!isConnected || agentStatus !== 'running'}
            className="interrupt-btn"
          >
            Interrupt
          </button>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <button onClick={() => startNewTask('Analyze market trends', 'analysis')}>
            📊 Market Analysis
          </button>
          <button onClick={() => startNewTask('Research competitors', 'research')}>
            🔍 Competitor Research
          </button>
          <button onClick={() => startNewTask('Generate report', 'writing')}>
            📄 Generate Report
          </button>
        </div>
      </div>
    </div>
  );
};

// Message Component
const MessageComponent: React.FC<{ event: AGUIEvent; isLast: boolean }> = ({ event, isLast }) => {
  const getMessageClass = () => {
    if (event.type === AGUIEventType.USER_INPUT) return 'user-message';
    if (event.type === AGUIEventType.ERROR) return 'error-message';
    if (event.type.startsWith('TOOL_CALL')) return 'tool-message';
    return 'agent-message';
  };

  const formatEventData = () => {
    switch (event.type) {
      case AGUIEventType.TEXT_MESSAGE_CONTENT:
      case AGUIEventType.TEXT_MESSAGE_START:
      case AGUIEventType.TEXT_MESSAGE_END:
        return (
          <div className="text-content">
            {event.data.content}
            {event.data.streaming && <span className="cursor">▊</span>}
          </div>
        );
      
      case AGUIEventType.TOOL_CALL_START:
        return (
          <div className="tool-call-start">
            🔧 Calling tool: <strong>{event.data.toolName}</strong>
            <pre>{JSON.stringify(event.data.args, null, 2)}</pre>
          </div>
        );
      
      case AGUIEventType.TOOL_CALL_END:
        return (
          <div className="tool-call-end">
            ✅ Tool completed: <strong>{event.data.toolName}</strong>
            <pre>{JSON.stringify(event.data.result, null, 2)}</pre>
          </div>
        );
      
      case AGUIEventType.RUN_STARTED:
        return (
          <div className="run-started">
            🚀 Started task: {event.data.task?.description}
          </div>
        );
      
      case AGUIEventType.AGENT_STATUS:
        return (
          <div className="agent-status-message">
            🤖 Agent status: {event.data.status}
            {event.data.details && <div className="details">{event.data.details}</div>}
          </div>
        );
      
      default:
        return (
          <div className="generic-event">
            <strong>{event.type}</strong>
            <pre>{JSON.stringify(event.data, null, 2)}</pre>
          </div>
        );
    }
  };

  return (
    <div className={`message ${getMessageClass()}`}>
      <div className="message-header">
        <span className="event-type">{event.type}</span>
        <span className="timestamp">
          {new Date(event.timestamp || Date.now()).toLocaleTimeString()}
        </span>
      </div>
      <div className="message-content">
        {formatEventData()}
      </div>
    </div>
  );
};

// Tool Call Component
const ToolCallComponent: React.FC<{ toolCall: any }> = ({ toolCall }) => (
  <div className={`tool-call ${toolCall.status}`}>
    <div className="tool-header">
      <strong>{toolCall.name}</strong>
      <span className={`status ${toolCall.status}`}>{toolCall.status}</span>
    </div>
    <div className="tool-args">
      <pre>{JSON.stringify(toolCall.args, null, 2)}</pre>
    </div>
    {toolCall.result && (
      <div className="tool-result">
        <strong>Result:</strong>
        <pre>{JSON.stringify(toolCall.result, null, 2)}</pre>
      </div>
    )}
  </div>
);

// System State Component
const SystemStateComponent: React.FC<{ state: any }> = ({ state }) => (
  <div className="system-state-display">
    {Object.entries(state).map(([key, value]) => (
      <div key={key} className="state-item">
        <strong>{key}:</strong> 
        <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
      </div>
    ))}
  </div>
);
```

### 2. AG-UI Client SDK Integration

```typescript
// frontend/src/lib/aguiClient.ts

// EventSource is a native browser API - no import needed

export interface AGUIClientConfig {
  endpoint: string;
  userId: string;
  taskId?: string;
  transport: 'sse' | 'websocket' | 'webhook';
  reconnectAttempts?: number;
  reconnectDelay?: number;
  headers?: Record<string, string>;
}

export class AGUIClient {
  private config: AGUIClientConfig;
  private eventSource: EventSource | null = null;
  private websocket: WebSocket | null = null;
  private eventHandlers: Map<string, Function[]> = new Map();
  private isConnected = false;
  private reconnectAttempts = 0;

  constructor(config: AGUIClientConfig) {
    this.config = {
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      ...config
    };
  }

  async connect(): Promise<void> {
    if (this.config.transport === 'sse') {
      await this.connectSSE();
    } else if (this.config.transport === 'websocket') {
      await this.connectWebSocket();
    }
  }

  private async connectSSE(): Promise<void> {
    const url = new URL(this.config.endpoint);
    url.searchParams.set('userId', this.config.userId);
    if (this.config.taskId) {
      url.searchParams.set('taskId', this.config.taskId);
    }

    this.eventSource = new EventSource(url.toString());

    this.eventSource.onopen = () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.emit('connected');
    };

    this.eventSource.onmessage = (event) => {
      try {
        const aguiEvent = JSON.parse(event.data);
        this.emit(aguiEvent.type, aguiEvent);
      } catch (error) {
        console.error('Failed to parse AG-UI event:', error);
      }
    };

    this.eventSource.onerror = () => {
      this.isConnected = false;
      this.emit('disconnected');
      this.handleReconnect();
    };
  }

  private async connectWebSocket(): Promise<void> {
    const url = new URL(this.config.endpoint);
    const wsUrl = `${url.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.host}${url.pathname}`;
    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.emit('connected');
      
      // Send initial connection message
      this.send({
        type: 'CONNECTION_INIT',
        data: {
          userId: this.config.userId,
          taskId: this.config.taskId
        }
      });
    };

    this.websocket.onmessage = (event) => {
      try {
        const aguiEvent = JSON.parse(event.data);
        this.emit(aguiEvent.type, aguiEvent);
      } catch (error) {
        console.error('Failed to parse AG-UI event:', error);
      }
    };

    this.websocket.onclose = () => {
      this.isConnected = false;
      this.emit('disconnected');
      this.handleReconnect();
    };

    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < (this.config.reconnectAttempts || 5)) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect();
      }, this.config.reconnectDelay || 1000);
    }
  }

  async send(event: AGUIEvent): Promise<void> {
    if (!this.isConnected) {
      throw new Error('Not connected to AG-UI backend');
    }

    const eventData = JSON.stringify(event);

    if (this.config.transport === 'websocket' && this.websocket) {
      this.websocket.send(eventData);
    } else if (this.config.transport === 'sse') {
      // For SSE, send via POST to a separate endpoint
      await fetch(this.config.endpoint.replace('/stream', '/send'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.config.headers
        },
        body: eventData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    }
  }

  on(eventType: string, handler: Function): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
  }

  off(eventType: string, handler: Function): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(eventType: string, data?: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
  }
}
```

## Backend Implementation

### 1. FastAPI Backend with AG-UI Protocol

```python
# backend/ag_ui_server.py

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
import json
import uuid
from datetime import datetime
import logging
from dataclasses import dataclass, asdict

# AG-UI Event Models
class AGUIEvent(BaseModel):
    type: str
    id: Optional[str] = None
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class AGUIEventType:
    # Lifecycle Events
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    
    # Text Message Events
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    
    # Tool Call Events
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    
    # State Management Events
    STATE_DELTA = "STATE_DELTA"
    STATE_SYNC = "STATE_SYNC"
    
    # User Interaction Events
    USER_INPUT = "USER_INPUT"
    USER_INTERRUPT = "USER_INTERRUPT"
    
    # System Events
    ERROR = "ERROR"
    WARNING = "WARNING"
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
    AGENT_STATUS = "AGENT_STATUS"

@dataclass
class ATLASTask:
    id: str
    description: str
    type: str
    priority: str
    user_id: str
    teams: List[str]
    status: str = "pending"
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class AGUIConnection:
    """Manages individual AG-UI client connections"""
    
    def __init__(self, user_id: str, task_id: Optional[str] = None):
        self.user_id = user_id
        self.task_id = task_id
        self.connection_id = str(uuid.uuid4())
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.is_active = True
        
    async def send_event(self, event: AGUIEvent):
        """Send event to client"""
        if self.is_active:
            await self.event_queue.put(event)
    
    async def get_events(self) -> AsyncGenerator[str, None]:
        """Generator for SSE events"""
        while self.is_active:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=30.0)
                
                # Format as SSE
                sse_data = f"data: {json.dumps(event.dict() if hasattr(event, 'dict') else event.__dict__)}\n\n"
                yield sse_data
                
            except asyncio.TimeoutError:
                # Send keepalive
                yield "data: {\"type\": \"KEEPALIVE\"}\n\n"
            except Exception as e:
                logging.error(f"Error in AG-UI event stream: {e}")
                break
    
    def close(self):
        """Close connection"""
        self.is_active = False

class AGUIManager:
    """Manages AG-UI connections and event distribution"""
    
    def __init__(self):
        self.connections: Dict[str, AGUIConnection] = {}
        self.user_connections: Dict[str, List[str]] = {}
        self.task_connections: Dict[str, List[str]] = {}
        
    def add_connection(self, connection: AGUIConnection) -> str:
        """Add new connection"""
        self.connections[connection.connection_id] = connection
        
        # Track by user
        if connection.user_id not in self.user_connections:
            self.user_connections[connection.user_id] = []
        self.user_connections[connection.user_id].append(connection.connection_id)
        
        # Track by task
        if connection.task_id:
            if connection.task_id not in self.task_connections:
                self.task_connections[connection.task_id] = []
            self.task_connections[connection.task_id].append(connection.connection_id)
        
        return connection.connection_id
    
    def remove_connection(self, connection_id: str):
        """Remove connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            # Remove from user tracking
            if connection.user_id in self.user_connections:
                if connection_id in self.user_connections[connection.user_id]:
                    self.user_connections[connection.user_id].remove(connection_id)
            
            # Remove from task tracking
            if connection.task_id and connection.task_id in self.task_connections:
                if connection_id in self.task_connections[connection.task_id]:
                    self.task_connections[connection.task_id].remove(connection_id)
            
            # Close and remove connection
            connection.close()
            del self.connections[connection_id]
    
    async def broadcast_to_user(self, user_id: str, event: AGUIEvent):
        """Broadcast event to all connections for a user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.connections:
                    await self.connections[connection_id].send_event(event)
    
    async def broadcast_to_task(self, task_id: str, event: AGUIEvent):
        """Broadcast event to all connections for a task"""
        if task_id in self.task_connections:
            for connection_id in self.task_connections[task_id]:
                if connection_id in self.connections:
                    await self.connections[connection_id].send_event(event)
    
    async def send_to_connection(self, connection_id: str, event: AGUIEvent):
        """Send event to specific connection"""
        if connection_id in self.connections:
            await self.connections[connection_id].send_event(event)

# Global AG-UI manager
agui_manager = AGUIManager()

# FastAPI app setup
app = FastAPI(title="ATLAS AG-UI Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ag-ui/stream")
async def ag_ui_stream(
    request: Request,
    userId: str,
    taskId: Optional[str] = None
):
    """AG-UI Server-Sent Events endpoint"""
    
    # Create new connection
    connection = AGUIConnection(user_id=userId, task_id=taskId)
    connection_id = agui_manager.add_connection(connection)
    
    # Send initial connection event
    await connection.send_event(AGUIEvent(
        type="CONNECTION_ESTABLISHED",
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "connectionId": connection_id,
            "userId": userId,
            "taskId": taskId
        }
    ))
    
    async def event_stream():
        try:
            async for event_data in connection.get_events():
                yield event_data
        except Exception as e:
            logging.error(f"Error in AG-UI stream: {e}")
        finally:
            agui_manager.remove_connection(connection_id)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/ag-ui/send")
async def ag_ui_send(event: AGUIEvent, userId: str):
    """Receive events from frontend"""
    
    # Add metadata if missing
    if not event.id:
        event.id = str(uuid.uuid4())
    if not event.timestamp:
        event.timestamp = datetime.now().isoformat()
    
    # Handle different event types
    if event.type == AGUIEventType.USER_INPUT:
        await handle_user_input(event, userId)
    elif event.type == AGUIEventType.USER_INTERRUPT:
        await handle_user_interrupt(event, userId)
    elif event.type == "START_TASK":
        await handle_start_task(event, userId)
    
    return {"status": "received"}

async def handle_user_input(event: AGUIEvent, user_id: str):
    """Handle user input event"""
    
    # Process user input through ATLAS system
    task_id = event.data.get("taskId")
    user_content = event.data.get("content")
    
    # Broadcast to task connections
    if task_id:
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.SYSTEM_MESSAGE,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "message": f"Processing user input: {user_content}",
                "userId": user_id
            }
        ))
        
        # Trigger ATLAS processing (implementation depends on your backend)
        await trigger_atlas_processing(task_id, user_content, user_id)

async def handle_user_interrupt(event: AGUIEvent, user_id: str):
    """Handle user interrupt event"""
    
    task_id = event.data.get("taskId")
    
    if task_id:
        # Broadcast interrupt to all task connections
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.AGENT_STATUS,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "status": "interrupted",
                "reason": "user_requested",
                "userId": user_id
            }
        ))
        
        # Stop ATLAS processing
        await stop_atlas_processing(task_id)

async def handle_start_task(event: AGUIEvent, user_id: str):
    """Handle start task event"""
    
    # Create new ATLAS task
    task = ATLASTask(
        id=str(uuid.uuid4()),
        description=event.data.get("description", ""),
        type=event.data.get("type", "general"),
        priority=event.data.get("priority", "normal"),
        user_id=user_id,
        teams=["research", "analysis", "writing"]  # Default teams
    )
    
    # Broadcast task started
    await agui_manager.broadcast_to_user(user_id, AGUIEvent(
        type=AGUIEventType.RUN_STARTED,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "task": asdict(task)
        }
    ))
    
    # Start ATLAS processing
    await start_atlas_task(task)

# ATLAS Integration Functions (to be implemented with actual ATLAS backend)
async def trigger_atlas_processing(task_id: str, user_input: str, user_id: str):
    """Trigger ATLAS multi-agent processing"""
    # Implementation depends on your ATLAS backend
    pass

async def stop_atlas_processing(task_id: str):
    """Stop ATLAS processing for a task"""
    # Implementation depends on your ATLAS backend
    pass

async def start_atlas_task(task: ATLASTask):
    """Start new ATLAS task"""
    # Implementation depends on your ATLAS backend
    pass

# AG-UI Event Broadcasting Functions
class ATLASAGUIBroadcaster:
    """Broadcasts ATLAS events through AG-UI protocol"""
    
    @staticmethod
    async def broadcast_agent_message(
        task_id: str,
        agent_id: str,
        content: str,
        streaming: bool = False
    ):
        """Broadcast agent text message"""
        
        event_type = AGUIEventType.TEXT_MESSAGE_START if streaming else AGUIEventType.TEXT_MESSAGE_CONTENT
        
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=event_type,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "agentId": agent_id,
                "content": content,
                "streaming": streaming
            }
        ))
    
    @staticmethod
    async def broadcast_tool_call_start(
        task_id: str,
        agent_id: str,
        tool_name: str,
        tool_args: Dict[str, Any]
    ):
        """Broadcast tool call start"""
        
        tool_call_id = str(uuid.uuid4())
        
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.TOOL_CALL_START,
            id=tool_call_id,
            timestamp=datetime.now().isoformat(),
            data={
                "toolCallId": tool_call_id,
                "agentId": agent_id,
                "toolName": tool_name,
                "args": tool_args
            }
        ))
        
        return tool_call_id
    
    @staticmethod
    async def broadcast_tool_call_end(
        task_id: str,
        tool_call_id: str,
        result: Any,
        success: bool = True
    ):
        """Broadcast tool call completion"""
        
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.TOOL_CALL_END,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "toolCallId": tool_call_id,
                "result": result,
                "success": success
            }
        ))
    
    @staticmethod
    async def broadcast_state_update(
        task_id: str,
        state_delta: Dict[str, Any]
    ):
        """Broadcast state update"""
        
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.STATE_DELTA,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "delta": state_delta
            }
        ))
    
    @staticmethod
    async def broadcast_agent_status(
        task_id: str,
        agent_id: str,
        status: str,
        details: Optional[str] = None
    ):
        """Broadcast agent status change"""
        
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.AGENT_STATUS,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "agentId": agent_id,
                "status": status,
                "details": details
            }
        ))
    
    @staticmethod
    async def broadcast_task_completion(
        task_id: str,
        result: Dict[str, Any]
    ):
        """Broadcast task completion"""
        
        await agui_manager.broadcast_to_task(task_id, AGUIEvent(
            type=AGUIEventType.RUN_FINISHED,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "result": result,
                "taskId": task_id
            }
        ))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 2. LangGraph Integration with AG-UI

```python
# backend/langgraph_agui_integration.py

from langgraph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresCheckpointSaver
from typing import TypedDict, Dict, Any, List
import asyncio
from ag_ui_server import ATLASAGUIBroadcaster
import time

class ATLASState(TypedDict):
    task_id: str
    task_description: str
    user_id: str
    current_step: str
    team_results: Dict[str, Any]
    completed_teams: List[str]
    global_context: Dict[str, Any]
    error_log: List[str]
    metadata: Dict[str, Any]

class LangGraphAGUIIntegration:
    """Integrates LangGraph workflows with AG-UI protocol"""
    
    def __init__(self, postgres_url: str):
        self.checkpointer = PostgresCheckpointSaver(postgres_url)
        self.broadcaster = ATLASAGUIBroadcaster()
        self.workflow_graph = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow with AG-UI integration"""
        
        workflow = StateGraph(ATLASState)
        
        # Add nodes
        workflow.add_node("global_supervisor", self._global_supervisor_node)
        workflow.add_node("research_team", self._research_team_node)
        workflow.add_node("analysis_team", self._analysis_team_node)
        workflow.add_node("writing_team", self._writing_team_node)
        workflow.add_node("rating_team", self._rating_team_node)
        
        # Add edges
        workflow.add_edge(START, "global_supervisor")
        workflow.add_conditional_edges(
            "global_supervisor",
            self._route_from_supervisor,
            {
                "research": "research_team",
                "analysis": "analysis_team",
                "writing": "writing_team",
                "rating": "rating_team",
                "end": END
            }
        )
        
        # Team completion routes back to supervisor
        for team in ["research_team", "analysis_team", "writing_team", "rating_team"]:
            workflow.add_edge(team, "global_supervisor")
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _global_supervisor_node(self, state: ATLASState) -> ATLASState:
        """Global supervisor with AG-UI broadcasting"""
        
        task_id = state["task_id"]
        
        # Broadcast supervisor status
        await self.broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="global_supervisor",
            status="thinking",
            details="Analyzing task and planning coordination"
        )
        
        # Broadcast thinking process
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="global_supervisor",
            content="🤔 Analyzing the task requirements and determining the best approach...",
            streaming=False
        )
        
        # Simulate supervisor reasoning
        await asyncio.sleep(2)  # Simulated thinking time
        
        # Determine next step
        completed_teams = state.get("completed_teams", [])
        
        if "research" not in completed_teams:
            next_step = "research"
            message = "📚 I'll start by having the research team gather relevant information."
        elif "analysis" not in completed_teams:
            next_step = "analysis"
            message = "📊 Now I'll have the analysis team interpret the research findings."
        elif "writing" not in completed_teams:
            next_step = "writing"
            message = "✍️ Time for the writing team to create the final content."
        elif "rating" not in completed_teams:
            next_step = "rating"
            message = "⭐ Finally, the rating team will evaluate the quality."
        else:
            next_step = "end"
            message = "✅ All teams have completed their work. Task finished!"
        
        # Broadcast decision
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="global_supervisor",
            content=message,
            streaming=False
        )
        
        # Update state
        state["current_step"] = next_step
        state["metadata"]["supervisor_decision"] = {
            "next_step": next_step,
            "reasoning": message,
            "timestamp": time.time()
        }
        
        # Broadcast state update
        await self.broadcaster.broadcast_state_update(
            task_id=task_id,
            state_delta={
                "current_step": next_step,
                "supervisor_status": "decision_made"
            }
        )
        
        return state
    
    async def _research_team_node(self, state: ATLASState) -> ATLASState:
        """Research team with AG-UI integration"""
        
        task_id = state["task_id"]
        
        # Broadcast team activation
        await self.broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="research_supervisor",
            status="active",
            details="Starting research phase"
        )
        
        # Broadcast research start
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="research_supervisor",
            content="🔍 Research Team activated. Beginning information gathering...",
            streaming=False
        )
        
        # Simulate tool calls
        tool_call_id_1 = await self.broadcaster.broadcast_tool_call_start(
            task_id=task_id,
            agent_id="research_worker_1",
            tool_name="web_search",
            tool_args={"query": state["task_description"], "max_results": 10}
        )
        
        # Simulate research work
        await asyncio.sleep(3)
        
        # Broadcast tool completion
        await self.broadcaster.broadcast_tool_call_end(
            task_id=task_id,
            tool_call_id=tool_call_id_1,
            result={
                "sources_found": 15,
                "key_insights": ["Market trends show growth", "Competition is increasing"],
                "quality_score": 4.2
            },
            success=True
        )
        
        # More tool calls...
        tool_call_id_2 = await self.broadcaster.broadcast_tool_call_start(
            task_id=task_id,
            agent_id="research_worker_2",
            tool_name="document_analysis",
            tool_args={"documents": ["doc1.pdf", "doc2.pdf"]}
        )
        
        await asyncio.sleep(2)
        
        await self.broadcaster.broadcast_tool_call_end(
            task_id=task_id,
            tool_call_id=tool_call_id_2,
            result={
                "documents_processed": 2,
                "key_findings": ["Industry regulations changing", "New opportunities emerging"],
                "confidence": 0.85
            },
            success=True
        )
        
        # Broadcast final research results
        research_results = {
            "summary": "Research phase completed successfully",
            "key_findings": [
                "Market trends show 15% growth potential",
                "3 main competitors identified",
                "Regulatory changes create opportunities"
            ],
            "sources": 15,
            "quality_score": 4.1
        }
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="research_supervisor",
            content=f"✅ Research completed! Found {research_results['sources']} sources with quality score {research_results['quality_score']}/5",
            streaming=False
        )
        
        # Update state
        state["team_results"]["research"] = research_results
        state["completed_teams"].append("research")
        
        # Broadcast state update
        await self.broadcaster.broadcast_state_update(
            task_id=task_id,
            state_delta={
                "research_completed": True,
                "research_quality": research_results["quality_score"]
            }
        )
        
        return state
    
    async def _analysis_team_node(self, state: ATLASState) -> ATLASState:
        """Analysis team with AG-UI integration"""
        
        task_id = state["task_id"]
        
        await self.broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="analysis_supervisor",
            status="active",
            details="Starting analysis phase"
        )
        
        # Get research results
        research_data = state["team_results"].get("research", {})
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="analysis_supervisor",
            content=f"📊 Analysis Team activated. Processing {research_data.get('sources', 0)} research sources...",
            streaming=False
        )
        
        # Simulate analysis work with streaming
        analysis_steps = [
            "Organizing research findings...",
            "Applying SWOT analysis framework...",
            "Identifying key patterns and trends...",
            "Generating strategic recommendations...",
            "Validating conclusions against data..."
        ]
        
        for step in analysis_steps:
            await self.broadcaster.broadcast_agent_message(
                task_id=task_id,
                agent_id="analysis_worker_1",
                content=step,
                streaming=True
            )
            await asyncio.sleep(1.5)
        
        # Final analysis results
        analysis_results = {
            "summary": "Comprehensive analysis completed",
            "swot_analysis": {
                "strengths": ["Strong market position", "Innovative technology"],
                "weaknesses": ["Limited resources", "Market presence"],
                "opportunities": ["Growing market", "Regulatory changes"],
                "threats": ["Increased competition", "Economic uncertainty"]
            },
            "recommendations": [
                "Focus on innovation",
                "Expand market presence",
                "Monitor competition"
            ],
            "confidence": 0.87,
            "quality_score": 4.3
        }
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="analysis_supervisor",
            content=f"✅ Analysis completed! Generated {len(analysis_results['recommendations'])} recommendations with {analysis_results['confidence']:.0%} confidence",
            streaming=False
        )
        
        # Update state
        state["team_results"]["analysis"] = analysis_results
        state["completed_teams"].append("analysis")
        
        await self.broadcaster.broadcast_state_update(
            task_id=task_id,
            state_delta={
                "analysis_completed": True,
                "analysis_confidence": analysis_results["confidence"]
            }
        )
        
        return state
    
    async def _writing_team_node(self, state: ATLASState) -> ATLASState:
        """Writing team with AG-UI integration"""
        
        task_id = state["task_id"]
        
        await self.broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="writing_supervisor",
            status="active",
            details="Starting writing phase"
        )
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="writing_supervisor",
            content="✍️ Writing Team activated. Creating comprehensive report...",
            streaming=False
        )
        
        # Simulate writing with streaming content
        writing_sections = [
            "# Executive Summary\n\nBased on our comprehensive research and analysis...",
            "\n\n## Key Findings\n\n1. Market growth potential: 15%\n2. Competitive landscape: 3 main players\n3. Regulatory environment: Favorable changes ahead",
            "\n\n## Strategic Recommendations\n\n### Focus on Innovation\nOur analysis indicates that innovation will be the key differentiator...",
            "\n\n### Market Expansion\nThe current market conditions present an excellent opportunity...",
            "\n\n## Conclusion\n\nThe strategic analysis reveals significant opportunities for growth..."
        ]
        
        full_content = ""
        for section in writing_sections:
            await self.broadcaster.broadcast_agent_message(
                task_id=task_id,
                agent_id="writing_worker_1",
                content=section,
                streaming=True
            )
            full_content += section
            await asyncio.sleep(2)
        
        writing_results = {
            "summary": "Strategic report generated",
            "document": full_content,
            "word_count": len(full_content.split()),
            "sections": 4,
            "quality_score": 4.5
        }
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="writing_supervisor",
            content=f"✅ Writing completed! Generated {writing_results['word_count']} word report with quality score {writing_results['quality_score']}/5",
            streaming=False
        )
        
        # Update state
        state["team_results"]["writing"] = writing_results
        state["completed_teams"].append("writing")
        
        await self.broadcaster.broadcast_state_update(
            task_id=task_id,
            state_delta={
                "writing_completed": True,
                "document_ready": True
            }
        )
        
        return state
    
    async def _rating_team_node(self, state: ATLASState) -> ATLASState:
        """Rating team with AG-UI integration"""
        
        task_id = state["task_id"]
        
        await self.broadcaster.broadcast_agent_status(
            task_id=task_id,
            agent_id="rating_supervisor",
            status="active",
            details="Starting quality evaluation"
        )
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="rating_supervisor",
            content="⭐ Rating Team activated. Evaluating overall quality...",
            streaming=False
        )
        
        # Evaluate each team's work
        evaluations = {}
        for team in ["research", "analysis", "writing"]:
            if team in state["team_results"]:
                team_score = state["team_results"][team].get("quality_score", 3.0)
                evaluations[team] = team_score
                
                await self.broadcaster.broadcast_agent_message(
                    task_id=task_id,
                    agent_id="rating_worker_1",
                    content=f"Evaluated {team} team: {team_score}/5.0",
                    streaming=False
                )
                await asyncio.sleep(1)
        
        # Calculate overall rating
        overall_score = sum(evaluations.values()) / len(evaluations) if evaluations else 0
        
        rating_results = {
            "summary": "Quality evaluation completed",
            "team_scores": evaluations,
            "overall_score": overall_score,
            "recommendations": [
                "Excellent research coverage",
                "Strong analytical framework",
                "Clear and comprehensive writing"
            ],
            "approved": overall_score >= 4.0
        }
        
        status_message = "✅ APPROVED" if rating_results["approved"] else "⚠️ NEEDS IMPROVEMENT"
        
        await self.broadcaster.broadcast_agent_message(
            task_id=task_id,
            agent_id="rating_supervisor",
            content=f"{status_message} - Overall quality score: {overall_score:.1f}/5.0",
            streaming=False
        )
        
        # Update state
        state["team_results"]["rating"] = rating_results
        state["completed_teams"].append("rating")
        
        await self.broadcaster.broadcast_state_update(
            task_id=task_id,
            state_delta={
                "rating_completed": True,
                "overall_score": overall_score,
                "task_approved": rating_results["approved"]
            }
        )
        
        return state
    
    def _route_from_supervisor(self, state: ATLASState) -> str:
        """Route from global supervisor"""
        current_step = state.get("current_step", "start")
        
        if current_step == "end":
            return "end"
        else:
            return current_step
    
    async def execute_task(self, initial_state: ATLASState) -> Dict[str, Any]:
        """Execute ATLAS task with AG-UI broadcasting"""
        
        task_id = initial_state["task_id"]
        
        # Broadcast task start
        await self.broadcaster.broadcast_task_start(
            task_id=task_id,
            task_data=initial_state
        )
        
        try:
            # Execute workflow
            final_state = await self.workflow_graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": task_id}}
            )
            
            # Broadcast completion
            await self.broadcaster.broadcast_task_completion(
                task_id=task_id,
                result={
                    "status": "completed",
                    "team_results": final_state["team_results"],
                    "overall_quality": final_state["team_results"].get("rating", {}).get("overall_score", 0)
                }
            )
            
            return final_state
            
        except Exception as e:
            # Broadcast error
            await self.broadcaster.broadcast_error(
                task_id=task_id,
                error=str(e)
            )
            raise

# Usage example
async def main():
    # Initialize LangGraph AG-UI integration
    langgraph_agui = LangGraphAGUIIntegration(
        postgres_url="postgresql://user:pass@localhost:5432/atlas"
    )
    
    # Create initial task state
    initial_state = ATLASState(
        task_id="task_123",
        task_description="Analyze market opportunities for AI products",
        user_id="user_456",
        current_step="start",
        team_results={},
        completed_teams=[],
        global_context={},
        error_log=[],
        metadata={}
    )
    
    # Execute task with real-time AG-UI updates
    result = await langgraph_agui.execute_task(initial_state)
    print(f"Task completed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive AG-UI guide provides the foundation for real-time frontend-backend communication in the ATLAS multi-agent system, leveraging the latest 2025 protocol features for seamless agent-user interaction, bidirectional communication, and live streaming of agent activities.