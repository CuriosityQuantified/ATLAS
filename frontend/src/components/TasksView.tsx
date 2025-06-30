'use client'

import { useState } from 'react'
import Sidebar from './Sidebar'
import AgentArchitecture from './AgentArchitecture'
import ChatBar from './ChatBar'
import QuestionsPanel from './QuestionsPanel'
import ProjectSelector, { Project } from './ProjectSelector'

export default function TasksView() {
  const [activeTab, setActiveTab] = useState('Tasks')
  
  // Mock projects data
  const [projects] = useState<Project[]>([
    {
      id: 'market-analysis-q4-2024',
      name: 'Q4 2024 Tech Market Analysis',
      status: 'active',
      description: 'Comprehensive analysis of technology market trends for Q4 2024',
      lastActive: '2 minutes ago'
    },
    {
      id: 'competitor-analysis-saas',
      name: 'SaaS Competitor Analysis',
      status: 'completed',
      description: 'Deep dive into competitive landscape for SaaS productivity tools',
      lastActive: '3 days ago'
    },
    {
      id: 'investment-memo-ai-startups',
      name: 'AI Startups Investment Memo',
      status: 'paused',
      description: 'Investment analysis for early-stage AI companies',
      lastActive: '1 week ago'
    },
    {
      id: 'product-requirements-mobile',
      name: 'Mobile App PRD',
      status: 'active',
      description: 'Product requirements document for new mobile application',
      lastActive: '1 hour ago'
    }
  ])

  const [selectedProject, setSelectedProject] = useState<Project | null>(projects[0])
  
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
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-text">
              Tasks Monitor
            </h1>
            
            {/* Task Progress Dropdown */}
            <div className="relative">
              <button className="bg-card-glass glass-effect px-4 py-2 rounded-xl border border-border text-text hover:bg-card-bg transition-colors">
                Task Progress ▼
              </button>
              {/* Progress dropdown content - implement later */}
            </div>
          </div>

          {/* Project Selector */}
          <ProjectSelector
            projects={projects}
            selectedProject={selectedProject}
            onProjectChange={setSelectedProject}
          />

          {/* Agent Architecture */}
          <AgentArchitecture selectedProjectId={selectedProject?.id} />
        </div>
      </div>

      {/* Right Sidebar - Questions Panel */}
      <QuestionsPanel />

      {/* Chat Bar */}
      <ChatBar />
    </div>
  )
}