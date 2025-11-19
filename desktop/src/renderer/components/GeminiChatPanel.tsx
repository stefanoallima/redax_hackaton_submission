/**
 * Gemini Chat Panel Component
 * Allows users to customize the Gemini prompt and initiate AI-powered scans
 */
import React, { useState } from 'react'
import { Sparkles, Edit3, RotateCcw, Loader2, AlertCircle } from 'lucide-react'

interface GeminiChatPanelProps {
  onScan: (customPrompt?: string) => Promise<void>
  isLoading: boolean
  error?: string | null
}

const DEFAULT_PROMPT = `You are an expert in analyzing legal documents to identify personal data (PII).

Carefully analyze this PDF document and identify ALL the following types of personal information:

1. **PERSON** (Individuals): Full names and surnames (e.g., John Smith, Atty. Jane Doe)
2. **ORGANIZATION** (Entities/Organizations): Courts, companies, law firms (e.g., Court of Milan)
3. **LOCATION** (Specific places): Complete addresses, streets, cities with house numbers
4. **DATE_TIME** (Dates): Birth dates, hearings, judgments
5. **EMAIL_ADDRESS** (Email): Complete email addresses
6. **PHONE_NUMBER** (Phones): Phone numbers, fax, mobile phones
7. **IT_FISCAL_CODE** (Tax ID): Italian tax codes (16 characters)
8. **IT_VAT_CODE** (VAT Number): Italian VAT numbers
9. **IBAN** (Bank accounts): IBAN codes
10. **IT_IDENTITY_CARD** (Documents): ID card numbers, passport, driver's license

**IMPORTANT**:
- Extract the EXACT text as it appears in the document
- If a person appears multiple times, report each occurrence with the page number
- Include partial information if clearly identifiable (e.g., only surname if unique in the document)
- Ignore generic terms like "judge", "lawyer" without specific names
- For LOCATION, include only complete addresses, not just generic city names

Respond ONLY with a JSON array, without additional text.`

export const GeminiChatPanel: React.FC<GeminiChatPanelProps> = ({
  onScan,
  isLoading,
  error
}) => {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT)
  const [isEditing, setIsEditing] = useState(false)

  const handleScan = async () => {
    const finalPrompt = isEditing ? prompt : undefined
    await onScan(finalPrompt)
  }

  const handleReset = () => {
    setPrompt(DEFAULT_PROMPT)
    setIsEditing(false)
  }

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          <h3 className="text-lg font-semibold text-gray-900">
            Gemini AI - Advanced PII Detection
          </h3>
        </div>

        {/* Edit Toggle */}
        <button
          onClick={() => setIsEditing(!isEditing)}
          disabled={isLoading}
          className={`
            flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
            ${isEditing
              ? 'bg-purple-100 text-purple-700 border border-purple-300'
              : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
            }
            ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <Edit3 className="w-4 h-4" />
          {isEditing ? 'Edit Mode' : 'Customize Prompt'}
        </button>
      </div>

      {/* Prompt Display/Editor */}
      <div className="space-y-2">
        {isEditing ? (
          <>
            {/* Editable Textarea */}
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isLoading}
              className={`
                w-full h-64 p-4 border-2 rounded-lg font-mono text-sm
                focus:outline-none focus:ring-2 focus:ring-purple-500
                ${isLoading ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              `}
              placeholder="Enter custom prompt for Gemini..."
            />

            {/* Reset Button */}
            <button
              onClick={handleReset}
              disabled={isLoading}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Reset to Default Prompt
            </button>
          </>
        ) : (
          <>
            {/* Read-only Preview */}
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-700 whitespace-pre-line line-clamp-4">
                {prompt}
              </p>
            </div>
            <p className="text-xs text-gray-500">
              Using the default prompt optimized for Italian legal documents.
              Click "Customize Prompt" to modify.
            </p>
          </>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-red-800">
              <strong>Error:</strong> {error}
            </div>
          </div>
        </div>
      )}

      {/* Scan Button */}
      <button
        onClick={handleScan}
        disabled={isLoading}
        className={`
          w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold
          transition-all shadow-md
          ${isLoading
            ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
          }
        `}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Analyzing with Gemini AI...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            <span>Analyze with Gemini AI</span>
          </>
        )}
      </button>

      {/* Info Box */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <h4 className="text-sm font-semibold text-blue-900">How it works:</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>1. Gemini analyzes the PDF document with multimodal vision (text + layout)</li>
          <li>2. Identifies all PII entities with ~95%+ accuracy</li>
          <li>3. You can confirm or deny each found entity</li>
          <li>4. Confirmed entities will be saved to improve future local scans</li>
        </ul>
      </div>
    </div>
  )
}
