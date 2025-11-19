/**
 * ErrorDisplay Component
 * Shows errors in a copyable text format
 */
import React, { useState } from 'react'
import { AlertCircle, Copy, X } from 'lucide-react'

interface ErrorDisplayProps {
  error: string | null
  onClose: () => void
}

export default function ErrorDisplay({ error, onClose }: ErrorDisplayProps) {
  const [copied, setCopied] = useState(false)

  if (!error) return null

  const handleCopy = () => {
    navigator.clipboard.writeText(error)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-red-50">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h3 className="text-lg font-semibold text-red-900">Errore</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-red-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-red-600" />
          </button>
        </div>

        {/* Error Content */}
        <div className="flex-1 overflow-auto p-4">
          <div className="bg-gray-50 border border-gray-300 rounded p-4 font-mono text-sm">
            <pre className="whitespace-pre-wrap break-words">{error}</pre>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
          <p className="text-sm text-gray-600">
            Puoi copiare questo messaggio di errore per condividerlo con il supporto
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors flex items-center gap-2"
            >
              <Copy className="w-4 h-4" />
              {copied ? 'Copiato!' : 'Copia Errore'}
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
            >
              Chiudi
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
