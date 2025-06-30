export interface Agent {
  id: string
  title: string
  description: string
  status: 'active' | 'processing' | 'idle'
  type: 'supervisor' | 'worker'
  progress: number
  team?: string
}

export interface TaskProgress {
  name: string
  status: 'completed' | 'processing' | 'idle'
  icon: string
}

export interface Question {
  id: number
  agent: string
  question: string
  timestamp?: Date
}

export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'agent'
  agent?: string
  timestamp: Date
}