'use client'

interface AgentMessageBoxProps {
  agentId: string;
  content: string;
  timestamp: string;
  isTyping?: boolean;
}

const agentConfig: Record<string, { name: string; emoji: string; color: string }> = {
  global_supervisor: {
    name: 'Global Supervisor',
    emoji: '🌐',
    color: 'bg-blue-500/20'
  },
  research_supervisor: {
    name: 'Research Team Lead',
    emoji: '🔍',
    color: 'bg-purple-500/20'
  },
  analysis_supervisor: {
    name: 'Analysis Team Lead', 
    emoji: '📊',
    color: 'bg-green-500/20'
  },
  writing_supervisor: {
    name: 'Writing Team Lead',
    emoji: '✍️',
    color: 'bg-orange-500/20'
  },
  rating_supervisor: {
    name: 'Rating Team Lead',
    emoji: '⭐',
    color: 'bg-yellow-500/20'
  },
  default: {
    name: 'Agent',
    emoji: '🤖',
    color: 'bg-gray-500/20'
  }
}

export default function AgentMessageBox({ agentId, content, timestamp, isTyping = false }: AgentMessageBoxProps) {
  const agent = agentConfig[agentId] || agentConfig.default;
  
  return (
    <div className="bg-card-glass glass-effect border border-border rounded-lg p-4 max-w-xs lg:max-w-md">
      <div className="flex items-center mb-2">
        <div className={`w-8 h-8 ${agent.color} rounded-full flex items-center justify-center mr-2 ${isTyping ? 'animate-pulse' : ''}`}>
          <span className="text-xs">{agent.emoji}</span>
        </div>
        <span className="text-xs font-medium text-muted">
          {agent.name}
        </span>
      </div>
      
      {isTyping ? (
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      ) : (
        <>
          <div 
            className="text-sm whitespace-pre-wrap" 
            dangerouslySetInnerHTML={{
              __html: content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>')
            }}
          />
          <p className="text-xs opacity-70 mt-1">
            {new Date(timestamp).toLocaleTimeString()}
          </p>
        </>
      )}
    </div>
  );
}