'use client'

import { useState } from 'react'
import Sidebar from './Sidebar'
import TasksView from './TasksView'

interface Task {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  status: 'active' | 'completed' | 'failed';
  agent_type: string;
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [selectedTask, setSelectedTask] = useState<Task | 'new' | null>(null)

  const handleTaskSelect = (task: Task | 'new') => {
    if (task === 'new') {
      // Use a unique identifier to force state change even if already 'new'
      setSelectedTask(`new_${Date.now()}` as any)
    } else {
      setSelectedTask(task)
    }
    setActiveTab('Tasks')
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'Tasks':
        return <TasksView selectedTask={selectedTask} />
      case 'Dashboard':
        return (
          <div className="flex-1 p-6">
            <h1 className="text-2xl font-bold text-text mb-6">Dashboard</h1>
            <div className="text-muted">
              Dashboard content coming soon...
            </div>
          </div>
        )
      case 'Agents':
        return (
          <div className="flex-1 p-6">
            <h1 className="text-2xl font-bold text-text mb-6">Agents</h1>
            <div className="text-muted">
              Agent management coming soon...
            </div>
          </div>
        )
      case 'Memory':
        return (
          <div className="flex-1 p-6">
            <h1 className="text-2xl font-bold text-text mb-6">Memory</h1>
            <div className="text-muted">
              Memory system coming soon...
            </div>
          </div>
        )
      case 'Analytics':
        return (
          <div className="flex-1 p-6">
            <h1 className="text-2xl font-bold text-text mb-6">Analytics</h1>
            <div className="text-muted">
              Analytics dashboard coming soon...
            </div>
          </div>
        )
      case 'Settings':
        return (
          <div className="flex-1 p-6">
            <h1 className="text-2xl font-bold text-text mb-6">Settings</h1>
            <div className="text-muted">
              Settings panel coming soon...
            </div>
          </div>
        )
      default:
        return (
          <div className="flex-1 p-6">
            <h1 className="text-2xl font-bold text-text mb-6">Dashboard</h1>
            <div className="text-muted">
              Welcome to ATLAS
            </div>
          </div>
        )
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden relative">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        onTaskSelect={handleTaskSelect}
        selectedTask={selectedTask}
      />
      
      {renderActiveTab()}
    </div>
  )
}