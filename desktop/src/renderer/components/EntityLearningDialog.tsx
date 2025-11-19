/**
 * Entity Learning Dialog
 * 3-state classification for detected entities:
 * 1. ALWAYS REDACT - Add to allow-list (force detect in future)
 * 2. REVIEW EACH TIME - No learning (context-dependent)
 * 3. NEVER REDACT - Add to deny-list (ignore in future)
 */
import React, { useState } from 'react'
import { CheckCircle2, AlertCircle, XCircle, HelpCircle } from 'lucide-react'

interface EntityLearningDialogProps {
  entityText: string
  entityType: string
  currentClassification?: 'always' | 'flag' | 'neutral' | 'never'
  onClassify: (classification: 'always' | 'flag' | 'neutral' | 'never') => void
  onClose: () => void
}

export default function EntityLearningDialog({
  entityText,
  entityType,
  currentClassification,
  onClassify,
  onClose
}: EntityLearningDialogProps) {
  const [showHelp, setShowHelp] = useState(false)
  const isEditing = !!currentClassification

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="px-6 py-4 border-b bg-gray-50">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              {isEditing ? 'Edit learning classification' : 'How should I handle this term in the future?'}
            </h3>
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              title="Show help"
            >
              <HelpCircle className="w-5 h-5 text-gray-600" />
            </button>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {entityType}
            </span>
            <span className="text-lg font-mono bg-gray-100 px-3 py-1 rounded">
              "{entityText}"
            </span>
            {isEditing && (
              <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-medium">
                Current: {
                  currentClassification === 'always' ? '✓✓ Always' :
                  currentClassification === 'flag' ? '⚠ Flag' :
                  currentClassification === 'never' ? '✗✗ Never' :
                  '○ Neutral'
                }
              </span>
            )}
          </div>
        </div>

        {/* Editing Notice */}
        {isEditing && (
          <div className="px-6 py-3 bg-amber-50 border-b border-amber-200">
            <p className="text-sm text-amber-900">
              <strong>Editing:</strong> Changing this will update the stored preference. The previous classification will be removed.
            </p>
          </div>
        )}

        {/* Help Section */}
        {showHelp && (
          <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
            <div className="space-y-2 text-sm text-blue-900">
              <p><strong>Why this matters:</strong></p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><strong>Always Redact:</strong> Force-detect and auto-redact in all future documents</li>
                <li><strong>Flag to Review:</strong> Always detect but prompt for manual review (highlights ambiguous terms)</li>
                <li><strong>Neutral:</strong> Standard AI detection, no preference saved</li>
                <li><strong>Never Redact:</strong> Permanently ignore, never detect again</li>
              </ul>
            </div>
          </div>
        )}

        {/* Options */}
        <div className="p-6 space-y-3">
          {/* Option 1: Always Redact */}
          <button
            onClick={() => onClassify('always')}
            className={`w-full p-4 border-2 rounded-lg transition-colors text-left group ${
              currentClassification === 'always'
                ? 'border-green-500 bg-green-100 ring-2 ring-green-400'
                : 'border-green-300 bg-green-50 hover:bg-green-100'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="w-7 h-7 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-green-900 mb-1">
                  ✓✓ ALWAYS Redact This Term
                </h4>
                <p className="text-sm text-green-800 mb-2">
                  Add to <strong>Allow-List</strong> - Will be automatically detected and redacted in all future documents
                </p>
                <div className="text-xs text-green-700 bg-green-100 px-3 py-2 rounded">
                  <strong>Use when:</strong> This term is ALWAYS sensitive (e.g., your client's real name, your law firm name, specific sensitive company)
                </div>
                <div className="mt-2 text-xs text-green-600">
                  Example: "Mario Rossi" (your client), "ABC Legal Services" (your firm)
                </div>
              </div>
            </div>
          </button>

          {/* Option 2: Flag to Review */}
          <button
            onClick={() => onClassify('flag')}
            className={`w-full p-4 border-2 rounded-lg transition-colors text-left group ${
              currentClassification === 'flag'
                ? 'border-orange-500 bg-orange-100 ring-2 ring-orange-400'
                : 'border-orange-300 bg-orange-50 hover:bg-orange-100'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center">
                  <AlertCircle className="w-7 h-7 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-orange-900 mb-1">
                  ⚠ FLAG to Review (Context-Dependent)
                </h4>
                <p className="text-sm text-orange-800 mb-2">
                  Add to allow-list but mark for manual review - AI will ALWAYS detect it, you decide each time
                </p>
                <div className="text-xs text-orange-700 bg-orange-100 px-3 py-2 rounded">
                  <strong>Use when:</strong> Term has multiple meanings - you want it highlighted but need to decide based on context
                </div>
                <div className="mt-2 text-xs text-orange-600">
                  Example: "Rossi" (person OR wine), "Milano" (person OR city), "Corona" (surname OR brand)
                </div>
              </div>
            </div>
          </button>

          {/* Option 3: Neutral (No Learning) */}
          <button
            onClick={() => onClassify('neutral')}
            className={`w-full p-4 border-2 rounded-lg transition-colors text-left group ${
              currentClassification === 'neutral'
                ? 'border-gray-500 bg-gray-100 ring-2 ring-gray-400'
                : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-12 h-12 bg-gray-500 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 border-4 border-white rounded-full"></div>
                </div>
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-gray-900 mb-1">
                  ○ NEUTRAL (No Preference)
                </h4>
                <p className="text-sm text-gray-800 mb-2">
                  Remove from all lists - standard AI detection, no learning
                </p>
                <div className="text-xs text-gray-700 bg-gray-100 px-3 py-2 rounded">
                  <strong>Use when:</strong> You want to reset and let AI decide naturally (undo previous classification)
                </div>
                <div className="mt-2 text-xs text-gray-600">
                  This removes the term from allow/deny lists entirely
                </div>
              </div>
            </div>
          </button>

          {/* Option 4: Never Redact */}
          <button
            onClick={() => onClassify('never')}
            className={`w-full p-4 border-2 rounded-lg transition-colors text-left group ${
              currentClassification === 'never'
                ? 'border-red-500 bg-red-100 ring-2 ring-red-400'
                : 'border-red-300 bg-red-50 hover:bg-red-100'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-1">
                <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                  <XCircle className="w-7 h-7 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-red-900 mb-1">
                  ✗✗ NEVER Redact This Term
                </h4>
                <p className="text-sm text-red-800 mb-2">
                  Add to <strong>Deny-List</strong> - Will be permanently ignored in all future documents
                </p>
                <div className="text-xs text-red-700 bg-red-100 px-3 py-2 rounded">
                  <strong>Use when:</strong> This is a common false positive that should NEVER be redacted (legal titles, public entities, countries)
                </div>
                <div className="mt-2 text-xs text-red-600">
                  Example: "Giudice" (judge title), "Tribunale" (court), "Italia" (country), "Presidente" (title)
                </div>
              </div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {isEditing
              ? 'Your updated choice will replace the previous classification'
              : 'Your choice will be saved for future documents'
            }
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
