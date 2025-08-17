'use client'

import { useState } from 'react'
import TaskDropdown from './TaskDropdown'

interface Task {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  status: 'active' | 'completed' | 'failed';
  agent_type: string;
}

interface SidebarProps {
  activeTab: string
  setActiveTab: (tab: string) => void
  onTaskSelect: (task: Task | 'new') => void
  selectedTask: Task | string | null
  tasks: Task[]
}

export default function Sidebar({ activeTab, setActiveTab, onTaskSelect, selectedTask, tasks }: SidebarProps) {
  const navItems = [
    'Dashboard',
    'Agents',
    'Memory',
    'Analytics',
    'Letta ADE',
    'Settings'
  ]

  return (
    <div className="w-64 bg-sidebar-bg glass-effect shadow-custom p-6 flex flex-col justify-between border-r border-border">
      {/* User Header */}
      <div>
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
            <span className="text-white font-semibold">RU</span>
          </div>
          <div>
            <div className="text-text font-medium">Research User</div>
            <div className="text-muted text-sm">Analyst</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-2">
          {/* Task Dropdown */}
          <TaskDropdown 
            onTaskSelect={onTaskSelect}
            selectedTask={selectedTask}
            tasks={tasks}
            className="mb-2"
          />
          
          {/* Other Navigation Items */}
          {navItems.map((item) => (
            <button
              key={item}
              onClick={() => setActiveTab(item)}
              className={`w-full text-left px-4 py-3 rounded-xl transition-colors ${
                activeTab === item
                  ? 'bg-primary text-white shadow-lg'
                  : 'text-muted hover:text-text hover:bg-card-glass'
              }`}
            >
              {item}
            </button>
          ))}
        </nav>
      </div>

      {/* Footer */}
      <div className="text-muted text-sm">
        ATLAS v3.0
      </div>
    </div>
  )
}