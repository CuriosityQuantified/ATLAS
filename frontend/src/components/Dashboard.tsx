'use client'

import { useState } from 'react'
import Sidebar from './Sidebar'
import AgentArchitecture from './AgentArchitecture'
import ChatBar from './ChatBar'
import QuestionsPanel from './QuestionsPanel'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [taskProgress, setTaskProgress] = useState([
    { name: 'Research Phase', status: 'completed', icon: '✓' },
    { name: 'Analysis Phase', status: 'processing', icon: '⏳' },
    { name: 'Writing Phase', status: 'idle', icon: '⏸' },
    { name: 'Rating Phase', status: 'idle', icon: '⏸' },
  ])

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="p-6">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-2xl font-bold text-text">
              Multi-Agent Analysis Dashboard
            </h1>
            
            {/* Task Progress Dropdown */}
            <div className="relative">
              <button className="bg-card-glass glass-effect px-4 py-2 rounded-xl border border-border text-text hover:bg-card-bg transition-colors">
                Task Progress ▼
              </button>
              {/* Progress dropdown content - implement later */}
            </div>
          </div>

          {/* Agent Architecture */}
          <AgentArchitecture />
        </div>
      </div>

      {/* Right Sidebar - Questions Panel */}
      <QuestionsPanel />

      {/* Chat Bar */}
      <ChatBar />
    </div>
  )
}