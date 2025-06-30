'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'

export interface DialogueMessage {
  id: string
  timestamp: Date
  direction: 'input' | 'output'
  content: string
  sender: string
}

interface AgentDialogueProps {
  agentId: string
  agentName: string
  messages: DialogueMessage[]
  isExpanded: boolean
  onToggleExpand: () => void
  isLive: boolean
}

export default function AgentDialogue({
  agentId,
  agentName,
  messages,
  isExpanded,
  onToggleExpand,
  isLive
}: AgentDialogueProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  }

  const getMessageTypeColor = (direction: string) => {
    return direction === 'input' 
      ? 'bg-primary/10 border-l-2 border-primary' 
      : 'bg-card-glass border-l-2 border-accent'
  }

  return (
    <div className="mt-3 bg-card-glass/50 glass-effect rounded-xl border border-border/50 overflow-hidden">
      {/* Dialogue Header */}
      <button
        onClick={onToggleExpand}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-card-bg/50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center">
            <span className="text-xs text-primary font-medium">💬</span>
          </div>
          <div className="text-left">
            <div className="text-sm font-medium text-text">
              {agentName} Dialogue
            </div>
            <div className="text-xs text-muted">
              {messages.length} messages 
              {isLive && <span className="text-accent"> • Live</span>}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {isLive && (
            <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
          )}
          {isExpanded ? (
            <ChevronUpIcon className="w-4 h-4 text-muted" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 text-muted" />
          )}
        </div>
      </button>

      {/* Dialogue Content */}
      <div className={`
        transition-all duration-300 ease-in-out overflow-hidden
        ${isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}
      `}>
        <div className="border-t border-border/50">
          {messages.length > 0 ? (
            <div className="max-h-80 overflow-y-auto p-4 space-y-3">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`
                    p-3 rounded-lg text-sm
                    ${getMessageTypeColor(message.direction)}
                  `}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-text text-xs">
                        {message.sender}
                      </span>
                      <span className={`
                        px-2 py-1 rounded-full text-xs font-medium
                        ${message.direction === 'input' 
                          ? 'bg-primary/20 text-primary' 
                          : 'bg-accent/20 text-accent'
                        }
                      `}>
                        {message.direction === 'input' ? 'Input' : 'Output'}
                      </span>
                    </div>
                    <span className="text-xs text-muted">
                      {formatTime(message.timestamp)}
                    </span>
                  </div>
                  <div className="text-text leading-relaxed">
                    {message.content}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-muted">
              <div className="text-sm">No conversation history yet</div>
              <div className="text-xs mt-1">Messages will appear here when the agent starts working</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}