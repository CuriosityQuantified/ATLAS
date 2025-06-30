'use client'

interface Agent {
  id: string
  title: string
  description: string
  status: 'active' | 'processing' | 'idle'
  type: 'supervisor' | 'worker'
  progress: number
}

interface AgentCardProps {
  agent: Agent
}

export default function AgentCard({ agent }: AgentCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-active shadow-[0_0_8px_rgba(34,197,94,0.4)]'
      case 'processing':
        return 'bg-processing shadow-[0_0_8px_rgba(245,158,66,0.4)]'
      case 'idle':
        return 'bg-idle shadow-[0_0_8px_rgba(148,163,184,0.4)]'
      default:
        return 'bg-idle'
    }
  }

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'from-active to-primary-light'
      case 'processing':
        return 'from-processing to-yellow-400'
      case 'idle':
        return 'from-idle to-slate-400'
      default:
        return 'from-idle to-slate-400'
    }
  }

  return (
    <div className={`
      bg-card-glass glass-effect rounded-2xl p-4 border border-border
      hover:transform hover:-translate-y-1 transition-all duration-200
      shadow-custom hover:shadow-lg
      ${agent.type === 'worker' ? 'min-h-[140px]' : 'min-h-[160px]'}
    `}>
      {/* Status Indicator */}
      <div className="flex items-start justify-between mb-3">
        <div className={`
          w-3 h-3 rounded-full ${getStatusColor(agent.status)}
        `} />
        <div className="text-xs text-muted uppercase tracking-wide">
          {agent.type}
        </div>
      </div>

      {/* Agent Info */}
      <div className="mb-4">
        <h3 className="text-text font-semibold mb-2 text-sm">
          {agent.title}
        </h3>
        <p className="text-muted text-xs leading-relaxed">
          {agent.description}
        </p>
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted">Progress</span>
          <span className="text-xs text-text font-medium">{agent.progress}%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-1">
          <div
            className={`h-1 rounded-full bg-gradient-to-r ${getProgressColor(agent.status)}`}
            style={{ width: `${agent.progress}%` }}
          />
        </div>
      </div>
    </div>
  )
}