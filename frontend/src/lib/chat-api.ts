/**
 * Chat API Client for ATLAS Frontend
 * Provides functions to interact with chat persistence backend
 */

const API_BASE_URL = 'http://localhost:8000';

export interface ChatMessage {
  id: string;
  message_type: 'user' | 'agent' | 'system';
  content: string;
  agent_id?: string;
  timestamp: string;
  metadata: Record<string, any>;
  tokens_used: number;
  cost_usd: number;
  processing_time_ms: number;
  model_used?: string;
  response_quality?: number;
}

export interface ChatSession {
  id: string;
  task_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  status: string;
  mlflow_run_id?: string;
  metadata: Record<string, any>;
  message_count: number;
  total_tokens: number;
  total_cost_usd: number;
}

export interface RecentSession {
  id: string;
  task_id: string;
  created_at: string;
  status: string;
  message_count: number;
  total_tokens: number;
  total_cost_usd: number;
  last_message?: {
    content: string;
    timestamp: string;
    type: string;
  };
}

class ChatApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get chat history for a specific task
   */
  async getTaskChatHistory(taskId: string, userId: string = 'default_user'): Promise<ChatMessage[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat/tasks/${taskId}/history?user_id=${userId}`
      );
      
      if (!response.ok) {
        if (response.status === 404) {
          return []; // No chat history found
        }
        throw new Error(`Failed to fetch chat history: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching task chat history:', error);
      return [];
    }
  }

  /**
   * Get or create chat session for a task
   */
  async getOrCreateTaskSession(taskId: string, userId: string = 'default_user'): Promise<string> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat/sessions/task/${taskId}?user_id=${userId}`,
        { method: 'GET' }
      );

      if (!response.ok) {
        throw new Error(`Failed to get/create session: ${response.status}`);
      }

      const result = await response.json();
      return result.session_id;
    } catch (error) {
      console.error('Error getting/creating task session:', error);
      throw error;
    }
  }

  /**
   * Save a chat message
   */
  async saveMessage(
    sessionId: string,
    messageType: 'user' | 'agent' | 'system',
    content: string,
    agentId?: string,
    metadata: Record<string, any> = {}
  ): Promise<string> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat/sessions/${sessionId}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_type: messageType,
            content,
            agent_id: agentId,
            metadata
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to save message: ${response.status}`);
      }

      const result = await response.json();
      return result.message_id;
    } catch (error) {
      console.error('Error saving message:', error);
      throw error;
    }
  }

  /**
   * Get recent chat sessions for task dropdown
   */
  async getRecentSessions(userId: string = 'default_user', limit: number = 20): Promise<RecentSession[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat/recent?user_id=${userId}&limit=${limit}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch recent sessions: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching recent sessions:', error);
      return [];
    }
  }

  /**
   * Get complete chat history with session info
   */
  async getChatHistoryWithSession(sessionId: string): Promise<{
    messages: ChatMessage[];
    session_info: ChatSession;
  }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat/sessions/${sessionId}/history`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch chat history: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching chat history with session:', error);
      throw error;
    }
  }

  /**
   * Search messages within a session
   */
  async searchMessages(sessionId: string, searchTerm: string, limit: number = 50): Promise<ChatMessage[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/chat/sessions/${sessionId}/search?q=${encodeURIComponent(searchTerm)}&limit=${limit}`
      );

      if (!response.ok) {
        throw new Error(`Failed to search messages: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching messages:', error);
      return [];
    }
  }

  /**
   * Check chat system health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/health`);
      return response.ok;
    } catch (error) {
      console.error('Chat health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const chatApi = new ChatApiClient();

// Export utility functions
export const formatChatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return 'Unknown time';
  }
};

export const formatChatCost = (costUsd: number): string => {
  if (costUsd === 0) return 'Free';
  if (costUsd < 0.01) return '<$0.01';
  return `$${costUsd.toFixed(2)}`;
};

export const formatTokenCount = (tokens: number): string => {
  if (tokens === 0) return '0 tokens';
  if (tokens < 1000) return `${tokens} tokens`;
  return `${(tokens / 1000).toFixed(1)}k tokens`;
};

export default chatApi;