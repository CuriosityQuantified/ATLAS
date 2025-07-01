'use client'

import { ArrowDownTrayIcon, DocumentIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

interface FileRendererProps {
  data: string  // File URL or base64 data
  className?: string
  mimeType?: string
  filename?: string
  size?: number
}

export default function FileRenderer({ 
  data, 
  className = '',
  mimeType = 'application/octet-stream',
  filename = 'file.bin',
  size 
}: FileRendererProps) {
  
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('pdf')) return '📄'
    if (mimeType.includes('word') || mimeType.includes('document')) return '📝'
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊'
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return '📺'
    if (mimeType.includes('zip') || mimeType.includes('archive')) return '🗜️'
    if (mimeType.includes('text')) return '📄'
    if (mimeType.includes('json')) return '📋'
    if (mimeType.includes('csv')) return '📊'
    return '📎'
  }

  const getFileTypeLabel = (mimeType: string) => {
    if (mimeType.includes('pdf')) return 'PDF Document'
    if (mimeType.includes('word') || mimeType.includes('document')) return 'Word Document'
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'Excel Spreadsheet'
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return 'PowerPoint Presentation'
    if (mimeType.includes('zip')) return 'ZIP Archive'
    if (mimeType.includes('text/plain')) return 'Text File'
    if (mimeType.includes('application/json')) return 'JSON Data'
    if (mimeType.includes('csv')) return 'CSV Data'
    return 'File'
  }

  const handleDownload = () => {
    try {
      let downloadUrl = data
      
      // Handle base64 data
      if (!data.startsWith('http') && !data.startsWith('data:')) {
        downloadUrl = `data:${mimeType};base64,${data}`
      }
      
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('Failed to download file:', error)
    }
  }

  const canPreview = (mimeType: string) => {
    return mimeType.includes('pdf') || 
           mimeType.includes('text/plain') ||
           mimeType.includes('application/json')
  }

  const handlePreview = () => {
    if (mimeType.includes('pdf')) {
      // Open PDF in new tab
      window.open(data, '_blank')
    }
    // For other preview types, we would implement modal viewers
  }

  return (
    <div className={`bg-card-glass/50 border border-border rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        {/* File Icon */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-card-bg rounded-lg flex items-center justify-center text-2xl">
            {getFileIcon(mimeType)}
          </div>
        </div>

        {/* File Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-medium text-text truncate">
                {filename}
              </h3>
              <p className="text-xs text-muted mt-1">
                {getFileTypeLabel(mimeType)}
              </p>
              <p className="text-xs text-muted">
                {formatFileSize(size)}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2 ml-3">
              {canPreview(mimeType) && (
                <button
                  onClick={handlePreview}
                  className="p-2 text-muted hover:text-text bg-card-bg hover:bg-card-bg/80 rounded-lg transition-colors"
                  title="Preview file"
                >
                  <DocumentTextIcon className="w-4 h-4" />
                </button>
              )}
              
              <button
                onClick={handleDownload}
                className="p-2 text-primary hover:text-primary-light bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors"
                title="Download file"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* File Metadata */}
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-card-bg text-muted">
              {mimeType}
            </span>
            
            {size && size > 1024 * 1024 && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-500/10 text-yellow-400">
                Large File
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Preview Section for Text Files */}
      {mimeType.includes('text/plain') && data.length < 1000 && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="text-xs text-muted mb-2">File Preview:</div>
          <div className="bg-card-bg/50 rounded p-3 text-sm text-text font-mono max-h-32 overflow-y-auto">
            {data.split('\n').slice(0, 10).map((line, index) => (
              <div key={index} className="whitespace-pre-wrap">
                {line || '\u00A0'}
              </div>
            ))}
            {data.split('\n').length > 10 && (
              <div className="text-muted italic">... and {data.split('\n').length - 10} more lines</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}