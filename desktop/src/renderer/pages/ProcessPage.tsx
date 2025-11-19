/**
 * Process Page - Document Review & PII Entity Management
 * Shows detected entities with accept/reject controls
 */
import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Check, X, Eye, EyeOff, Download, ArrowLeft } from 'lucide-react'

interface PIIEntity {
  entity_type: string
  text: string
  start: number
  end: number
  score: number
  accepted?: boolean
  _id?: string  // Unique identifier to fix toggle bug
}

export default function ProcessPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { file, result } = location.state || {}

  const [entities, setEntities] = useState<PIIEntity[]>([])
  const [selectedEntity, setSelectedEntity] = useState<number | null>(null)
  const [showRejected, setShowRejected] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [redactionStyle, setRedactionStyle] = useState<'placeholder' | 'solid_black'>('placeholder')

  // Manual selection state
  const [selectionMode, setSelectionMode] = useState(true) // Always enabled
  const [pendingSelection, setPendingSelection] = useState<{text: string, start: number, end: number} | null>(null)

  useEffect(() => {
    if (result?.entities) {
      // Initialize all entities as accepted by default with unique IDs
      const timestamp = Date.now()
      const initialEntities = result.entities.map((e: PIIEntity, idx: number) => ({
        ...e,
        accepted: true,
        _id: `${timestamp}-${idx}-${e.start}-${e.end}`  // Unique ID: timestamp + index + position
      }))

      console.log('🚀 ProcessPage: Initialized', initialEntities.length, 'entities with unique IDs')
      console.log('First 3 entities:', initialEntities.slice(0, 3).map(e => ({
        _id: e._id,
        text: e.text ? e.text.substring(0, 30) : '[No text]',
        type: e.entity_type,
        start: e.start,
        end: e.end
      })))

      setEntities(initialEntities)
    }
  }, [result])

  const handleAccept = (entityId: string) => {
    console.log('✅ Accept entity:', entityId)
    setEntities(prev => prev.map((e) =>
      e._id === entityId ? { ...e, accepted: true } : e
    ))
  }

  const handleReject = (entityId: string) => {
    console.log('❌ Reject entity:', entityId)
    setEntities(prev => prev.map((e) =>
      e._id === entityId ? { ...e, accepted: false } : e
    ))
  }

  const handleAcceptAll = () => {
    setEntities(prev => prev.map(e => ({ ...e, accepted: true })))
  }

  const handleRejectAll = () => {
    setEntities(prev => prev.map(e => ({ ...e, accepted: false })))
  }

  // Handle manual text selection
  const handleManualSelection = (text: string, start: number, end: number) => {
    // Check if already exists
    const exists = entities.find(e => e.start === start && e.end === end)
    if (exists) {
      alert('This text has already been selected')
      return
    }

    setPendingSelection({ text, start, end })
  }

  // Confirm and add manual selection
  const handleConfirmSelection = () => {
    if (!pendingSelection) return

    const manualEntity: PIIEntity = {
      entity_type: 'MANUAL',
      text: pendingSelection.text,
      start: pendingSelection.start,
      end: pendingSelection.end,
      score: 1.0,
      accepted: true,
      _id: `MANUAL-${pendingSelection.start}-${pendingSelection.end}-${Date.now()}`
    }

    setEntities(prev => [...prev, manualEntity])
    setPendingSelection(null)
    console.log('✅ Added manual selection:', manualEntity)
  }

  const handleExport = async () => {
    setProcessing(true)

    try {
      // Get accepted entities
      const acceptedEntities = entities.filter(e => e.accepted)

      console.log('📤 EXPORT DEBUG:')
      console.log(`   Total entities: ${entities.length}`)
      console.log(`   Accepted (to redact): ${acceptedEntities.length}`)
      console.log(`   Rejected (NOT to redact): ${entities.filter(e => !e.accepted).length}`)
      console.log('   Accepted entities:', acceptedEntities.map(e => ({
        text: e.text ? e.text.substring(0, 30) : '[No text]',
        type: e.entity_type,
        accepted: e.accepted
      })))

      // Call Python backend to generate redacted PDF
      const exportResult = await window.electron.processDocument({
        action: 'export_redacted',
        file_path: file.path,
        entities: acceptedEntities,
        redaction_style: redactionStyle
      })

      if (exportResult.status === 'success') {
        alert(`Redacted PDF saved to: ${exportResult.output_path}`)
        navigate('/')
      } else {
        alert(`Export failed: ${exportResult.error}`)
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('Unable to export document')
    } finally {
      setProcessing(false)
    }
  }

  // Entity statistics
  const stats = {
    total: entities.length,
    toRedact: entities.filter(e => e.accepted).length,  // "accepted" means "will be redacted"
    toKeep: entities.filter(e => !e.accepted).length,   // "rejected" means "keep as is"
    byType: entities.reduce((acc, e) => {
      acc[e.entity_type] = (acc[e.entity_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
  }

  // Filter entities for display
  const displayEntities = showRejected 
    ? entities 
    : entities.filter(e => e.accepted)

  if (!file || !result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No document loaded</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-gray-100 rounded"
              aria-label="Go back to home page"
              title="Back to home"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-semibold">{file.name}</h1>
              <p className="text-sm text-gray-600">
                Review detected personal data
              </p>
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-700">Redaction Style</label>
              <select
                value={redactionStyle}
                onChange={(e) => setRedactionStyle(e.target.value as 'placeholder' | 'solid_black')}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="placeholder">Labeled (Black text on yellow)</option>
                <option value="solid_black">Solid Black (Traditional)</option>
              </select>
            </div>
            <button
              onClick={() => navigate('/review', { state: { file, result, entities } })}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              aria-label="Open advanced PDF preview with interactive selection"
              title="Advanced PDF preview with selection"
            >
              <Eye className="w-5 h-5" aria-hidden="true" />
              Advanced PDF Preview
            </button>
            <button
              onClick={handleExport}
              disabled={processing || stats.toRedact === 0}
              className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label={`Export redacted PDF with ${stats.toRedact} redactions`}
              aria-disabled={processing || stats.toRedact === 0}
            >
              <Download className="w-5 h-5" aria-hidden="true" />
              {processing ? 'Processing...' : 'Export Redacted PDF'}
            </button>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Sidebar - Entity List */}
        <div className="w-96 bg-white border-r flex flex-col">
          {/* Stats */}
          <div className="p-4 border-b">
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
                <div className="text-xs text-gray-600">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats.toRedact}</div>
                <div className="text-xs text-red-700 font-medium">⚠️ Will Redact</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.toKeep}</div>
                <div className="text-xs text-green-700 font-medium">✓ Will Keep</div>
              </div>
            </div>

            {/* Bulk Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleAcceptAll}
                className="flex-1 px-3 py-2 text-sm border border-red-600 text-red-600 rounded hover:bg-red-50 font-medium"
                title="Mark all items for redaction"
              >
                ✗ Redact All
              </button>
              <button
                onClick={handleRejectAll}
                className="flex-1 px-3 py-2 text-sm border border-green-600 text-green-600 rounded hover:bg-green-50 font-medium"
                title="Keep all items visible"
              >
                ✓ Keep All
              </button>
              <button
                onClick={() => setShowRejected(!showRejected)}
                className="px-3 py-2 text-sm border rounded hover:bg-gray-50"
                aria-label={showRejected ? "Hide items that will be kept" : "Show all items including those that will be kept"}
                title={showRejected ? "Hide items to keep" : "Show all items"}
              >
                {showRejected ? <EyeOff className="w-4 h-4" aria-hidden="true" /> : <Eye className="w-4 h-4" aria-hidden="true" />}
              </button>
            </div>
          </div>

          {/* Entity List */}
          <div className="flex-1 overflow-y-auto">
            {Object.entries(stats.byType).map(([type, count]) => (
              <div key={type} className="border-b">
                <div className="px-4 py-2 bg-gray-50 font-medium text-sm">
                  {type.replace('_', ' ')} ({count})
                </div>
                {displayEntities
                  .filter(e => e.entity_type === type)
                  .map((entity) => (
                    <div
                      key={entity._id || `${entity.start}-${entity.end}`}
                      onClick={() => setSelectedEntity(entity.start)}
                      className={`
                        px-4 py-3 cursor-pointer border-l-4 hover:bg-gray-50
                        ${selectedEntity === entity.start ? 'bg-blue-50' : ''}
                        ${entity.accepted ? 'border-red-500 bg-red-50/30' : 'border-green-500 bg-green-50/30'}
                      `}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{entity.text}</div>
                          <div className="text-xs text-gray-600 mt-1">
                            Confidence: {(entity.score * 100).toFixed(0)}%
                            {entity.accepted && <span className="ml-2 text-red-600 font-semibold">⚠️ Will Redact</span>}
                            {!entity.accepted && <span className="ml-2 text-green-600 font-semibold">✓ Will Keep</span>}
                          </div>
                        </div>
                        <div className="flex gap-1 ml-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              if (entity._id) {
                                handleReject(entity._id)
                              } else {
                                console.error('Entity missing _id:', entity)
                              }
                            }}
                            className={`
                              p-1 rounded transition-colors
                              ${!entity.accepted ? 'bg-green-100 text-green-700 ring-2 ring-green-500' : 'hover:bg-gray-100 text-gray-400'}
                            `}
                            title="✓ Keep this item visible (don't redact)"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              if (entity._id) {
                                handleAccept(entity._id)
                              } else {
                                console.error('Entity missing _id:', entity)
                              }
                            }}
                            className={`
                              p-1 rounded transition-colors
                              ${entity.accepted ? 'bg-red-100 text-red-700 ring-2 ring-red-500' : 'hover:bg-gray-100 text-gray-400'}
                            `}
                            title="✗ Redact this item (remove from document)"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        </div>

        {/* Main - Document Viewer */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg">
            {/* Header with instructions */}
            <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
              <h2 className="text-2xl font-bold mb-2">Document Preview</h2>
              <p className="text-sm text-gray-700">
                💡 <strong>Select any text</strong> not highlighted that you want to redact
              </p>
            </div>

            {/* Selection confirmation toolbar */}
            {pendingSelection && (
              <div className="p-4 bg-gradient-to-r from-indigo-500 to-purple-600 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-white font-bold text-sm">
                      ✓ Text selected:
                    </span>
                    <span className="ml-3 bg-white px-3 py-1 rounded shadow text-gray-900 font-semibold">
                      {pendingSelection.text.substring(0, 60)}{pendingSelection.text.length > 60 ? '...' : ''}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleConfirmSelection}
                      className="px-6 py-2 bg-white text-indigo-700 rounded-lg hover:bg-indigo-50 font-bold shadow-lg"
                    >
                      ✓ Add to List
                    </button>
                    <button
                      onClick={() => setPendingSelection(null)}
                      className="px-4 py-2 bg-transparent text-white border-2 border-white rounded-lg hover:bg-white/20 font-medium"
                    >
                      ✗ Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Document text with highlights */}
            <div className="p-8 prose max-w-none">
              {result.full_text ? (
                <HighlightedText
                  text={result.full_text}
                  entities={entities}
                  selectedEntity={selectedEntity}
                  onManualSelection={handleManualSelection}
                />
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-500 mb-4">No text content available</p>
                  <p className="text-sm text-gray-400">
                    {typeof result === 'object' ? (
                      <>Debug: {Object.keys(result).length > 0 ? `Result has ${Object.keys(result).length} properties: ${Object.keys(result).join(', ')}` : 'Result is empty'}</>
                    ) : (
                      `Result type: ${typeof result}`
                    )}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Component to highlight PII entities in text
function HighlightedText({
  text,
  entities,
  selectedEntity,
  onManualSelection
}: {
  text: string
  entities: PIIEntity[]
  selectedEntity: number | null
  onManualSelection?: (text: string, start: number, end: number) => void
}) {
  const containerRef = React.useRef<HTMLDivElement>(null)

  // Handle text selection
  const handleMouseUp = () => {
    if (!onManualSelection || !containerRef.current) return

    const selection = window.getSelection()
    if (!selection || selection.toString().trim().length === 0) return

    const selectedText = selection.toString().trim()
    const range = selection.getRangeAt(0)

    // Calculate position in original text
    const preRange = document.createRange()
    preRange.setStart(containerRef.current, 0)
    preRange.setEnd(range.startContainer, range.startOffset)
    const textBefore = preRange.toString()

    const start = textBefore.length
    const end = start + selectedText.length

    console.log('📝 Text selected:', { selectedText, start, end })
    onManualSelection(selectedText, start, end)

    // Clear selection
    window.getSelection()?.removeAllRanges()
  }

  // Sort entities by start position
  const sortedEntities = [...entities].sort((a, b) => a.start - b.start)

  // Build highlighted text
  const parts: JSX.Element[] = []
  let lastIndex = 0

  sortedEntities.forEach((entity, idx) => {
    // Add text before entity
    if (entity.start > lastIndex) {
      parts.push(
        <span key={`text-${idx}`}>
          {text.substring(lastIndex, entity.start)}
        </span>
      )
    }

    // Add highlighted entity
    parts.push(
      <mark
        key={`entity-${idx}`}
        className={`
          px-1 rounded cursor-pointer transition-colors font-medium
          ${entity.accepted ? 'bg-red-200 text-red-900' : 'bg-green-200 text-green-900'}
          ${selectedEntity === idx ? 'ring-2 ring-blue-500' : ''}
          hover:ring-2 hover:ring-blue-300
        `}
        title={`${entity.entity_type} (${(entity.score * 100).toFixed(0)}%) - ${entity.accepted ? '⚠️ Will be REDACTED' : '✓ Will be KEPT'}`}
      >
        {entity.text}
      </mark>
    )

    lastIndex = entity.end
  })

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <span key="text-end">
        {text.substring(lastIndex)}
      </span>
    )
  }

  return (
    <div
      ref={containerRef}
      className="whitespace-pre-wrap select-text cursor-text"
      onMouseUp={handleMouseUp}
      style={{ userSelect: 'text' }}
    >
      {parts}
    </div>
  )
}
