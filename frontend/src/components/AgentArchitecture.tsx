'use client'

import AgentCard from './AgentCard'

export default function AgentArchitecture() {
  const globalSupervisor = {
    id: 'global-supervisor',
    title: 'Global Supervisor',
    description: 'Orchestrates all team operations and maintains task coherence',
    status: 'active' as const,
    type: 'supervisor' as const,
    progress: 93
  }

  const teamSupervisors = [
    {
      id: 'research-supervisor',
      title: '🕵️‍♂️ Research Supervisor',
      description: 'Coordinates information gathering and source validation',
      status: 'active' as const,
      type: 'supervisor' as const,
      progress: 100
    },
    {
      id: 'analysis-supervisor',
      title: '📊 Analysis Supervisor',
      description: 'Manages analytical frameworks and data interpretation',
      status: 'processing' as const,
      type: 'supervisor' as const,
      progress: 75
    },
    {
      id: 'writing-supervisor',
      title: '✍️ Writing Supervisor',
      description: 'Oversees content generation and narrative coherence',
      status: 'idle' as const,
      type: 'supervisor' as const,
      progress: 30
    },
    {
      id: 'rating-supervisor',
      title: '📈 Rating Supervisor',
      description: 'Evaluates quality and provides improvement feedback',
      status: 'idle' as const,
      type: 'supervisor' as const,
      progress: 10
    }
  ]

  const workerAgents = [
    {
      id: 'web-researcher',
      title: 'Web Researcher',
      description: 'Gathers information from online sources',
      status: 'active' as const,
      type: 'worker' as const,
      progress: 100
    },
    {
      id: 'data-analyst',
      title: 'Data Analyst',
      description: 'Processes and interprets quantitative data',
      status: 'active' as const,
      type: 'worker' as const,
      progress: 65
    },
    {
      id: 'swot-analyzer',
      title: 'SWOT Analyzer',
      description: 'Conducts strategic analysis frameworks',
      status: 'processing' as const,
      type: 'worker' as const,
      progress: 73
    },
    {
      id: 'content-writer',
      title: 'Content Writer',
      description: 'Generates structured written content',
      status: 'idle' as const,
      type: 'worker' as const,
      progress: 25
    },
    {
      id: 'quality-reviewer',
      title: 'Quality Reviewer',
      description: 'Reviews and scores output quality',
      status: 'idle' as const,
      type: 'worker' as const,
      progress: 5
    }
  ]

  return (
    <div className="space-y-6">
      {/* Global Supervisor */}
      <div className="flex justify-center">
        <AgentCard agent={globalSupervisor} />
      </div>

      {/* Team Supervisors */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {teamSupervisors.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {/* Worker Agents */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {workerAgents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}