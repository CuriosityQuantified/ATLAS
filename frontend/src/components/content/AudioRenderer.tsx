'use client'

import { ArrowDownTrayIcon, SpeakerWaveIcon } from '@heroicons/react/24/outline'

interface AudioRendererProps {
  data: string  // Audio URL or base64 data
  className?: string
  mimeType?: string
  filename?: string
  size?: number
}

export default function AudioRenderer({ 
  data, 
  className = '',
  mimeType = 'audio/mp3',
  filename = 'audio.mp3',
  size 
}: AudioRendererProps) {
  
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  // Handle audio URL format (base64 or regular URL)
  const audioUrl = data.startsWith('data:') ? data : `data:${mimeType};base64,${data}`

  const handleDownload = () => {
    try {
      const link = document.createElement('a')
      link.href = audioUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('Failed to download audio:', error)
    }
  }

  return (
    <div className={`bg-card-glass/50 border border-border rounded-lg p-4 ${className}`}>
      <div className="flex items-center space-x-3 mb-3">
        <div className="w-10 h-10 bg-accent/20 rounded-lg flex items-center justify-center">
          <SpeakerWaveIcon className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-text truncate">
            {filename}
          </h3>
          <p className="text-xs text-muted">
            {formatFileSize(size)} • {mimeType}
          </p>
        </div>
        <button
          onClick={handleDownload}
          className="p-2 text-primary hover:text-primary-light bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors"
          title="Download audio"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Audio Player */}
      <audio
        controls
        className="w-full h-8"
        preload="metadata"
      >
        <source src={audioUrl} type={mimeType} />
        Your browser does not support the audio element.
      </audio>
    </div>
  )
}