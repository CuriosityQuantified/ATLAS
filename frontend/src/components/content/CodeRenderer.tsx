'use client'

import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import { ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline'

interface CodeRendererProps {
  data: string
  className?: string
  mimeType?: string
  filename?: string
  size?: number
}

export default function CodeRenderer({ 
  data, 
  className = '',
  mimeType,
  filename,
  size 
}: CodeRendererProps) {
  const [copied, setCopied] = useState(false)

  // Detect language from filename or mimeType
  const detectLanguage = () => {
    if (filename) {
      const ext = filename.split('.').pop()?.toLowerCase()
      const languageMap: { [key: string]: string } = {
        'js': 'javascript',
        'jsx': 'jsx',
        'ts': 'typescript',
        'tsx': 'tsx',
        'py': 'python',
        'rb': 'ruby',
        'go': 'go',
        'rs': 'rust',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'cs': 'csharp',
        'php': 'php',
        'sh': 'bash',
        'sql': 'sql',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'xml': 'xml',
        'html': 'html',
        'css': 'css',
        'scss': 'scss',
        'md': 'markdown'
      }
      return languageMap[ext || ''] || 'text'
    }
    return 'text'
  }

  const language = detectLanguage()

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(data)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy code:', error)
    }
  }

  const getLanguageLabel = (lang: string) => {
    const labelMap: { [key: string]: string } = {
      'javascript': 'JavaScript',
      'typescript': 'TypeScript',
      'python': 'Python',
      'jsx': 'React JSX',
      'tsx': 'React TSX',
      'bash': 'Shell Script',
      'json': 'JSON',
      'yaml': 'YAML',
      'markdown': 'Markdown'
    }
    return labelMap[lang] || lang.toUpperCase()
  }

  return (
    <div className={`bg-card-glass/50 border border-border rounded-lg overflow-hidden ${className}`}>
      {/* Code Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-card-bg/50 border-b border-border">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium text-text">
            {filename || 'Code'}
          </span>
          <span className="px-2 py-1 bg-primary/20 text-primary text-xs rounded">
            {getLanguageLabel(language)}
          </span>
        </div>
        
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 px-2 py-1 text-xs text-muted hover:text-text bg-transparent hover:bg-card-bg rounded transition-colors"
          title="Copy code"
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

      {/* Code Content */}
      <div className="relative">
        <SyntaxHighlighter
          language={language}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent',
            fontSize: '0.875rem',
            lineHeight: '1.5'
          }}
          showLineNumbers={data.split('\n').length > 5}
          wrapLines={true}
          wrapLongLines={true}
        >
          {data}
        </SyntaxHighlighter>
      </div>

      {/* Code Stats */}
      {size && (
        <div className="px-4 py-2 bg-card-bg/30 border-t border-border text-xs text-muted">
          {data.split('\n').length} lines • {size} bytes
        </div>
      )}
    </div>
  )
}