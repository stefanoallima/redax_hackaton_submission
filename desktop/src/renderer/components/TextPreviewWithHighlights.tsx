/**
 * Text Preview with PII Highlights
 * Shows extracted text with highlighted PII entities
 * Click to toggle accept/reject for each entity
 */
import React, { useMemo } from 'react'
import { AlertCircle, MousePointer2, Check, X } from 'lucide-react'

interface Entity {
  entity_type: string
  text: string
  start: number
  end: number
  score: number
  accepted: boolean
  manual?: boolean
  _id?: string
  locations?: Array<{
    page: number
    rect: {
      x0: number
      y0: number
      x1: number
      y1: number
    }
  }>
}

interface TextPreviewProps {
  fullText: string
  entities: Entity[]
  onEntityToggle: (entityId: string) => void
  onManualSelection?: (text: string, start: number, end: number) => void
}

// Entity type color mapping (same as PDF viewer for consistency)
const ENTITY_COLORS: Record<string, { bg: string, border: string, text: string }> = {
  'PERSON': { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-900' },
  'CODICE_FISCALE': { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-900' },
  'PHONE_NUMBER': { bg: 'bg-blue-100', border: 'border-blue-500', text: 'text-blue-900' },
  'EMAIL_ADDRESS': { bg: 'bg-purple-100', border: 'border-purple-500', text: 'text-purple-900' },
  'IBAN': { bg: 'bg-amber-100', border: 'border-amber-500', text: 'text-amber-900' },
  'IT_ADDRESS': { bg: 'bg-pink-100', border: 'border-pink-500', text: 'text-pink-900' },
  'DATE_TIME': { bg: 'bg-cyan-100', border: 'border-cyan-500', text: 'text-cyan-900' },
  'LOCATION': { bg: 'bg-teal-100', border: 'border-teal-500', text: 'text-teal-900' },
  'MANUAL': { bg: 'bg-indigo-100', border: 'border-indigo-500', text: 'text-indigo-900' }
}

const DEFAULT_COLORS = { bg: 'bg-gray-100', border: 'border-gray-500', text: 'text-gray-900' }

// Get entity color
const getEntityColors = (entityType: string) => {
  return ENTITY_COLORS[entityType] || DEFAULT_COLORS
}

export default function TextPreviewWithHighlights({
  fullText,
  entities,
  onEntityToggle,
  onManualSelection
}: TextPreviewProps) {
  // Force re-render when entities change by using a render key
  const [renderKey, setRenderKey] = React.useState(0)
  const [selectionMode, setSelectionMode] = React.useState(true) // ALWAYS ON by default
  const [selectedText, setSelectedText] = React.useState('')
  const [selectedRange, setSelectedRange] = React.useState<{start: number, end: number} | null>(null)
  const textContentRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    setRenderKey(prev => prev + 1)
  }, [entities])

  // Build highlighted text segments
  const textSegments = useMemo(() => {
    if (!fullText || entities.length === 0) {
      return [{ text: fullText || 'No text content available', isEntity: false }]
    }

    // Sort entities by start position (keep original entity objects with _id)
    const sortedEntities = [...entities].sort((a, b) => a.start - b.start)

    const segments: Array<{
      text: string
      isEntity: boolean
      entity?: Entity
    }> = []

    let currentPos = 0

    sortedEntities.forEach((entity) => {
      // Add text before entity
      if (currentPos < entity.start) {
        segments.push({
          text: fullText.substring(currentPos, entity.start),
          isEntity: false
        })
      }

      // Add entity segment
      segments.push({
        text: fullText.substring(entity.start, entity.end),
        isEntity: true,
        entity
      })

      currentPos = entity.end
    })

    // Add remaining text
    if (currentPos < fullText.length) {
      segments.push({
        text: fullText.substring(currentPos),
        isEntity: false
      })
    }

    return segments
  }, [fullText, entities])

  const acceptedCount = entities.filter(e => e.accepted).length
  const rejectedCount = entities.length - acceptedCount

  // Handle text selection
  const handleTextSelection = () => {
    if (!selectionMode || !textContentRef.current) return

    const selection = window.getSelection()
    if (!selection || selection.toString().trim().length === 0) return

    const range = selection.getRangeAt(0)
    const selectedText = selection.toString().trim()

    // Calculate absolute position in fullText
    // This is tricky because we need to account for React elements
    const textContent = textContentRef.current.innerText
    const beforeSelection = range.toString()

    // Find the start position by getting text before selection
    const preRange = document.createRange()
    preRange.setStart(textContentRef.current, 0)
    preRange.setEnd(range.startContainer, range.startOffset)
    const textBefore = preRange.toString()

    const start = textBefore.length
    const end = start + selectedText.length

    console.log('📝 Text selected:', { selectedText, start, end })
    setSelectedText(selectedText)
    setSelectedRange({ start, end })
  }

  // Add selected text as manual entity
  const handleAddSelection = () => {
    if (!selectedRange || !selectedText || !onManualSelection) return

    onManualSelection(selectedText, selectedRange.start, selectedRange.end)

    // Clear selection
    setSelectedText('')
    setSelectedRange(null)
    setSelectionMode(false)
    window.getSelection()?.removeAllRanges()
  }

  // Cancel selection
  const handleCancelSelection = () => {
    setSelectedText('')
    setSelectedRange(null)
    setSelectionMode(false)
    window.getSelection()?.removeAllRanges()
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b shadow-sm">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold">Document Text Preview</h3>
            <p className="text-xs text-gray-600">
              💡 Click highlighted text to toggle • Drag to select unmarked text to redact
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-4 h-4 bg-green-100 border-2 border-green-500 rounded"></div>
            <span className="text-gray-700">
              Accepted: <strong>{acceptedCount}</strong>
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-4 h-4 bg-red-100 border-2 border-red-500 rounded"></div>
            <span className="text-gray-700">
              Rejected: <strong>{rejectedCount}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Selection Toolbar (shown when text is selected) */}
      {selectionMode && selectedText && (
        <div className="px-4 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 border-b shadow-lg">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-white">
                ✓ Text Selected:
              </span>
              <span className="font-mono bg-white px-3 py-1.5 rounded shadow text-gray-900 font-semibold max-w-md truncate">
                {selectedText}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleAddSelection}
                className="flex items-center gap-2 px-6 py-2.5 bg-white text-indigo-700 rounded-lg hover:bg-indigo-50 text-sm font-bold shadow-lg transition-all transform hover:scale-105"
              >
                <Check className="w-5 h-5" />
                Add to Redaction List
              </button>
              <button
                onClick={handleCancelSelection}
                className="flex items-center gap-2 px-4 py-2.5 bg-transparent text-white rounded-lg hover:bg-white/20 text-sm font-medium border-2 border-white"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Text Content with Highlights */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm p-8">
          <div
            ref={textContentRef}
            onMouseUp={handleTextSelection}
            className={`text-base leading-relaxed font-mono whitespace-pre-wrap ${selectionMode ? 'select-text cursor-text' : ''}`}
          >
            {textSegments.map((segment, index) => {
              if (!segment.isEntity || !segment.entity) {
                return <span key={`text-${renderKey}-${index}`}>{segment.text}</span>
              }

              const colors = getEntityColors(segment.entity.entity_type)
              const isAccepted = segment.entity.accepted

              return (
                <span
                  key={`${renderKey}-${segment.entity.start}-${segment.entity.end}-${segment.entity.text}`}
                  data-entity-start={segment.entity.start}
                  data-entity-end={segment.entity.end}
                  data-entity-text={segment.entity.text}
                  onClick={() => {
                    const clickedEntity = segment.entity
                    console.log('👆 CLICKED ENTITY:', clickedEntity)
                    console.log('   Has _id?', !!clickedEntity?._id)

                    if (clickedEntity) {
                      if (clickedEntity._id) {
                        console.log('✅ Entity has _id, calling onEntityToggle')
                        onEntityToggle(clickedEntity._id)
                      } else {
                        console.error('❌ Entity missing _id field! Entity:', clickedEntity)
                        console.error('   This means the document was loaded BEFORE the fix was applied.')
                        console.error('   Please go back and reload the document!')
                      }
                    } else {
                      console.error('❌ No entity in segment!')
                    }
                  }}
                  className={`
                    inline-block px-1 py-0.5 rounded cursor-pointer transition-all
                    border-2
                    ${isAccepted
                      ? `${colors.bg} ${colors.border} ${colors.text}`
                      : 'bg-red-100 border-red-500 text-red-900 line-through'
                    }
                    hover:opacity-75 hover:shadow-md
                  `}
                  title={`${segment.entity.entity_type}: "${segment.entity.text}" (${Math.round(segment.entity.score * 100)}%)\nPosition: ${segment.entity.start}-${segment.entity.end}\nClick to ${isAccepted ? 'reject' : 'accept'}`}
                >
                  {segment.text}
                </span>
              )
            })}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-4 py-3 bg-indigo-50 border-t border-indigo-200">
        <div className="text-sm text-indigo-900 text-center font-medium">
          <MousePointer2 className="w-4 h-4 inline mr-2" />
          <strong>HOW TO USE:</strong> Click on <span className="bg-green-200 px-1 rounded">colored text</span> to toggle •
          <strong> Drag to select</strong> any unmarked text you want to redact
        </div>
      </div>
    </div>
  )
}
