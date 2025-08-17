/**
 * API configuration for the ATLAS frontend
 */

export const API_CONFIG = {
  // Backend API base URL
  BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001',
  
  // WebSocket URL (derived from backend URL)
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001',
  
  // API endpoints
  endpoints: {
    // Letta endpoints
    lettaAgents: '/api/letta/agents',
    lettaAgent: (id: string) => `/api/letta/agents/${id}`,
    lettaMessages: (id: string) => `/api/letta/agents/${id}/messages`,
    lettaConversation: (id: string) => `/api/letta/agents/${id}/conversation`,
    lettaStream: (id: string) => `/api/letta/agents/${id}/stream`,
    
    // Task endpoints
    tasks: '/api/tasks',
    task: (id: string) => `/api/tasks/${id}`,
    
    // AG-UI endpoints
    aguiWebSocket: (taskId: string) => `/api/agui/ws/${taskId}`,
    aguiStream: (taskId: string) => `/api/agui/stream/${taskId}`,
    
    // Agent endpoints
    agents: '/api/agents',
    agent: (id: string) => `/api/agents/${id}`,
    
    // Health check
    health: '/health',
    root: '/'
  }
};

// Helper function to build full URL
export const buildUrl = (endpoint: string): string => {
  return `${API_CONFIG.BACKEND_URL}${endpoint}`;
};

// Helper function to build WebSocket URL
export const buildWsUrl = (endpoint: string): string => {
  return `${API_CONFIG.WS_URL}${endpoint}`;
};