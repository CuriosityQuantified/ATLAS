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

  // Mock dialogue data - SYNTHETIC DATA FOR DEVELOPMENT
  const mockDialogues: Record<string, DialogueMessage[]> = {
    'global-supervisor': [
      {
        id: '1',
        timestamp: new Date(Date.now() - 300000),
        direction: 'input',
        content: '[SYNTHETIC] Initiating market analysis for Q4 2024 technology trends. Please coordinate team efforts.',
        sender: 'User'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 280000),
        direction: 'output',
        content: {
          type: 'text',
          data: '**[DEMO DATA]** Understood. Delegating research phase to Research Team.\n\nAnalysis framework will focus on:\n- 🤖 AI automation trends\n- ☁️ Cloud computing evolution\n- 🔐 Cybersecurity developments\n\n*This is synthetic conversation data for development purposes.*'
        },
        sender: 'Global Supervisor',
        metadata: {
          model: 'claude-3-sonnet',
          tokens: 156,
          cost: 0.0023,
          processingTime: 1240
        }
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 120000),
        direction: 'output',
        content: {
          type: 'json',
          data: {
            status: "[SYNTHETIC] Research Phase Complete",
            sources_analyzed: 47,
            quality_score: 4.2,
            next_phase: "analysis",
            breakdown: {
              "academic_papers": 12,
              "industry_reports": 18,
              "news_articles": 17
            },
            note: "This is demo JSON data for development"
          }
        },
        sender: 'Global Supervisor',
        metadata: {
          model: 'claude-3-sonnet',
          tokens: 89,
          cost: 0.0012,
          processingTime: 890
        }
      }
    ],
    'research-supervisor': [
      {
        id: '4',
        timestamp: new Date(Date.now() - 250000),
        direction: 'input',
        content: '[SYNTHETIC] Research team, gather comprehensive data on Q4 2024 tech trends focusing on market growth and adoption rates.',
        sender: 'Global Supervisor'
      },
      {
        id: '5',
        timestamp: new Date(Date.now() - 240000),
        direction: 'output',
        content: {
          type: 'code',
          data: `# [DEMO] Research Deployment Script
# This is synthetic code for development purposes

import requests
from datetime import datetime

def deploy_researchers():
    """Deploy web researchers to gather tech trend data"""
    sources = [
        "https://techcrunch.com/",
        "https://venturebeat.com/", 
        "https://wired.com/"
    ]
    
    print("[SYNTHETIC] Deploying researchers...")
    for source in sources:
        print(f"Scanning: {source}")
    
    return {"status": "deployed", "sources": len(sources)}

# Execute deployment
result = deploy_researchers()
print(f"Research deployment: {result}")`,
          filename: 'research_deployment.py',
          mimeType: 'text/x-python'
        },
        sender: 'Research Supervisor',
        metadata: {
          model: 'claude-3-haiku',
          tokens: 234,
          cost: 0.0018,
          processingTime: 1580
        }
      },
      {
        id: '6',
        timestamp: new Date(Date.now() - 130000),
        direction: 'output',
        content: {
          type: 'file',
          data: 'data:application/pdf;base64,JVBERi0xLjQKJcOkw7zDtsOgUERGLTE...', // Mock base64
          filename: '[SYNTHETIC] research_summary.pdf',
          mimeType: 'application/pdf',
          size: 2847593
        },
        sender: 'Research Supervisor',
        metadata: {
          model: 'claude-3-sonnet',
          tokens: 445,
          cost: 0.0067,
          processingTime: 3200
        }
      }
    ],
    'analysis-supervisor': [
      {
        id: '7',
        timestamp: new Date(Date.now() - 110000),
        direction: 'input',
        content: '[SYNTHETIC] Analyze collected research data using SWOT framework and trend analysis methodologies.',
        sender: 'Global Supervisor'
      },
      {
        id: '8',
        timestamp: new Date(Date.now() - 100000),
        direction: 'output',
        content: {
          type: 'image',
          data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
          filename: '[SYNTHETIC] swot_analysis_framework.png',
          mimeType: 'image/png',
          size: 145678
        },
        sender: 'Analysis Supervisor',
        metadata: {
          model: 'claude-3-opus',
          tokens: 312,
          cost: 0.0094,
          processingTime: 2100
        }
      },
      {
        id: '9',
        timestamp: new Date(Date.now() - 30000),
        direction: 'output',
        content: {
          type: 'chart',
          data: {
            type: 'bar',
            title: '[DEMO] Tech Sector Growth Analysis',
            note: 'Synthetic chart data for development',
            series: [
              { name: 'AI Automation', value: 45.2, color: '#22c55e' },
              { name: 'Cloud Infrastructure', value: 32.1, color: '#3b82f6' },
              { name: 'Cybersecurity', value: 28.7, color: '#f59e0b' },
              { name: 'IoT Devices', value: 24.3, color: '#ef4444' }
            ]
          },
          filename: '[SYNTHETIC] growth_analysis.json',
          mimeType: 'application/json',
          size: 1024
        },
        sender: 'Analysis Supervisor',
        metadata: {
          model: 'claude-3-sonnet',
          tokens: 267,
          cost: 0.0040,
          processingTime: 1890
        }
      }
    ],
    'web-researcher': [
      {
        id: '10',
        timestamp: new Date(Date.now() - 220000),
        direction: 'output',
        content: '[SYNTHETIC] Scanning TechCrunch, VentureBeat, and Wired for Q4 2024 technology trends...',
        sender: 'Web Researcher'
      },
      {
        id: '11',
        timestamp: new Date(Date.now() - 180000),
        direction: 'output',
        content: {
          type: 'audio',
          data: 'data:audio/mp3;base64,SUQzAwAAAAAAI1RJVDIAAAAPAAAAVGVzdCBBdWRpbyBGaWxlAA==',
          filename: '[SYNTHETIC] research_briefing.mp3',
          mimeType: 'audio/mp3',
          size: 892456
        },
        sender: 'Web Researcher',
        metadata: {
          model: 'claude-3-haiku',
          tokens: 145,
          cost: 0.0008,
          processingTime: 750
        }
      },
      {
        id: '12',
        timestamp: new Date(Date.now() - 150000),
        direction: 'output',
        content: {
          type: 'json',
          data: {
            task_status: "[SYNTHETIC] Research Complete",
            sources_gathered: {
              total: 37,
              breakdown: {
                articles: 23,
                reports: 8,
                studies: 6
              }
            },
            key_themes: [
              "AI integration in enterprise",
              "Remote work technology evolution", 
              "Sustainability initiatives in tech",
              "Cybersecurity automation"
            ],
            confidence_score: 0.87,
            note: "This is synthetic research data for demo purposes"
          },
          filename: '[SYNTHETIC] research_summary.json',
          mimeType: 'application/json',
          size: 2048
        },
        sender: 'Web Researcher',
        metadata: {
          model: 'claude-3-sonnet',
          tokens: 198,
          cost: 0.0030,
          processingTime: 1120
        }
      }
    ],
    'data-analyst': [
      {
        id: '13',
        timestamp: new Date(Date.now() - 90000),
        direction: 'output',
        content: {
          type: 'code',
          data: `# [SYNTHETIC] Data Analysis Pipeline
# This is demo code for development purposes

import pandas as pd
import numpy as np
from scipy import stats

def analyze_market_data(data_sources):
    """Analyze tech market growth data"""
    
    # Mock data processing
    growth_rates = {
        'AI_automation': 45.2,
        'cloud_services': 32.1, 
        'cybersecurity': 28.7,
        'iot_devices': 24.3
    }
    
    # Calculate confidence intervals
    for sector, rate in growth_rates.items():
        ci = stats.norm.interval(0.95, loc=rate, scale=2.1)
        print(f"{sector}: {rate}% (CI: {ci[0]:.1f}-{ci[1]:.1f}%)")
    
    return growth_rates

# [DEMO] Execute analysis
print("🔍 [SYNTHETIC] Market Analysis Results:")
results = analyze_market_data(['gartner', 'idc', 'techcrunch'])
print(f"Analysis complete. {len(results)} sectors analyzed.")`,
          filename: '[SYNTHETIC] market_analysis.py',
          mimeType: 'text/x-python'
        },
        sender: 'Data Analyst',
        metadata: {
          model: 'claude-3-haiku',
          tokens: 287,
          cost: 0.0021,
          processingTime: 1650
        }
      },
      {
        id: '14',
        timestamp: new Date(Date.now() - 60000),
        direction: 'output',
        content: {
          type: 'file',
          data: 'data:text/csv;base64,U2VjdG9yLEdyb3d0aFJhdGUsQ29uZmlkZW5jZUludGVydmFsCkFJIEF1dG9tYXRpb24sNDUuMiw0MC4xLTUwLjMKQ2xvdWQgU2VydmljZXMsMzIuMSwyOS4wLTM1LjIKQ3liZXJzZWN1cml0eSwyOC43LDI1LjYtMzEuOApJb1QgRGV2aWNlcywyNC4zLDIxLjItMjcuNA==',
          filename: '[SYNTHETIC] growth_analysis.csv',
          mimeType: 'text/csv',
          size: 512
        },
        sender: 'Data Analyst',
        metadata: {
          model: 'claude-3-sonnet',
          tokens: 167,
          cost: 0.0025,
          processingTime: 980
        }
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