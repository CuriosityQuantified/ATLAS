'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'

interface ToolCallBoxProps {
  id: string
  toolName: string
  summary?: string
  arguments?: any
  status: 'pending' | 'executing' | 'complete' | 'failed'
  result?: any
  executionTime?: number
  timestamp: string
}

export default function ToolCallBox({
  id,
  toolName,
  summary,
  arguments: args,
  status,
  result,
  executionTime,
  timestamp
}: ToolCallBoxProps) {
  const [expanded, setExpanded] = useState(false)

  // Generate summary if not provided
  const displaySummary = summary || generateToolSummary(toolName, args)

  // Status styles
  const statusStyles = {
    pending: 'border-yellow-500 bg-yellow-500/10 animate-pulse',
    executing: 'border-blue-500 bg-blue-500/10',
    complete: 'border-green-500 bg-green-500/10',
    failed: 'border-red-500 bg-red-500/10'
  }

  const statusIcons = {
    pending: '⏳',
    executing: '⚙️',
    complete: '✅',
    failed: '❌'
  }

  const statusText = {
    pending: 'Pending',
    executing: 'Executing',
    complete: 'Complete',
    failed: 'Failed'
  }

  return (
    <div className={`border-l-4 ${statusStyles[status]} rounded-lg p-3 my-2 bg-slate-700/50`}>
      <div 
        className="flex justify-between items-center cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{statusIcons[status]}</span>
            <span className="text-blue-400 font-medium">{formatToolName(toolName)}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              status === 'complete' ? 'bg-green-500/20 text-green-400' :
              status === 'failed' ? 'bg-red-500/20 text-red-400' :
              status === 'executing' ? 'bg-blue-500/20 text-blue-400' :
              'bg-yellow-500/20 text-yellow-400'
            }`}>
              {statusText[status]}
            </span>
          </div>
          <p className="text-gray-300 text-sm mt-1">{displaySummary}</p>
          {executionTime && (
            <p className="text-gray-500 text-xs mt-1">
              Execution time: {executionTime.toFixed(0)}ms
            </p>
          )}
        </div>
        <div className="ml-4">
          {expanded ? (
            <ChevronDownIcon className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRightIcon className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-600/50 space-y-3">
          {/* Arguments */}
          {args && Object.keys(args).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Arguments:</h4>
              <pre className="text-xs text-gray-300 bg-black/30 rounded p-2 overflow-x-auto">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          )}

          {/* Result */}
          {result && (
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Result:</h4>
              <div className="text-sm text-gray-300 bg-black/30 rounded p-2">
                {renderToolResult(result)}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="text-xs text-gray-500">
            <p>Tool Call ID: {id}</p>
            <p>Timestamp: {new Date(timestamp).toLocaleTimeString()}</p>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to generate tool summaries
function generateToolSummary(toolName: string, args: any): string {
  const summaries: { [key: string]: (args: any) => string } = {
    'call_research_team': (args) => `Researching: ${args.task_description?.substring(0, 50)}...`,
    'call_analysis_team': (args) => `Analyzing: ${args.task_description?.substring(0, 50)}...`,
    'call_writing_team': (args) => `Writing ${args.content_type || 'content'}: ${args.task_description?.substring(0, 50)}...`,
    'call_rating_team': (args) => `Rating: ${args.task_description?.substring(0, 50)}...`,
    'respond_to_user': (args) => `Responding: ${args.message?.substring(0, 50)}...`
  }

  const generator = summaries[toolName]
  return generator ? generator(args) : `Calling ${toolName}`
}

// Helper function to format tool names
function formatToolName(toolName: string): string {
  const formatted: { [key: string]: string } = {
    'call_research_team': 'Research Team',
    'call_analysis_team': 'Analysis Team',
    'call_writing_team': 'Writing Team',
    'call_rating_team': 'Rating Team',
    'respond_to_user': 'User Response'
  }

  return formatted[toolName] || toolName
}

// Helper function to render tool results
function renderToolResult(result: any): React.ReactNode {
  if (typeof result === 'string') {
    return result
  }

  if (result.tool_name) {
    // This is a team result
    const { findings, metadata } = result
    return (
      <div className="space-y-2">
        {findings?.summary && (
          <div>
            <p className="font-medium text-green-400">Summary:</p>
            <p>{findings.summary}</p>
          </div>
        )}
        {findings?.key_points && (
          <div>
            <p className="font-medium text-blue-400">Key Points:</p>
            <ul className="list-disc list-inside">
              {findings.key_points.map((point: string, i: number) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
          </div>
        )}
        {metadata?.workers_used && (
          <p className="text-xs text-gray-500 mt-2">
            Workers: {metadata.workers_used.join(', ')}
          </p>
        )}
      </div>
    )
  }

  // Fallback to JSON
  return (
    <pre className="text-xs overflow-x-auto">
      {JSON.stringify(result, null, 2)}
    </pre>
  )
}