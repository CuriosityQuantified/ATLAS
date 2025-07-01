'use client'

import { useState } from 'react'
import { ChevronRightIcon, ChevronDownIcon, ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline'

interface JSONRendererProps {
  data: any  // JSON object or string
  className?: string
  mimeType?: string
  filename?: string
  size?: number
}

interface JSONTreeProps {
  data: any
  level?: number
  parentKey?: string
}

function JSONTree({ data, level = 0, parentKey }: JSONTreeProps) {
  const [collapsed, setCollapsed] = useState<{ [key: string]: boolean }>({})

  const isObject = (value: any) => value !== null && typeof value === 'object' && !Array.isArray(value)
  const isArray = (value: any) => Array.isArray(value)
  const isPrimitive = (value: any) => !isObject(value) && !isArray(value)

  const toggleCollapse = (key: string) => {
    setCollapsed(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const renderValue = (value: any, key: string, index?: number) => {
    const fullKey = parentKey ? `${parentKey}.${key}` : key
    const isCollapsed = collapsed[fullKey]

    if (isPrimitive(value)) {
      return (
        <div className="flex items-center" style={{ marginLeft: `${level * 16}px` }}>
          <span className="text-accent text-sm font-medium mr-2">{key}:</span>
          <span className={`text-sm ${
            typeof value === 'string' ? 'text-green-400' :
            typeof value === 'number' ? 'text-blue-400' :
            typeof value === 'boolean' ? 'text-purple-400' :
            'text-gray-400'
          }`}>
            {typeof value === 'string' ? `"${value}"` : String(value)}
          </span>
        </div>
      )
    }

    if (isArray(value)) {
      return (
        <div>
          <div 
            className="flex items-center cursor-pointer hover:bg-card-bg/30 rounded px-1"
            style={{ marginLeft: `${level * 16}px` }}
            onClick={() => toggleCollapse(fullKey)}
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-3 h-3 text-muted mr-1" />
            ) : (
              <ChevronDownIcon className="w-3 h-3 text-muted mr-1" />
            )}
            <span className="text-accent text-sm font-medium mr-2">{key}:</span>
            <span className="text-yellow-400 text-sm">
              [{value.length} item{value.length !== 1 ? 's' : ''}]
            </span>
          </div>
          {!isCollapsed && (
            <div className="mt-1">
              {value.map((item: any, idx: number) => (
                <div key={idx}>
                  {renderValue(item, `[${idx}]`, idx)}
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }

    if (isObject(value)) {
      const keys = Object.keys(value)
      return (
        <div>
          <div 
            className="flex items-center cursor-pointer hover:bg-card-bg/30 rounded px-1"
            style={{ marginLeft: `${level * 16}px` }}
            onClick={() => toggleCollapse(fullKey)}
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-3 h-3 text-muted mr-1" />
            ) : (
              <ChevronDownIcon className="w-3 h-3 text-muted mr-1" />
            )}
            <span className="text-accent text-sm font-medium mr-2">{key}:</span>
            <span className="text-orange-400 text-sm">
              {'{' + keys.length + ' key' + (keys.length !== 1 ? 's' : '') + '}'}
            </span>
          </div>
          {!isCollapsed && (
            <div className="mt-1">
              {keys.map(objKey => (
                <div key={objKey}>
                  <JSONTree 
                    data={value[objKey]} 
                    level={level + 1} 
                    parentKey={fullKey}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }

    return null
  }

  if (isObject(data)) {
    return (
      <div>
        {Object.keys(data).map(key => (
          <div key={key} className="mb-1">
            {renderValue(data[key], key)}
          </div>
        ))}
      </div>
    )
  }

  if (isArray(data)) {
    return (
      <div>
        {data.map((item: any, index: number) => (
          <div key={index} className="mb-1">
            {renderValue(item, `[${index}]`, index)}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="text-text text-sm">
      {typeof data === 'string' ? `"${data}"` : String(data)}
    </div>
  )
}

export default function JSONRenderer({ 
  data, 
  className = '',
  mimeType,
  filename,
  size 
}: JSONRendererProps) {
  const [copied, setCopied] = useState(false)
  const [viewMode, setViewMode] = useState<'tree' | 'raw'>('tree')

  // Parse JSON if it's a string
  let jsonData = data
  if (typeof data === 'string') {
    try {
      jsonData = JSON.parse(data)
    } catch (error) {
      jsonData = { error: 'Invalid JSON', raw: data }
    }
  }

  const jsonString = JSON.stringify(jsonData, null, 2)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy JSON:', error)
    }
  }

  return (
    <div className={`bg-card-glass/50 border border-border rounded-lg overflow-hidden ${className}`}>
      {/* JSON Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-card-bg/50 border-b border-border">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium text-text">
            {filename || 'JSON Data'}
          </span>
          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded">
            JSON
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="flex bg-card-bg rounded overflow-hidden">
            <button
              onClick={() => setViewMode('tree')}
              className={`px-2 py-1 text-xs transition-colors ${
                viewMode === 'tree' 
                  ? 'bg-primary text-white' 
                  : 'text-muted hover:text-text'
              }`}
            >
              Tree
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-2 py-1 text-xs transition-colors ${
                viewMode === 'raw' 
                  ? 'bg-primary text-white' 
                  : 'text-muted hover:text-text'
              }`}
            >
              Raw
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2 py-1 text-xs text-muted hover:text-text bg-transparent hover:bg-card-bg rounded transition-colors"
            title="Copy JSON"
          >
            {copied ? (
              <>
                <CheckIcon className="w-3 h-3" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <ClipboardIcon className="w-3 h-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* JSON Content */}
      <div className="p-4 max-h-96 overflow-auto">
        {viewMode === 'tree' ? (
          <JSONTree data={jsonData} />
        ) : (
          <pre className="text-sm text-text font-mono whitespace-pre-wrap">
            {jsonString}
          </pre>
        )}
      </div>

      {/* JSON Stats */}
      {size && (
        <div className="px-4 py-2 bg-card-bg/30 border-t border-border text-xs text-muted">
          {Object.keys(jsonData).length} keys • {size} bytes
        </div>
      )}
    </div>
  )
}