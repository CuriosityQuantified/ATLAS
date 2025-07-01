'use client'

import { useState } from 'react'
import { XMarkIcon, ArrowDownTrayIcon, EyeIcon } from '@heroicons/react/24/outline'

interface ImageRendererProps {
  data: string  // Base64 data or URL
  className?: string
  mimeType?: string
  filename?: string
  size?: number
}

export default function ImageRenderer({ 
  data, 
  className = '',
  mimeType = 'image/png',
  filename = 'image.png',
  size 
}: ImageRendererProps) {
  const [isZoomed, setIsZoomed] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  // Handle image URL format (base64 or regular URL)
  const imageUrl = data.startsWith('data:') ? data : `data:${mimeType};base64,${data}`
  
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleDownload = () => {
    try {
      const link = document.createElement('a')
      link.href = imageUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('Failed to download image:', error)
    }
  }

  const handleImageLoad = () => {
    setIsLoading(false)
    setHasError(false)
  }

  const handleImageError = () => {
    setIsLoading(false)
    setHasError(true)
  }

  if (hasError) {
    return (
      <div className={`p-4 bg-red-500/10 border border-red-500/20 rounded-lg ${className}`}>
        <div className="flex items-center space-x-2 text-red-400">
          <span className="text-sm font-medium">Failed to load image</span>
        </div>
        <div className="text-red-300 text-xs mt-1">
          {filename} • {formatFileSize(size)}
        </div>
      </div>
    )
  }

  return (
    <>
      <div className={`relative group ${className}`}>
        {/* Image Container */}
        <div className="relative bg-card-bg/50 rounded-lg border border-border overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-card-bg">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          )}
          
          <img
            src={imageUrl}
            alt={filename}
            className="max-w-full h-auto max-h-64 object-contain cursor-pointer transition-transform hover:scale-105"
            onClick={() => setIsZoomed(true)}
            onLoad={handleImageLoad}
            onError={handleImageError}
          />
          
          {/* Overlay Controls */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors">
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <div className="flex space-x-1">
                <button
                  onClick={() => setIsZoomed(true)}
                  className="p-1.5 bg-black/50 hover:bg-black/70 rounded text-white transition-colors"
                  title="View full size"
                >
                  <EyeIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={handleDownload}
                  className="p-1.5 bg-black/50 hover:bg-black/70 rounded text-white transition-colors"
                  title="Download image"
                >
                  <ArrowDownTrayIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Image Metadata */}
        <div className="mt-2 text-xs text-muted">
          <div className="flex items-center justify-between">
            <span>{filename}</span>
            <span>{formatFileSize(size)}</span>
          </div>
          <div className="mt-1">
            <span className="bg-card-bg px-2 py-1 rounded text-xs">{mimeType}</span>
          </div>
        </div>
      </div>

      {/* Zoom Modal */}
      {isZoomed && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="relative max-w-7xl max-h-full">
            {/* Close Button */}
            <button
              onClick={() => setIsZoomed(false)}
              className="absolute -top-10 right-0 p-2 text-white hover:text-gray-300 transition-colors"
              title="Close"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
            
            {/* Full Size Image */}
            <img
              src={imageUrl}
              alt={filename}
              className="max-w-full max-h-full object-contain"
            />
            
            {/* Image Info */}
            <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white p-4">
              <div className="flex items-center justify-between text-sm">
                <span>{filename}</span>
                <div className="flex items-center space-x-4">
                  <span>{formatFileSize(size)}</span>
                  <button
                    onClick={handleDownload}
                    className="flex items-center space-x-1 px-3 py-1 bg-primary hover:bg-primary-light rounded transition-colors"
                  >
                    <ArrowDownTrayIcon className="w-4 h-4" />
                    <span>Download</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}