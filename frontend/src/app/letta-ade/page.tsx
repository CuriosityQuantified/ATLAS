'use client'

import { useState, useEffect } from 'react'
import { PlusIcon, ChatBubbleLeftRightIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import ChatInterface from '@/components/letta/ChatInterface'
import { API_CONFIG, buildUrl } from '@/config/api'

interface LettaAgent {
  id: string
  name: string
  description?: string
  status: string
  model: string
  created_at: string
  updated_at: string
}

export default function LettaADEPage() {
  const [agents, setAgents] = useState<LettaAgent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<LettaAgent | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(true)

  // Fetch agents on mount
  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const response = await fetch(buildUrl(API_CONFIG.endpoints.lettaAgents))
      if (response.ok) {
        const data = await response.json()
        setAgents(data)
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgent = async (agentData: any) => {
    try {
      const response = await fetch(buildUrl(API_CONFIG.endpoints.lettaAgents), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentData)
      })
      if (response.ok) {
        const newAgent = await response.json()
        setAgents([...agents, newAgent])
        setShowCreateModal(false)
      }
    } catch (error) {
      console.error('Failed to create agent:', error)
    }
  }

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return
    
    try {
      const response = await fetch(buildUrl(API_CONFIG.endpoints.lettaAgent(agentId)), {
        method: 'DELETE'
      })
      if (response.ok) {
        setAgents(agents.filter(a => a.id !== agentId))
        if (selectedAgent?.id === agentId) {
          setSelectedAgent(null)
        }
      }
    } catch (error) {
      console.error('Failed to delete agent:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="flex h-screen">
        {/* Left Panel - Agent List */}
        <div className="w-1/3 border-r border-gray-800 p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Letta Agents</h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Create Agent
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8">Loading agents...</div>
          ) : agents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No agents yet. Create your first agent!
            </div>
          ) : (
            <div className="space-y-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className={`p-4 rounded-lg cursor-pointer transition-colors ${
                    selectedAgent?.id === agent.id
                      ? 'bg-blue-600/20 border border-blue-600'
                      : 'bg-gray-800 hover:bg-gray-700'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold">{agent.name}</h3>
                      <p className="text-sm text-gray-400 mt-1">
                        {agent.description || 'No description'}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{agent.model}</span>
                        <span className={`px-2 py-1 rounded ${
                          agent.status === 'active' ? 'bg-green-600/20 text-green-400' : 'bg-gray-600/20'
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // TODO: Implement edit
                        }}
                        className="p-1 hover:bg-gray-600 rounded"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteAgent(agent.id)
                        }}
                        className="p-1 hover:bg-red-600 rounded"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel - Agent Details/Chat */}
        <div className="flex-1 flex flex-col">
          {selectedAgent ? (
            <>
              <div className="border-b border-gray-800 p-6">
                <h2 className="text-2xl font-bold">{selectedAgent.name}</h2>
                <p className="text-gray-400 mt-2">{selectedAgent.description}</p>
                <div className="flex gap-4 mt-4 text-sm">
                  <span>Model: {selectedAgent.model}</span>
                  <span>Created: {new Date(selectedAgent.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              
              {/* Chat Interface Component */}
              <div className="flex-1 p-6">
                <ChatInterface agentId={selectedAgent.id} agentName={selectedAgent.name} />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              Select an agent to view details and start chatting
            </div>
          )}
        </div>
      </div>

      {/* Create Agent Modal */}
      {showCreateModal && (
        <CreateAgentModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateAgent}
        />
      )}
    </div>
  )
}

// Create Agent Modal Component
function CreateAgentModal({ onClose, onCreate }: { onClose: () => void, onCreate: (data: any) => void }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    model: 'gpt-4',
    persona: '',
    human: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate(formData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-4">Create New Agent</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Model</label>
            <select
              value={formData.model}
              onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Persona</label>
            <textarea
              value={formData.persona}
              onChange={(e) => setFormData({ ...formData, persona: e.target.value })}
              placeholder="Describe the agent's personality and behavior..."
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Human Description</label>
            <input
              type="text"
              value={formData.human}
              onChange={(e) => setFormData({ ...formData, human: e.target.value })}
              placeholder="Describe the human user..."
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
            >
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}