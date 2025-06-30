'use client'

import { useState } from 'react'
import AgentCard from './AgentCard'
import { DialogueMessage } from './AgentDialogue'

interface AgentArchitectureProps {
  selectedProjectId?: string
}

export default function AgentArchitecture({ selectedProjectId }: AgentArchitectureProps) {
  // State for managing which dialogue windows are expanded
  const [expandedDialogues, setExpandedDialogues] = useState<Set<string>>(new Set())

  // Mock dialogue data
  const mockDialogues: Record<string, DialogueMessage[]> = {
    'global-supervisor': [
      {
        id: '1',
        timestamp: new Date(Date.now() - 300000),
        direction: 'input',
        content: 'Initiating market analysis for Q4 2024 technology trends. Please coordinate team efforts.',
        sender: 'User'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 280000),
        direction: 'output',
        content: 'Understood. Delegating research phase to Research Team. Analysis framework will focus on AI, cloud computing, and cybersecurity sectors.',
        sender: 'Global Supervisor'
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 120000),
        direction: 'output',
        content: 'Research phase completed. 47 sources analyzed. Transitioning to analysis phase with comprehensive data set.',
        sender: 'Global Supervisor'
      }
    ],
    'research-supervisor': [
      {
        id: '4',
        timestamp: new Date(Date.now() - 250000),
        direction: 'input',
        content: 'Research team, gather comprehensive data on Q4 2024 tech trends focusing on market growth and adoption rates.',
        sender: 'Global Supervisor'
      },
      {
        id: '5',
        timestamp: new Date(Date.now() - 240000),
        direction: 'output',
        content: 'Deploying web researchers to gather data from tech publications, market research firms, and industry reports.',
        sender: 'Research Supervisor'
      },
      {
        id: '6',
        timestamp: new Date(Date.now() - 130000),
        direction: 'output',
        content: 'Research complete. Collected 47 sources including Gartner, IDC, and TechCrunch. Data quality score: 4.2/5.0',
        sender: 'Research Supervisor'
      }
    ],
    'analysis-supervisor': [
      {
        id: '7',
        timestamp: new Date(Date.now() - 110000),
        direction: 'input',
        content: 'Analyze collected research data using SWOT framework and trend analysis methodologies.',
        sender: 'Global Supervisor'
      },
      {
        id: '8',
        timestamp: new Date(Date.now() - 100000),
        direction: 'output',
        content: 'Beginning analytical phase. Deploying SWOT analyzer and data analyst. Processing 47 research sources.',
        sender: 'Analysis Supervisor'
      },
      {
        id: '9',
        timestamp: new Date(Date.now() - 30000),
        direction: 'output',
        content: 'Preliminary analysis shows strong growth in AI automation (+45%) and cloud infrastructure (+32%). Continuing detailed analysis.',
        sender: 'Analysis Supervisor'
      }
    ],
    'web-researcher': [
      {
        id: '10',
        timestamp: new Date(Date.now() - 220000),
        direction: 'output',
        content: 'Scanning TechCrunch, VentureBeat, and Wired for Q4 2024 technology trends...',
        sender: 'Web Researcher'
      },
      {
        id: '11',
        timestamp: new Date(Date.now() - 180000),
        direction: 'output',
        content: 'Found 15 relevant articles. Key themes: AI integration, remote work tech, sustainability initiatives.',
        sender: 'Web Researcher'
      },
      {
        id: '12',
        timestamp: new Date(Date.now() - 150000),
        direction: 'output',
        content: 'Research task completed. Total sources gathered: 23 articles, 8 reports, 6 industry studies.',
        sender: 'Web Researcher'
      }
    ],
    'data-analyst': [
      {
        id: '13',
        timestamp: new Date(Date.now() - 90000),
        direction: 'output',
        content: 'Processing numerical data from market research reports. Calculating growth rates and market size projections.',
        sender: 'Data Analyst'
      },
      {
        id: '14',
        timestamp: new Date(Date.now() - 60000),
        direction: 'output',
        content: 'AI market growth: 45.2% YoY. Cloud services: 32.1% YoY. Cybersecurity: 28.7% YoY. Computing confidence intervals.',
        sender: 'Data Analyst'
      }
    ]
  }

  // Helper function to toggle dialogue expansion
  const toggleDialogue = (agentId: string) => {
    const newExpanded = new Set(expandedDialogues)
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId)
    } else {
      newExpanded.add(agentId)
    }
    setExpandedDialogues(newExpanded)
  }

  // Helper function to get messages for an agent
  const getMessagesForAgent = (agentId: string): DialogueMessage[] => {
    return mockDialogues[agentId] || []
  }
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
        <div className="w-full max-w-md">
          <AgentCard 
            agent={globalSupervisor}
            dialogueMessages={getMessagesForAgent(globalSupervisor.id)}
            isDialogueExpanded={expandedDialogues.has(globalSupervisor.id)}
            onToggleDialogue={() => toggleDialogue(globalSupervisor.id)}
          />
        </div>
      </div>

      {/* Team Supervisors */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {teamSupervisors.map((agent) => (
          <AgentCard 
            key={agent.id} 
            agent={agent}
            dialogueMessages={getMessagesForAgent(agent.id)}
            isDialogueExpanded={expandedDialogues.has(agent.id)}
            onToggleDialogue={() => toggleDialogue(agent.id)}
          />
        ))}
      </div>

      {/* Worker Agents */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {workerAgents.map((agent) => (
          <AgentCard 
            key={agent.id} 
            agent={agent}
            dialogueMessages={getMessagesForAgent(agent.id)}
            isDialogueExpanded={expandedDialogues.has(agent.id)}
            onToggleDialogue={() => toggleDialogue(agent.id)}
          />
        ))}
      </div>
    </div>
  )
}