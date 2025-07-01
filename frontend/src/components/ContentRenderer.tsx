'use client'

import { MessageContent, isLegacyTextMessage, isMultiModalContent } from './AgentDialogue'
import TextRenderer from './content/TextRenderer'
import ImageRenderer from './content/ImageRenderer'
import FileRenderer from './content/FileRenderer'
import AudioRenderer from './content/AudioRenderer'
import CodeRenderer from './content/CodeRenderer'
import JSONRenderer from './content/JSONRenderer'
import ChartRenderer from './content/ChartRenderer'

interface ContentRendererProps {
  content: MessageContent | string
  className?: string
}

export default function ContentRenderer({ content, className = '' }: ContentRendererProps) {
  // Handle legacy text messages
  if (isLegacyTextMessage(content)) {
    return (
      <TextRenderer 
        data={content} 
        className={className}
      />
    )
  }

  // Handle multi-modal content
  if (isMultiModalContent(content)) {
    const commonProps = {
      data: content.data,
      mimeType: content.mimeType,
      filename: content.filename,
      size: content.size,
      className
    }

    switch (content.type) {
      case 'text':
        return <TextRenderer {...commonProps} />
      
      case 'image':
        return <ImageRenderer {...commonProps} />
      
      case 'file':
        return <FileRenderer {...commonProps} />
      
      case 'audio':
        return <AudioRenderer {...commonProps} />
      
      case 'code':
        return <CodeRenderer {...commonProps} />
      
      case 'json':
        return <JSONRenderer {...commonProps} />
      
      case 'chart':
        return <ChartRenderer {...commonProps} />
      
      default:
        return (
          <div className={`p-3 bg-red-500/10 border border-red-500/20 rounded-lg ${className}`}>
            <div className="text-red-400 text-sm font-medium">Unsupported Content Type</div>
            <div className="text-red-300 text-xs mt-1">
              Content type "{(content as any).type}" is not supported
            </div>
          </div>
        )
    }
  }

  // Fallback for invalid content
  return (
    <div className={`p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg ${className}`}>
      <div className="text-yellow-400 text-sm font-medium">Invalid Content</div>
      <div className="text-yellow-300 text-xs mt-1">
        Content format is not recognized
      </div>
    </div>
  )
}