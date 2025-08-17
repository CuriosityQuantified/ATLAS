import React from 'react'

interface StreamingMessageProps {
  content: string
  isThinking?: boolean
  isComplete?: boolean
}

export default function StreamingMessage({ content, isThinking, isComplete }: StreamingMessageProps) {
  return (
    <div className="streaming-message">
      {isThinking && (
        <div className="thinking-indicator mb-2">
          <span className="text-xs text-yellow-400 italic">🤔 Thinking...</span>
          <div className="thinking-content bg-yellow-900/20 border border-yellow-800/30 rounded p-2 mt-1 text-xs text-yellow-300 font-mono">
            {content}
          </div>
        </div>
      )}
      
      {!isThinking && (
        <div className="message-content text-sm text-text">
          <span className="whitespace-pre-wrap">{content}</span>
          {!isComplete && (
            <span className="typing-cursor inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
          )}
        </div>
      )}
    </div>
  )
}