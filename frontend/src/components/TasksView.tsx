'use client'

import { useState, useEffect, useRef } from 'react'
import AgentArchitecture from './AgentArchitecture'
import AgentMessageBox from './AgentMessageBox'
import ChatBar from './ChatBar'
import QuestionsPanel from './QuestionsPanel'
import ProjectSelector, { Project } from './ProjectSelector'
import ToolCallBox from './ToolCallBox'
import StreamingMessage from './StreamingMessage'
import TaskWebSocketClient from '../lib/websocket-client'
import { chatApi, ChatMessage, formatChatTimestamp } from '../lib/chat-api'

interface Task {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  status: 'active' | 'completed' | 'failed';
  agent_type: string;
}

interface TasksViewProps {
  selectedTask: Task | string | null;
  onTaskCreated?: (task: Task) => void;
}

interface ToolCall {
  id: string
  toolName: string
  arguments?: any
  status: 'pending' | 'executing' | 'complete' | 'failed'
  result?: any
  executionTime?: number
  timestamp: string
}

interface ExtendedChatMessage {
  id: string | number
  type: 'user' | 'agent' | 'system' | 'tool_call'
  content?: string
  toolCall?: ToolCall
  timestamp: string
  agent_id?: string
}

export default function TasksView({ selectedTask, onTaskCreated }: TasksViewProps) {
  const [currentTask, setCurrentTask] = useState<Task | null>(null)
  const [isCreatingTask, setIsCreatingTask] = useState(false)
  const [chatMessages, setChatMessages] = useState<ExtendedChatMessage[]>([])
  const [persistentChatHistory, setPersistentChatHistory] = useState<ChatMessage[]>([])
  const [isLoadingChatHistory, setIsLoadingChatHistory] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [isAgentTyping, setIsAgentTyping] = useState(false)
  const [typingAgentId, setTypingAgentId] = useState<string | null>(null)
  const [toolCalls, setToolCalls] = useState<Map<string, ToolCall>>(new Map())
  const [streamingContent, setStreamingContent] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [thinkingContent, setThinkingContent] = useState<string>('')
  const [isThinking, setIsThinking] = useState(false)
  const wsClient = useRef<TaskWebSocketClient | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  
  // Helper function to safely format content for display
  const formatMessageContent = (content: any): string => {
    if (typeof content === 'string') {
      return content
    } else if (typeof content === 'object' && content !== null) {
      try {
        // For structured responses, create a readable format
        if (content.task_summary) {
          // This is a Global Supervisor response
          const summary = content.task_summary
          const deliverables = content.deliverables
          const metrics = content.quality_metrics
          
          return `**Task Completed Successfully!**

**Original Request:** ${summary.original_request}
**Status:** ${summary.completion_status}
**Teams Involved:** ${summary.teams_involved}

**Strategy Used:** ${content.execution_summary?.strategy_used || 'Not specified'}

**Key Deliverables:**
${deliverables?.coordination_plan || 'Task coordination completed'}

**Quality Metrics:**
- Delegation Success Rate: ${((metrics?.delegation_success_rate || 0) * 100).toFixed(0)}%
- Global Confidence: ${((metrics?.global_confidence || 0) * 100).toFixed(0)}%

**Next Steps:** ${deliverables?.next_steps || 'Ready for team execution'}`
        }
        
        // Fallback to JSON for other objects
        return JSON.stringify(content, null, 2)
      } catch (error) {
        return String(content)
      }
    } else {
      return String(content)
    }
  }
  
  // Load chat history for existing task
  const loadChatHistory = async (taskId: string) => {
    setIsLoadingChatHistory(true)
    try {
      const chatHistory = await chatApi.getTaskChatHistory(taskId)
      setPersistentChatHistory(chatHistory)
      
      // Convert chat history to display format
      const formattedMessages = chatHistory.map((msg, index) => ({
        id: msg.id,
        type: msg.message_type,
        content: formatMessageContent(msg.content),
        timestamp: msg.timestamp,
        agent_id: msg.agent_id
      }))
      
      setChatMessages(formattedMessages)
      console.log(`Loaded ${chatHistory.length} messages from chat history`)
    } catch (error) {
      console.error('Failed to load chat history:', error)
      setPersistentChatHistory([])
      setChatMessages([])
    } finally {
      setIsLoadingChatHistory(false)
    }
  }
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])
  
  // Handle task selection
  useEffect(() => {
    if (typeof selectedTask === 'string' && selectedTask.startsWith('new')) {
      setIsCreatingTask(true)
      setCurrentTask(null)
      setChatMessages([])
      setToolCalls(new Map())
      setIsAgentTyping(false)
      setTypingAgentId(null)
      // Disconnect any existing WebSocket
      if (wsClient.current) {
        wsClient.current.disconnect()
        wsClient.current = null
      }
      setConnectionStatus('disconnected')
    } else if (selectedTask && typeof selectedTask === 'object') {
      setIsCreatingTask(false)
      setCurrentTask(selectedTask)
      setToolCalls(new Map())
      setIsAgentTyping(false)
      setTypingAgentId(null)
      // Load chat history for existing task
      loadChatHistory(selectedTask.id)
      // Connect to WebSocket for existing task
      connectToTask(selectedTask.id)
    }
  }, [selectedTask])

  // Connect to WebSocket for real-time updates
  const connectToTask = async (taskId: string) => {
    try {
      if (wsClient.current) {
        wsClient.current.disconnect()
      }
      
      setConnectionStatus('connecting')
      wsClient.current = new TaskWebSocketClient(taskId)
      
      // Set up message handlers
      wsClient.current.onMessage('agent_connected', (message) => {
        console.log('Agent connected:', message)
        setChatMessages(prev => [...prev, {
          id: Date.now(),
          type: 'system',
          content: `Connected to ${message.agent_id}`,
          timestamp: message.timestamp
        }])
      })
      
      // Handle agent typing indicators
      wsClient.current.onMessage('agent_status_changed', (message) => {
        if (message.data?.new_status === 'typing' || message.data?.new_status === 'active' || message.data?.new_status === 'processing') {
          setIsAgentTyping(true)
          setTypingAgentId(message.agent_id || null)
        } else if (message.data?.new_status === 'idle' || message.data?.new_status === 'completed') {
          setIsAgentTyping(false)
          setTypingAgentId(null)
          setIsStreaming(false)
        }
      })
      
      // Handle thinking updates
      wsClient.current.onMessage('agent_thinking_update', (message) => {
        if (message.data?.thinking_status === 'started') {
          setIsThinking(true)
          setThinkingContent('')
        } else if (message.data?.thinking_status === 'chunk') {
          setThinkingContent(prev => prev + message.data.thinking_content)
        } else if (message.data?.thinking_status === 'complete') {
          setIsThinking(false)
          // Optionally show complete thinking in a collapsed box
          console.log('Agent thinking:', message.data.thinking_content)
        }
      })
      
      // Handle streaming content
      wsClient.current.onMessage('agent_content_stream', (message) => {
        if (message.data?.stream_status === 'started') {
          setIsStreaming(true)
          setStreamingContent('')
          setIsAgentTyping(true)
          setTypingAgentId(message.agent_id)
        } else if (message.data?.stream_status === 'chunk') {
          setStreamingContent(prev => prev + message.data.content)
        } else if (message.data?.stream_status === 'complete') {
          // Add complete message to chat
          setChatMessages(prev => [...prev, {
            id: Date.now(),
            type: 'agent',
            content: message.data.full_content || streamingContent,
            timestamp: message.timestamp,
            agent_id: message.agent_id
          }])
          setIsStreaming(false)
          setStreamingContent('')
          setIsAgentTyping(false)
        }
      })
      
      // Handle tool streaming updates
      wsClient.current.onMessage('tool_call_stream_update', (message) => {
        if (message.data?.status === 'started') {
          // Show tool being constructed
          console.log('Tool call starting:', message.data.tool_name)
        } else if (message.data?.status === 'ready') {
          // Tool call is ready to execute
          console.log('Tool call ready:', message.data)
        }
      })

      wsClient.current.onMessage('status_acknowledged', (message) => {
        console.log('Status update:', message)
        // Update task status if needed
        if (message.data.status) {
          setCurrentTask(prev => prev ? { ...prev, status: message.data.status } : null)
        }
      })

      wsClient.current.onMessage('dialogue_acknowledged', (message) => {
        console.log('Dialogue update:', message)
        setChatMessages(prev => [...prev, {
          id: Date.now(),
          type: 'agent',
          content: formatMessageContent(message.data.message || 'Processing your request...'),
          timestamp: message.timestamp,
          agent_id: message.agent_id
        }])
      })

      wsClient.current.onMessage('agent_dialogue_update', (message) => {
        console.log('Agent dialogue update:', message)
        
        // Handle both user and agent messages from WebSocket
        if (message.data && message.data.direction === 'input' && message.data.sender === 'user') {
          // Skip user messages since we already add them immediately when sent
          return
        }
        
        if (message.data && message.data.content && message.data.content.data) {
          setChatMessages(prev => {
            const newContent = formatMessageContent(message.data.content.data)
            
            // More precise duplicate detection - check for exact timestamp matches only
            // This prevents legitimate responses from being filtered out
            const exists = prev.some(msg => 
              msg.agent_id === message.agent_id && 
              msg.content === newContent &&
              msg.timestamp === message.timestamp  // Exact timestamp match only
            )
            
            if (exists) {
              console.log('Exact duplicate message detected, skipping')
              return prev
            }
            
            // Hide typing indicator when agent response arrives
            setIsAgentTyping(false)
            setTypingAgentId(null)
            
            console.log('Adding agent message to chat:', {
              agent_id: message.agent_id,
              content: newContent.substring(0, 100) + '...',
              timestamp: message.timestamp
            })
            
            return [...prev, {
              id: Date.now(),
              type: 'agent',
              content: newContent,
              timestamp: message.timestamp,
              agent_id: message.agent_id || 'unknown_agent'
            }]
          })
        }
      })

      // Tool call event handlers
      wsClient.current.onMessage('tool_call_initiated', (message) => {
        console.log('Tool call initiated:', message)
        const toolCallId = message.data.tool_call_id
        const toolCall: ToolCall = {
          id: toolCallId,
          toolName: message.data.tool_name,
          arguments: message.data.arguments,
          status: 'pending',
          timestamp: message.data.initiated_at || message.timestamp
        }
        
        // Update tool calls map
        setToolCalls(prev => {
          const newMap = new Map(prev)
          newMap.set(toolCallId, toolCall)
          return newMap
        })
        
        // Add to chat messages
        setChatMessages(prev => [...prev, {
          id: `tool_${toolCallId}`,
          type: 'tool_call',
          toolCall: toolCall,
          timestamp: toolCall.timestamp,
          agent_id: message.agent_id
        }])
      })

      wsClient.current.onMessage('tool_call_executing', (message) => {
        console.log('Tool call executing:', message)
        const toolCallId = message.data.tool_call_id
        
        // Update tool call status
        setToolCalls(prev => {
          const newMap = new Map(prev)
          const toolCall = newMap.get(toolCallId)
          if (toolCall) {
            toolCall.status = 'executing'
            newMap.set(toolCallId, { ...toolCall })
          }
          return newMap
        })
        
        // Update existing message
        setChatMessages(prev => prev.map(msg => {
          if (msg.type === 'tool_call' && msg.toolCall?.id === toolCallId) {
            return {
              ...msg,
              toolCall: {
                ...msg.toolCall,
                status: 'executing'
              }
            }
          }
          return msg
        }))
      })

      wsClient.current.onMessage('tool_call_completed', (message) => {
        console.log('Tool call completed:', message)
        const toolCallId = message.data.tool_call_id
        
        // Update tool call with result
        setToolCalls(prev => {
          const newMap = new Map(prev)
          const toolCall = newMap.get(toolCallId)
          if (toolCall) {
            toolCall.status = 'complete'
            toolCall.result = message.data.result
            toolCall.executionTime = message.data.execution_time_ms
            newMap.set(toolCallId, { ...toolCall })
          }
          return newMap
        })
        
        // Update existing message
        setChatMessages(prev => prev.map(msg => {
          if (msg.type === 'tool_call' && msg.toolCall?.id === toolCallId) {
            return {
              ...msg,
              toolCall: {
                ...msg.toolCall,
                status: 'complete',
                result: message.data.result,
                executionTime: message.data.execution_time_ms
              }
            }
          }
          return msg
        }))
      })

      wsClient.current.onMessage('tool_call_failed', (message) => {
        console.log('Tool call failed:', message)
        const toolCallId = message.data.tool_call_id
        
        // Update tool call status
        setToolCalls(prev => {
          const newMap = new Map(prev)
          const toolCall = newMap.get(toolCallId)
          if (toolCall) {
            toolCall.status = 'failed'
            toolCall.result = { error: message.data.error_message }
            newMap.set(toolCallId, { ...toolCall })
          }
          return newMap
        })
        
        // Update existing message
        setChatMessages(prev => prev.map(msg => {
          if (msg.type === 'tool_call' && msg.toolCall?.id === toolCallId) {
            return {
              ...msg,
              toolCall: {
                ...msg.toolCall,
                status: 'failed',
                result: { error: message.data.error_message }
              }
            }
          }
          return msg
        }))
      })

      wsClient.current.onAnyMessage((message) => {
        console.log('WebSocket message received:', message)
        if (message.event_type && message.event_type.includes('tool_call')) {
          console.log('TOOL CALL EVENT:', message)
        }
      })

      await wsClient.current.connect()
      setConnectionStatus('connected')
      
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
      setConnectionStatus('disconnected')
    }
  }

  // Polling function for task status as fallback
  const pollTaskStatus = async (taskId: string) => {
    let attempts = 0
    const maxAttempts = 60 // Poll for up to 10 minutes (10 seconds * 60)
    
    const poll = async () => {
      try {
        console.log(`Polling task status for ${taskId}, attempt ${attempts + 1}`)
        const response = await fetch(`http://localhost:8000/api/tasks/${taskId}/status`)
        
        if (response.ok) {
          const taskStatus = await response.json()
          console.log('Task status response:', taskStatus)
          
          // If task is completed and we have results, check if we need to add the response
          if (taskStatus.status === 'completed' && taskStatus.results) {
            console.log('Task completed, checking for agent response...')
            
            // Check if we already have an agent response (avoid duplicates)
            const hasAgentResponse = chatMessages.some(msg => 
              msg.type === 'agent' && msg.agent_id === 'global_supervisor' && 
              !msg.content.includes('Waiting for Global Supervisor')
            )
            
            console.log('Has agent response already:', hasAgentResponse)
            console.log('Task results content:', taskStatus.results.content)
            
            if (!hasAgentResponse && taskStatus.results.content) {
              console.log('Adding agent response to chat')
              setChatMessages(prev => {
                // Remove the "waiting" message and add the real response
                const filtered = prev.filter(msg => !msg.content.includes('Waiting for Global Supervisor'))
                return [...filtered, {
                  id: Date.now(),
                  type: 'agent',
                  content: formatMessageContent(taskStatus.results.content),
                  timestamp: new Date().toISOString(),
                  agent_id: 'global_supervisor'
                }]
              })
            }
            return // Stop polling when completed
          }
          
          // Continue polling if not completed yet
          attempts++
          if (attempts < maxAttempts && (taskStatus.status === 'running' || taskStatus.status === 'created' || taskStatus.status === 'active')) {
            setTimeout(poll, 5000) // Poll every 5 seconds
          } else if (attempts >= maxAttempts) {
            console.log('Max polling attempts reached')
          }
        } else {
          console.error(`Task status request failed: ${response.status}`)
        }
      } catch (error) {
        console.error('Error polling task status:', error)
      }
    }
    
    // Start polling immediately, then every 5 seconds
    poll()
  }

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsClient.current) {
        wsClient.current.disconnect()
      }
    }
  }, [])
  
  // Mock projects data
  const [projects] = useState<Project[]>([
    {
      id: 'market-analysis-q4-2024',
      name: 'Q4 2024 Tech Market Analysis',
      status: 'active',
      description: 'Comprehensive analysis of technology market trends for Q4 2024',
      lastActive: '2 minutes ago'
    },
    {
      id: 'competitor-analysis-saas',
      name: 'SaaS Competitor Analysis',
      status: 'completed',
      description: 'Deep dive into competitive landscape for SaaS productivity tools',
      lastActive: '3 days ago'
    },
    {
      id: 'investment-memo-ai-startups',
      name: 'AI Startups Investment Memo',
      status: 'paused',
      description: 'Investment analysis for early-stage AI companies',
      lastActive: '1 week ago'
    },
    {
      id: 'product-requirements-mobile',
      name: 'Mobile App PRD',
      status: 'active',
      description: 'Product requirements document for new mobile application',
      lastActive: '1 hour ago'
    }
  ])

  const [selectedProject, setSelectedProject] = useState<Project | null>(projects[0])
  
  const [taskProgress, setTaskProgress] = useState([
    { name: 'Research Phase', status: 'completed', icon: '✓' },
    { name: 'Analysis Phase', status: 'processing', icon: '⏳' },
    { name: 'Writing Phase', status: 'idle', icon: '⏸' },
    { name: 'Rating Phase', status: 'idle', icon: '⏸' },
  ])

  const createNewTask = async (message: string) => {
    try {
      // Call backend API to create new task
      const response = await fetch('http://localhost:8000/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_type: 'general_analysis',
          description: message,
          priority: 'medium',
          context: {}
        }),
      })
      
      if (response.ok) {
        const taskData = await response.json()
        
        // Start the task
        await fetch(`http://localhost:8000/api/tasks/${taskData.task_id}/start`, {
          method: 'POST',
        })
        
        // Update current task state
        const newTask: Task = {
          id: taskData.task_id,
          name: message.slice(0, 50) + (message.length > 50 ? '...' : ''),
          description: message,
          created_at: new Date().toISOString(),
          status: 'active',
          agent_type: 'global_supervisor'
        }
        
        setCurrentTask(newTask)
        setIsCreatingTask(false)
        
        // Notify parent component about the new task
        if (onTaskCreated) {
          onTaskCreated(newTask)
        }
        
        // Add initial user message to chat
        setChatMessages([
          {
            id: 1,
            type: 'user',
            content: message,
            timestamp: new Date().toISOString()
          },
          {
            id: 2,
            type: 'system',
            content: 'Task created successfully! Waiting for Global Supervisor response...',
            timestamp: new Date().toISOString()
          }
        ])

        // Connect to WebSocket for real-time updates
        await connectToTask(taskData.task_id)
        
        // Also start polling for task status as a fallback
        pollTaskStatus(taskData.task_id)
      }
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  const sendMessage = async (message: string) => {
    if (!currentTask) return
    
    // Add user message to chat immediately for responsiveness
    const userMessage: ExtendedChatMessage = {
      id: Date.now(),
      type: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }
    
    setChatMessages(prev => [...prev, userMessage])
    
    // Immediately show typing indicator
    setIsAgentTyping(true)
    setTypingAgentId('global_supervisor')
    
    try {
      // Send message via new chat endpoint that handles both DB and WebSocket
      const response = await fetch(`http://localhost:8000/api/chat/${currentTask.id}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message_type: 'user',
          content: message,
          metadata: {
            task_id: currentTask.id,
            user_id: 'default_user'
          }
        }),
      })
      
      if (!response.ok) {
        console.error('Failed to send message:', response.status)
      }
      
      // Also send to task input endpoint for processing
      await fetch(`http://localhost:8000/api/tasks/${currentTask.id}/input`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          agent_id: 'global_supervisor',
          context: {}
        }),
      })
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const handleChatSubmit = (message: string) => {
    if (isCreatingTask || (typeof selectedTask === 'string' && selectedTask.startsWith('new'))) {
      createNewTask(message)
    } else {
      sendMessage(message)
    }
  }

  if (isCreatingTask) {
    return (
      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto pb-24">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-2xl font-bold text-text">
                New Task
              </h1>
            </div>

            {/* New Task Interface */}
            <div className="max-w-4xl mx-auto">
              <div className="bg-card-glass glass-effect rounded-xl border border-border p-8 text-center">
                <div className="mb-6">
                  <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">🤖</span>
                  </div>
                  <h2 className="text-xl font-semibold text-text mb-2">
                    Start a New Task with Global Supervisor
                  </h2>
                  <p className="text-muted">
                    Describe what you&apos;d like to accomplish. The Global Supervisor will coordinate with specialized teams to complete your task.
                  </p>
                </div>
                
                <div className="text-left bg-background/50 rounded-lg p-4 mb-6">
                  <h3 className="font-medium text-text mb-2">Example tasks:</h3>
                  <ul className="text-sm text-muted space-y-1">
                    <li>• &quot;Analyze the competitive landscape for AI productivity tools&quot;</li>
                    <li>• &quot;Create a market research report on sustainable energy trends&quot;</li>
                    <li>• &quot;Write a technical specification for a mobile app feature&quot;</li>
                    <li>• &quot;Research and summarize the latest developments in quantum computing&quot;</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Bar for new task creation */}
        <div className="fixed bottom-0 left-64 right-0 z-10">
          <ChatBar 
            onSubmit={handleChatSubmit}
            placeholder="Describe your task..."
            submitText="Create Task"
          />
        </div>
      </div>
    )
  }

  if (currentTask) {
    return (
      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto pb-24">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <div>
                <h1 className="text-2xl font-bold text-text">
                  {currentTask.name}
                </h1>
                <p className="text-muted text-sm mt-1">
                  Task ID: {currentTask.id} • Status: {currentTask.status}
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  currentTask.status === 'active' ? 'bg-green-500/20 text-green-400' :
                  currentTask.status === 'completed' ? 'bg-blue-500/20 text-blue-400' :
                  'bg-red-500/20 text-red-400'
                }`}>
                  {currentTask.status}
                </span>
                
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  connectionStatus === 'connected' ? 'bg-green-500/20 text-green-400' :
                  connectionStatus === 'connecting' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {connectionStatus === 'connected' ? '🟢 Connected' : 
                   connectionStatus === 'connecting' ? '🟡 Connecting' : '⚪ Disconnected'}
                </span>
              </div>
            </div>

            {/* Chat History */}
            <div className="bg-card-glass glass-effect rounded-xl border border-border p-6">
              <h3 className="font-semibold text-text mb-4">Conversation with Global Supervisor</h3>
              
              {isLoadingChatHistory ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse">
                      <div className="flex space-x-3">
                        <div className="w-8 h-8 bg-gray-700 rounded-full"></div>
                        <div className="flex-1">
                          <div className="h-4 bg-gray-700 rounded w-1/4 mb-2"></div>
                          <div className="h-16 bg-gray-700 rounded"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : chatMessages.length === 0 ? (
                <div className="text-center text-muted py-8">
                  <p>No messages yet. Start the conversation below.</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {chatMessages.map((message) => {
                    if (message.type === 'tool_call' && message.toolCall) {
                      return (
                        <ToolCallBox
                          key={message.id}
                          id={message.toolCall.id}
                          toolName={message.toolCall.toolName}
                          arguments={message.toolCall.arguments}
                          status={message.toolCall.status}
                          result={message.toolCall.result}
                          executionTime={message.toolCall.executionTime}
                          timestamp={message.toolCall.timestamp}
                        />
                      )
                    }
                    
                    return (
                      <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {message.type === 'agent' ? (
                          <AgentMessageBox 
                            agentId={message.agent_id || 'unknown'}
                            content={message.content || ''}
                            timestamp={message.timestamp}
                          />
                        ) : (
                          <div className={`max-w-xs lg:max-w-md ${
                            message.type === 'user' 
                              ? 'bg-primary text-white px-4 py-2 rounded-lg' 
                              : 'bg-yellow-500/10 text-yellow-400 px-3 py-1 rounded-md text-sm italic'
                          }`}>
                            <div className="text-sm whitespace-pre-wrap" 
                                 dangerouslySetInnerHTML={{
                                   __html: (message.content || '')
                                     .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                     .replace(/\n/g, '<br>')
                                 }}
                            />
                            <p className="text-xs opacity-70 mt-1">
                              {new Date(message.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        )}
                      </div>
                    )
                  })}
                  
                  {/* Thinking Indicator */}
                  {isThinking && (
                    <div className="flex justify-start mb-4">
                      <div className="max-w-lg">
                        <StreamingMessage
                          content={thinkingContent}
                          isThinking={true}
                          isComplete={false}
                        />
                      </div>
                    </div>
                  )}
                  
                  {/* Streaming Message */}
                  {isStreaming && !isThinking && (
                    <div className="flex justify-start">
                      <AgentMessageBox 
                        agentId={typingAgentId || 'global_supervisor'}
                        content={streamingContent}
                        timestamp={new Date().toISOString()}
                        isTyping={false}
                      />
                    </div>
                  )}
                  
                  {/* Regular Typing Indicator */}
                  {isAgentTyping && !isStreaming && !isThinking && typingAgentId && (
                    <div className="flex justify-start">
                      <AgentMessageBox 
                        agentId={typingAgentId}
                        content=""
                        timestamp={new Date().toISOString()}
                        isTyping={true}
                      />
                    </div>
                  )}
                  
                  {/* Scroll anchor */}
                  <div ref={chatEndRef} />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar - Questions Panel */}
        <QuestionsPanel />

        {/* Chat Bar for ongoing conversation */}
        <div className="fixed bottom-0 left-64 right-80 z-10">
          <ChatBar 
            onSubmit={handleChatSubmit}
            placeholder="Continue the conversation..."
            submitText="Send"
          />
        </div>
      </div>
    )
  }

  // Default view when no task is selected
  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Main Content Area with Right Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Scrollable Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto pb-24">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-2xl font-bold text-text">
                Tasks Monitor
              </h1>
              
              {/* Task Progress Dropdown */}
              <div className="relative">
                <button className="bg-card-glass glass-effect px-4 py-2 rounded-xl border border-border text-text hover:bg-card-bg transition-colors">
                  Task Progress ▼
                </button>
                {/* Progress dropdown content - implement later */}
              </div>
            </div>

            {/* Project Selector */}
            <ProjectSelector
              projects={projects}
              selectedProject={selectedProject}
              onProjectChange={setSelectedProject}
            />

            {/* Agent Architecture - Main scrollable content */}
            <AgentArchitecture selectedProjectId={selectedProject?.id} />
          </div>
        </div>

        {/* Right Sidebar - Questions Panel */}
        <QuestionsPanel />
      </div>

      {/* Chat Bar - Fixed at bottom */}
      <ChatBar />
    </div>
  )
}