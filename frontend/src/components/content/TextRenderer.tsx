'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

interface TextRendererProps {
  data: string
  className?: string
  mimeType?: string
  filename?: string
  size?: number
}

export default function TextRenderer({ 
  data, 
  className = '',
  mimeType,
  filename,
  size 
}: TextRendererProps) {
  
  // Check if content looks like markdown
  const isMarkdown = data.includes('##') || data.includes('**') || data.includes('```') || 
                    data.includes('* ') || data.includes('- ') || data.includes('[')
  
  if (isMarkdown) {
    return (
      <div className={`prose prose-invert prose-sm max-w-none ${className}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '')
              return !inline && match ? (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  className="rounded-md"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={`${className} bg-slate-700 px-1 py-0.5 rounded text-sm`} {...props}>
                  {children}
                </code>
              )
            },
            h1: ({ children }) => (
              <h1 className="text-xl font-bold text-text mb-3">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-lg font-semibold text-text mb-2">{children}</h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-base font-medium text-text mb-2">{children}</h3>
            ),
            p: ({ children }) => (
              <p className="text-text mb-2 leading-relaxed">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc list-inside text-text mb-2 space-y-1">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside text-text mb-2 space-y-1">{children}</ol>
            ),
            li: ({ children }) => (
              <li className="text-text">{children}</li>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-accent pl-4 italic text-muted mb-2">
                {children}
              </blockquote>
            ),
            a: ({ children, href }) => (
              <a 
                href={href} 
                className="text-primary hover:text-primary-light underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto mb-2">
                <table className="min-w-full border border-border rounded-lg">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-card-bg">{children}</thead>
            ),
            tbody: ({ children }) => (
              <tbody>{children}</tbody>
            ),
            tr: ({ children }) => (
              <tr className="border-b border-border">{children}</tr>
            ),
            th: ({ children }) => (
              <th className="px-4 py-2 text-left text-text font-medium">{children}</th>
            ),
            td: ({ children }) => (
              <td className="px-4 py-2 text-text">{children}</td>
            )
          }}
        >
          {data}
        </ReactMarkdown>
      </div>
    )
  }

  // Plain text rendering
  return (
    <div className={`text-text leading-relaxed whitespace-pre-wrap ${className}`}>
      {data}
    </div>
  )
}