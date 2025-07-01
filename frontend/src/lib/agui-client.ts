// /Users/nicholaspate/Documents/ATLAS/frontend/src/lib/agui-client.ts

/**
 * ATLAS AG-UI Client
 * Provides real-time communication with the ATLAS backend using WebSockets and Server-Sent Events.
 */

export interface AGUIEvent {
  event_id: string
  event_type: string
  task_id: string
  agent_id?: string
  data: any
  timestamp: string
}

export interface AGUIConnectionOptions {
  baseUrl?: string
  reconnectAttempts?: number
  reconnectDelay?: number
  heartbeatInterval?: number
}

export interface AGUIEventHandler {
  (event: AGUIEvent): void
}

export class AGUIClient {
  private baseUrl: string
  private websocket: WebSocket | null = null
  private eventSource: EventSource | null = null
  private eventHandlers: Map<string, AGUIEventHandler[]> = new Map()
  private globalHandlers: AGUIEventHandler[] = []
  
  private reconnectAttempts: number
  private reconnectDelay: number
  private heartbeatInterval: number
  private currentTaskId: string | null = null
  
  private reconnectCount = 0
  private isConnected = false
  private heartbeatTimer: NodeJS.Timeout | null = null

  constructor(options: AGUIConnectionOptions = {}) {
    this.baseUrl = options.baseUrl || 'http://localhost:8000'
    this.reconnectAttempts = options.reconnectAttempts || 5
    this.reconnectDelay = options.reconnectDelay || 3000
    this.heartbeatInterval = options.heartbeatInterval || 30000
  }

  /**
   * Connect to the backend using WebSocket for bidirectional communication
   */
  async connectWebSocket(taskId: string): Promise<void> {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected')
      return
    }

    this.currentTaskId = taskId
    const wsUrl = this.baseUrl.replace('http', 'ws') + `/api/agui/ws/${taskId}`
    
    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(wsUrl)
        
        this.websocket.onopen = (event) => {
          console.log('AG-UI WebSocket connected:', event)
          this.isConnected = true
          this.reconnectCount = 0
          this.startHeartbeat()
          resolve()
        }
        
        this.websocket.onmessage = (event) => {
          try {
            const aguiEvent: AGUIEvent = JSON.parse(event.data)
            this.handleEvent(aguiEvent)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
        
        this.websocket.onclose = (event) => {
          console.log('AG-UI WebSocket disconnected:', event)
          this.isConnected = false
          this.stopHeartbeat()
          
          // Attempt to reconnect if not a clean close
          if (!event.wasClean && this.reconnectCount < this.reconnectAttempts) {
            this.reconnectCount++
            console.log(`Attempting to reconnect (${this.reconnectCount}/${this.reconnectAttempts})...`)
            setTimeout(() => this.connectWebSocket(taskId), this.reconnectDelay)
          }
        }
        
        this.websocket.onerror = (error) => {
          console.error('AG-UI WebSocket error:', error)
          reject(error)
        }
        
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Connect using Server-Sent Events for one-way communication (server to client)
   */
  async connectSSE(taskId: string): Promise<void> {
    if (this.eventSource?.readyState === EventSource.OPEN) {
      console.warn('SSE already connected')
      return
    }

    this.currentTaskId = taskId
    const sseUrl = `${this.baseUrl}/api/agui/stream/${taskId}`
    
    return new Promise((resolve, reject) => {
      try {
        this.eventSource = new EventSource(sseUrl)
        
        this.eventSource.onopen = (event) => {
          console.log('AG-UI SSE connected:', event)
          this.isConnected = true
          this.reconnectCount = 0
          resolve()
        }
        
        this.eventSource.onmessage = (event) => {
          try {
            const aguiEvent: AGUIEvent = JSON.parse(event.data)
            this.handleEvent(aguiEvent)
          } catch (error) {
            console.error('Failed to parse SSE message:', error)
          }
        }
        
        this.eventSource.onerror = (error) => {
          console.error('AG-UI SSE error:', error)
          this.isConnected = false
          
          // Attempt to reconnect
          if (this.reconnectCount < this.reconnectAttempts) {
            this.reconnectCount++
            console.log(`Attempting to reconnect SSE (${this.reconnectCount}/${this.reconnectAttempts})...`)
            this.eventSource?.close()
            setTimeout(() => this.connectSSE(taskId), this.reconnectDelay)
          } else {
            reject(error)
          }
        }
        
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Send a message to the backend via WebSocket
   */
  async sendMessage(message: any): Promise<void> {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected')
    }
    
    this.websocket.send(JSON.stringify(message))
  }

  /**
   * Send user input to a specific agent
   */
  async sendUserInput(input: string, targetAgent?: string): Promise<void> {
    await this.sendMessage({
      type: 'user_input',
      data: {
        input,
        target_agent: targetAgent
      }
    })
  }

  /**
   * Request agent interruption
   */
  async interruptAgent(agentId: string): Promise<void> {
    await this.sendMessage({
      type: 'agent_interrupt',
      agent_id: agentId
    })
  }

  /**
   * Send task control command
   */
  async controlTask(action: 'pause' | 'resume' | 'cancel'): Promise<void> {
    await this.sendMessage({
      type: 'task_control',
      action
    })
  }

  /**
   * Register an event handler for a specific event type
   */
  on(eventType: string, handler: AGUIEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, [])
    }
    this.eventHandlers.get(eventType)!.push(handler)
  }

  /**
   * Register a global event handler that receives all events
   */
  onAny(handler: AGUIEventHandler): void {
    this.globalHandlers.push(handler)
  }

  /**
   * Remove an event handler
   */
  off(eventType: string, handler: AGUIEventHandler): void {
    const handlers = this.eventHandlers.get(eventType)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * Remove a global event handler
   */
  offAny(handler: AGUIEventHandler): void {
    const index = this.globalHandlers.indexOf(handler)
    if (index > -1) {
      this.globalHandlers.splice(index, 1)
    }
  }

  /**
   * Disconnect from the backend
   */
  disconnect(): void {
    this.isConnected = false
    this.stopHeartbeat()
    
    if (this.websocket) {
      this.websocket.close()
      this.websocket = null
    }
    
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    
    console.log('AG-UI client disconnected')
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): {
    isConnected: boolean
    connectionType: 'websocket' | 'sse' | 'none'
    taskId: string | null
  } {
    let connectionType: 'websocket' | 'sse' | 'none' = 'none'
    
    if (this.websocket?.readyState === WebSocket.OPEN) {
      connectionType = 'websocket'
    } else if (this.eventSource?.readyState === EventSource.OPEN) {
      connectionType = 'sse'
    }
    
    return {
      isConnected: this.isConnected,
      connectionType,
      taskId: this.currentTaskId
    }
  }

  private handleEvent(event: AGUIEvent): void {
    // Call global handlers
    this.globalHandlers.forEach(handler => {
      try {
        handler(event)
      } catch (error) {
        console.error('Error in global event handler:', error)
      }
    })
    
    // Call specific event handlers
    const handlers = this.eventHandlers.get(event.event_type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(event)
        } catch (error) {
          console.error(`Error in ${event.event_type} event handler:`, error)
        }
      })
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'ping' }).catch(console.error)
      }
    }, this.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

// Convenience functions for common event types

export function createDialogueUpdateHandler(
  callback: (agentId: string, message: any) => void
): AGUIEventHandler {
  return (event: AGUIEvent) => {
    if (event.event_type === 'agent_dialogue_update' && event.agent_id) {
      callback(event.agent_id, event.data)
    }
  }
}

export function createAgentStatusHandler(
  callback: (agentId: string, oldStatus: string, newStatus: string) => void
): AGUIEventHandler {
  return (event: AGUIEvent) => {
    if (event.event_type === 'agent_status_changed' && event.agent_id) {
      callback(event.agent_id, event.data.old_status, event.data.new_status)
    }
  }
}

export function createTaskProgressHandler(
  callback: (progress: number, phase: string, message: string) => void
): AGUIEventHandler {
  return (event: AGUIEvent) => {
    if (event.event_type === 'task_progress') {
      callback(
        event.data.progress_percentage,
        event.data.current_phase,
        event.data.message
      )
    }
  }
}

export function createContentGeneratedHandler(
  callback: (agentId: string, contentType: string, size: number) => void
): AGUIEventHandler {
  return (event: AGUIEvent) => {
    if (event.event_type === 'content_generated' && event.agent_id) {
      callback(
        event.agent_id,
        event.data.content_type,
        event.data.content_size_bytes
      )
    }
  }
}