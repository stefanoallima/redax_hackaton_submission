/**
 * Learning Confirmation Modal Component
 * Shows Gemini results and allows users to confirm/deny entities for learning
 */
import React, { useState } from 'react'
import { Check, X, Sparkles, Database, AlertCircle, Info } from 'lucide-react'

interface GeminiEntity {
  text: string
  entity_type: string
  page: number
  confidence: number
  source: string
}

interface LearningConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  geminiResults: {
    entities: GeminiEntity[]
    summary: {
      total_entities: number
      by_type: Record<string, number>
      pages_analyzed: number
    }
  } | null
  onConfirm: (confirmed: GeminiEntity[], denied: GeminiEntity[]) => Promise<void>
  isLearning: boolean
}

export const LearningConfirmationModal: React.FC<LearningConfirmationModalProps> = ({
  isOpen,
  onClose,
  geminiResults,
  onConfirm,
  isLearning
}) => {
  const [entityStates, setEntityStates] = useState<Record<number, 'confirmed' | 'denied' | 'pending'>>({})

  // Initialize entity states when modal opens
  React.useEffect(() => {
    if (isOpen && geminiResults && geminiResults.entities && geminiResults.entities.length > 0) {
      const initial: Record<number, 'confirmed' | 'denied' | 'pending'> = {}
      geminiResults.entities.forEach((_, idx) => {
        initial[idx] = 'pending'
      })
      setEntityStates(initial)
    }
  }, [isOpen, geminiResults])

  // Reset state when modal closes
  React.useEffect(() => {
    if (!isOpen) {
      setEntityStates({})
    }
  }, [isOpen])

  if (!isOpen || !geminiResults) return null

  const { entities, summary } = geminiResults

  const handleToggle = (index: number, state: 'confirmed' | 'denied') => {
    setEntityStates(prev => ({
      ...prev,
      [index]: prev[index] === state ? 'pending' : state
    }))
  }

  const handleConfirmAll = () => {
    const allConfirmed: Record<number, 'confirmed' | 'denied' | 'pending'> = {}
    entities.forEach((_, idx) => {
      allConfirmed[idx] = 'confirmed'
    })
    setEntityStates(allConfirmed)
  }

  const handleSubmit = async () => {
    const confirmed: GeminiEntity[] = []
    const denied: GeminiEntity[] = []

    Object.entries(entityStates).forEach(([idxStr, state]) => {
      const idx = parseInt(idxStr)
      if (state === 'confirmed') {
        confirmed.push(entities[idx])
      } else if (state === 'denied') {
        denied.push(entities[idx])
      }
    })

    await onConfirm(confirmed, denied)
    setEntityStates({})  // Reset for next time
    onClose()
  }

  const confirmedCount = Object.values(entityStates).filter(s => s === 'confirmed').length
  const deniedCount = Object.values(entityStates).filter(s => s === 'denied').length
  const pendingCount = Object.values(entityStates).filter(s => s === 'pending').length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-purple-500" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Gemini AI Results
              </h2>
              <p className="text-sm text-gray-600">
                {summary.total_entities} entities found in {summary.pages_analyzed} pages
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isLearning}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Summary Stats */}
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="text-2xl font-bold text-green-700">{confirmedCount}</div>
              <div className="text-xs text-green-600">Confirmed</div>
            </div>
            <div className="p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="text-2xl font-bold text-red-700">{deniedCount}</div>
              <div className="text-xs text-red-600">Denied</div>
            </div>
            <div className="p-3 bg-gray-100 rounded-lg border border-gray-300">
              <div className="text-2xl font-bold text-gray-700">{pendingCount}</div>
              <div className="text-xs text-gray-600">Pending</div>
            </div>
          </div>
        </div>

        {/* Info Box */}
        <div className="p-4 bg-blue-50 border-b border-blue-200">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-blue-800">
              <strong>Confirm the correct entities</strong> to teach them to the local model.
              Confirmed entities will be automatically recognized in future standard scans.
            </p>
          </div>
        </div>

        {/* Entity List (scrollable) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2">
          {entities.map((entity, idx) => {
            const state = entityStates[idx] || 'pending'
            return (
              <div
                key={idx}
                className={`
                  p-4 rounded-lg border-2 transition-all
                  ${state === 'confirmed' ? 'border-green-500 bg-green-50' : ''}
                  ${state === 'denied' ? 'border-red-500 bg-red-50' : ''}
                  ${state === 'pending' ? 'border-gray-200 bg-white' : ''}
                `}
              >
                <div className="flex items-start justify-between">
                  {/* Entity Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-semibold text-gray-900">
                        {entity.text}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 rounded">
                        {entity.entity_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        Page {entity.page}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      Confidence: {(entity.confidence * 100).toFixed(0)}%
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleToggle(idx, 'confirmed')}
                      disabled={isLearning}
                      className={`
                        p-2 rounded-lg transition-all
                        ${state === 'confirmed'
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-600'
                        }
                        ${isLearning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                      title="Confirm entity"
                    >
                      <Check className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleToggle(idx, 'denied')}
                      disabled={isLearning}
                      className={`
                        p-2 rounded-lg transition-all
                        ${state === 'denied'
                          ? 'bg-red-500 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-red-100 hover:text-red-600'
                        }
                        ${isLearning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                      title="Deny entity"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={handleConfirmAll}
              disabled={isLearning}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Confirm All
            </button>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isLearning}
              className={`
                flex-1 px-6 py-3 rounded-lg font-semibold transition-colors
                ${isLearning
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }
              `}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isLearning || confirmedCount === 0}
              className={`
                flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold
                transition-all shadow-md
                ${isLearning || confirmedCount === 0
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-green-600 to-blue-600 text-white hover:from-green-700 hover:to-blue-700'
                }
              `}
            >
              <Database className="w-5 h-5" />
              <span>
                {isLearning
                  ? 'Learning in progress...'
                  : `Learn ${confirmedCount} ${confirmedCount === 1 ? 'entity' : 'entities'}`
                }
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
