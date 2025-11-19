/**
 * Scan Mode Selector Component
 * Allows users to choose between Standard Scan (local) and Gemini Scan (cloud AI)
 */
import React from 'react'
import { Zap, Sparkles, Database, Info } from 'lucide-react'

export type ScanMode = 'standard' | 'gemini'

interface ScanModeSelectorProps {
  selectedMode: ScanMode
  onModeChange: (mode: ScanMode) => void
  learnedCount: number  // Number of entities learned from Gemini
  disabled?: boolean
}

export const ScanModeSelector: React.FC<ScanModeSelectorProps> = ({
  selectedMode,
  onModeChange,
  learnedCount,
  disabled = false
}) => {
  return (
    <div className="w-full space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Info className="w-4 h-4 text-blue-500" />
        <h3 className="text-sm font-medium text-gray-700">Scan Mode</h3>
      </div>

      {/* Mode Selection */}
      <div className="grid grid-cols-2 gap-4">
        {/* Standard Scan */}
        <button
          onClick={() => !disabled && onModeChange('standard')}
          disabled={disabled}
          className={`
            relative p-4 rounded-lg border-2 transition-all
            ${selectedMode === 'standard'
              ? 'border-blue-500 bg-blue-50 shadow-md'
              : 'border-gray-200 bg-white hover:border-blue-300'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          {/* Free Badge */}
          <div className="absolute top-2 right-2">
            <span className="px-2 py-0.5 text-xs font-semibold text-green-700 bg-green-100 rounded-full">
              FREE
            </span>
          </div>

          {/* Icon */}
          <div className="flex justify-center mb-2">
            <Zap className={`w-8 h-8 ${selectedMode === 'standard' ? 'text-blue-500' : 'text-gray-400'}`} />
          </div>

          {/* Title */}
          <h4 className="text-base font-semibold text-gray-900 mb-1">
            Standard Scan
          </h4>

          {/* Description */}
          <p className="text-xs text-gray-600 mb-2">
            Local scan with ML (GLiNER + Presidio)
          </p>

          {/* Learned Entities Badge */}
          {learnedCount > 0 && (
            <div className="flex items-center gap-1 mt-2 p-2 bg-purple-50 rounded border border-purple-200">
              <Database className="w-3 h-3 text-purple-600" />
              <span className="text-xs font-medium text-purple-700">
                {learnedCount} terms learned from Gemini for redaction
              </span>
            </div>
          )}

          {/* Performance Stats */}
          <div className="mt-2 text-xs text-gray-500">
            <div>•Intelligent textual matching (GLiNER + Presidio)</div>
            <div>• Time: ~5-30s</div>
          </div>
        </button>

        {/* Gemini Scan */}
        <button
          onClick={() => !disabled && onModeChange('gemini')}
          disabled={disabled}
          className={`
            relative p-4 rounded-lg border-2 transition-all
            ${selectedMode === 'gemini'
              ? 'border-purple-500 bg-purple-50 shadow-md'
              : 'border-gray-200 bg-white hover:border-purple-300'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          {/* Premium Badge */}
          <div className="absolute top-2 right-2">
            <span className="px-2 py-0.5 text-xs font-semibold text-purple-700 bg-purple-100 rounded-full">
              PREMIUM
            </span>
          </div>

          {/* Icon */}
          <div className="flex justify-center mb-2">
            <Sparkles className={`w-8 h-8 ${selectedMode === 'gemini' ? 'text-purple-500' : 'text-gray-400'}`} />
          </div>

          {/* Title */}
          <h4 className="text-base font-semibold text-gray-900 mb-1">
            Gemini Scan
          </h4>

          {/* Description */}
          <p className="text-xs text-gray-600 mb-2">
            Multimodal AI for maximum precision
          </p>

          {/* Learning Feature */}
          <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
            <p className="text-xs font-medium text-blue-700">
              ✨ Teaches the local model
            </p>
          </div>

          {/* Performance Stats */}
          <div className="mt-2 text-xs text-gray-500">
            <div>• F1 Score: ~95%+</div>
            <div>• Time: ~10-20s</div>
          </div>
        </button>
      </div>

      {/* Info Box */}
      {selectedMode === 'gemini' && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-yellow-800">
              <strong>Privacy:</strong> The document will be sent to Google Gemini API for analysis.
              Confirmed results will be saved locally to improve future scans.
            </div>
          </div>
        </div>
      )}

      {/* Learning Loop Explanation */}
      {learnedCount > 0 && selectedMode === 'standard' && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Database className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-green-800">
              <strong>Active Learning:</strong> Thanks to previous Gemini scans, this
              model now automatically recognizes {learnedCount} additional entity types!
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
