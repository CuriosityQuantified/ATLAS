'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon, PlusIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';
import { chatApi, RecentSession, formatChatTimestamp } from '../lib/chat-api';

interface Task {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  status: 'active' | 'completed' | 'failed';
  agent_type: string;
}

interface TaskDropdownProps {
  onTaskSelect: (task: Task | 'new') => void;
  selectedTask?: Task | string | null;
  tasks: Task[];
  className?: string;
}

const TaskDropdown: React.FC<TaskDropdownProps> = ({ 
  onTaskSelect, 
  selectedTask, 
  tasks,
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([]);
  const [isLoadingRecentSessions, setIsLoadingRecentSessions] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  // Load recent chat sessions
  const loadRecentSessions = async () => {
    setIsLoadingRecentSessions(true);
    try {
      const sessions = await chatApi.getRecentSessions('default_user', 20);
      setRecentSessions(sessions);
    } catch (error) {
      console.error('Failed to load recent sessions:', error);
      setRecentSessions([]);
    } finally {
      setIsLoadingRecentSessions(false);
    }
  };
  
  // Load recent sessions when dropdown opens
  useEffect(() => {
    if (isOpen) {
      loadRecentSessions();
    }
  }, [isOpen]);

  const handleTaskSelect = (task: Task | 'new') => {
    onTaskSelect(task);
    setIsOpen(false);
  };
  
  const handleRecentSessionSelect = (session: RecentSession) => {
    // Convert recent session to Task format
    const task: Task = {
      id: session.task_id,
      name: session.last_message?.content?.slice(0, 50) + '...' || 'Untitled Task',
      description: session.last_message?.content || '',
      created_at: session.created_at,
      status: session.status as 'active' | 'completed' | 'failed',
      agent_type: 'global_supervisor'
    };
    
    onTaskSelect(task);
    setIsOpen(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'completed': return 'text-blue-400';
      case 'failed': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '🟢';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '⚪';
    }
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Dropdown Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2 text-left bg-transparent 
                   border border-gray-600 rounded-lg hover:bg-gray-800/50 
                   transition-all duration-200 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="flex items-center space-x-2">
          <ChatBubbleLeftIcon className="w-5 h-5" />
          <span>
            {selectedTask && typeof selectedTask === 'object' ? selectedTask.name : 
             selectedTask && typeof selectedTask === 'string' && selectedTask.startsWith('new') ? 'New Task' :
             'Tasks'}
          </span>
        </div>
        <ChevronDownIcon 
          className={`w-4 h-4 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 bg-gray-900/95 backdrop-blur-sm 
                        border border-gray-600 rounded-lg shadow-2xl max-h-80 overflow-y-auto">
          
          {/* New Task Option */}
          <button
            onClick={() => handleTaskSelect('new')}
            className="w-full px-4 py-3 text-left hover:bg-gray-800/50 transition-colors duration-200 
                       border-b border-gray-700 flex items-center space-x-3"
          >
            <PlusIcon className="w-5 h-5 text-green-400" />
            <div>
              <div className="font-medium text-white">New Task</div>
              <div className="text-sm text-gray-400">Start a new conversation with Global Supervisor</div>
            </div>
          </button>

          {/* Task History */}
          <div className="py-2">
            <div className="px-4 py-2 text-xs font-medium text-gray-400 uppercase tracking-wider">
              Recent Conversations
            </div>
            
            {isLoadingRecentSessions ? (
              <div className="px-4 py-6 text-center text-gray-500">
                Loading conversations...
              </div>
            ) : recentSessions.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-500">
                No previous conversations found
              </div>
            ) : (
              recentSessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleRecentSessionSelect(session)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-800/50 transition-colors duration-200 
                             border-b border-gray-700/50 last:border-b-0"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm">{getStatusIcon(session.status)}</span>
                        <span className="font-medium text-white truncate">
                          {session.last_message?.content?.slice(0, 40) || 'Untitled Task'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>{formatChatTimestamp(session.created_at)}</span>
                        <span className={`capitalize ${getStatusColor(session.status)}`}>
                          {session.status}
                        </span>
                        <span>{session.message_count} messages</span>
                      </div>
                      {session.total_cost_usd > 0 && (
                        <div className="text-xs text-gray-400 mt-1">
                          ${session.total_cost_usd.toFixed(4)} • {session.total_tokens} tokens
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskDropdown;