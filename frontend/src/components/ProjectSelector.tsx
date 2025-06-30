'use client'

import { useState } from 'react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'

export interface Project {
  id: string
  name: string
  status: 'active' | 'completed' | 'paused'
  description: string
  lastActive: string
}

interface ProjectSelectorProps {
  projects: Project[]
  selectedProject: Project | null
  onProjectChange: (project: Project) => void
}

export default function ProjectSelector({ 
  projects, 
  selectedProject, 
  onProjectChange 
}: ProjectSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-active'
      case 'completed':
        return 'bg-green-500'
      case 'paused':
        return 'bg-yellow-500'
      default:
        return 'bg-idle'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active'
      case 'completed':
        return 'Completed'
      case 'paused':
        return 'Paused'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="relative mb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Project</h2>
        
        {/* Project Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="bg-card-glass glass-effect px-4 py-3 rounded-xl border border-border text-text hover:bg-card-bg transition-all duration-200 flex items-center space-x-3 min-w-[280px]"
          >
            <div className="flex items-center space-x-3 flex-1">
              {selectedProject && (
                <>
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedProject.status)}`} />
                  <div className="text-left">
                    <div className="font-medium">{selectedProject.name}</div>
                    <div className="text-xs text-muted">{getStatusText(selectedProject.status)} • {selectedProject.lastActive}</div>
                  </div>
                </>
              )}
              {!selectedProject && (
                <div className="text-muted">Select a project...</div>
              )}
            </div>
            <ChevronDownIcon 
              className={`w-4 h-4 text-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
            />
          </button>

          {/* Dropdown Menu */}
          {isOpen && (
            <div className="absolute top-full right-0 mt-2 w-full bg-card-glass glass-effect rounded-xl border border-border shadow-lg z-50 max-h-64 overflow-y-auto">
              {projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => {
                    onProjectChange(project)
                    setIsOpen(false)
                  }}
                  className={`w-full p-4 text-left hover:bg-card-bg transition-colors first:rounded-t-xl last:rounded-b-xl ${
                    selectedProject?.id === project.id ? 'bg-primary/10 border-l-2 border-primary' : ''
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(project.status)}`} />
                    <div className="flex-1">
                      <div className="font-medium text-text">{project.name}</div>
                      <div className="text-xs text-muted mt-1">{project.description}</div>
                      <div className="text-xs text-muted mt-1">
                        {getStatusText(project.status)} • {project.lastActive}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
              
              {projects.length === 0 && (
                <div className="p-4 text-center text-muted">
                  No projects available
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Clicked outside handler */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}