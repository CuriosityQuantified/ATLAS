'use client'

import { useState } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/outline'

interface ChatBarProps {
  onSubmit?: (message: string) => void
  placeholder?: string
  submitText?: string
}

export default function ChatBar({ 
  onSubmit, 
  placeholder = "Ask a question or provide guidance to the agents...",
  submitText = "Send"
}: ChatBarProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim()) {
      if (onSubmit) {
        onSubmit(message)
      } else {
        console.log('Sending message:', message)
      }
      setMessage('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background via-background/90 to-transparent">
      <div className="max-w-4xl mx-auto flex items-end space-x-3">
        <div className="flex-1 relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="chat-input w-full px-4 py-3 pr-12 min-h-[48px] max-h-32 resize-none rounded-xl"
            rows={1}
          />
        </div>
        
        <button
          onClick={handleSend}
          disabled={!message.trim()}
          className="bg-primary hover:bg-primary-light disabled:bg-slate-600 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-colors shadow-lg"
        >
          <PaperAirplaneIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}