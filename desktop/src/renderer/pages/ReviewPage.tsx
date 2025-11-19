/**
 * Review Page - Improved UX with Auto-Accept and Quick Summary
 * Shows PII summary with entity type checkboxes + manual additions
 * Includes PDF preview with interactive redaction overlays
 */
import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Download, ArrowLeft, AlertCircle, CheckCircle, Plus, X, FileText, File, Settings, CheckCircle2, XCircle, Database } from 'lucide-react'
import PDFViewerWithAnnotations from '../components/PDFViewerWithAnnotations'
import TextPreviewWithHighlights from '../components/TextPreviewWithHighlights'
import CustomPatternsSettings from '../components/CustomPatternsSettings'
import EntityLearningDialog from '../components/EntityLearningDialog'
import LearnedEntitiesViewer from '../components/LearnedEntitiesViewer'

interface PIIEntity {
  entity_type: string
  text: string
  start: number
  end: number
  score: number
  accepted: boolean  // Changed from optional to required after initialization
  manual?: boolean  // User-added custom redaction
  _id?: string  // Unique identifier for this entity instance
  locations?: Array<{  // PDF page coordinates (from Python backend)
    page: number
    rect: {
      x0: number
      y0: number
      x1: number
      y1: number
    }
  }>
}

interface GroupedPII {
  text: string  // Canonical text (first occurrence)
  variations: string[]  // All text variations (e.g., "mario rossi", "Mario Rossi", "MARIO ROSSI")
  entity_type: string
  count: number  // Number of occurrences
  avgScore: number
  accepted: boolean
  manual: boolean
  entityIndices: number[]  // Indices of all entities with this text
  learningStatus?: 'always' | 'flag' | 'neutral' | 'never'  // Learning classification
}

interface EntityTypeConfig {
  type: string
  label: string
  description: string
  icon: string
  enabled: boolean
  color: string
}

// Helper function to group entities by unique text value
const groupEntitiesByText = (entities: PIIEntity[], caseInsensitive: boolean = true): GroupedPII[] => {
  const groups = new Map<string, GroupedPII>()

  entities.forEach((entity, index) => {
    // Create a key combining text and type to group identical values
    // Use lowercase for case-insensitive grouping, original text otherwise
    const normalizedText = caseInsensitive ? entity.text.toLowerCase() : entity.text
    const key = `${normalizedText}||${entity.entity_type}`

    if (groups.has(key)) {
      const group = groups.get(key)!
      group.count++
      group.avgScore = (group.avgScore * (group.count - 1) + entity.score) / group.count
      group.entityIndices.push(index)
      // If any instance is accepted, the group is accepted
      group.accepted = group.accepted || (entity.accepted ?? true)
      // Track text variations
      if (!group.variations.includes(entity.text)) {
        group.variations.push(entity.text)
      }
    } else {
      groups.set(key, {
        text: entity.text,  // Use first occurrence as canonical
        variations: [entity.text],
        entity_type: entity.entity_type,
        count: 1,
        avgScore: entity.score,
        accepted: entity.accepted ?? true,
        manual: entity.manual ?? false,
        entityIndices: [index]
      })
    }
  })

  return Array.from(groups.values())
}

// Default entity types configuration
const DEFAULT_ENTITY_TYPES: EntityTypeConfig[] = [
  {
    type: 'PERSON',
    label: 'Person Names',
    description: 'Full names, first names, last names',
    icon: '👤',
    enabled: true,
    color: 'blue'
  },
  {
    type: 'CODICE_FISCALE',
    label: 'Codice Fiscale',
    description: 'Italian tax identification numbers',
    icon: '🆔',
    enabled: true,
    color: 'red'
  },
  {
    type: 'PHONE_NUMBER',
    label: 'Phone Numbers',
    description: 'Mobile and landline numbers',
    icon: '📱',
    enabled: true,
    color: 'green'
  },
  {
    type: 'EMAIL_ADDRESS',
    label: 'Email Addresses',
    description: 'Email contacts',
    icon: '📧',
    enabled: true,
    color: 'purple'
  },
  {
    type: 'IBAN',
    label: 'Bank Accounts (IBAN)',
    description: 'Italian bank account numbers',
    icon: '🏦',
    enabled: true,
    color: 'yellow'
  },
  {
    type: 'IT_ADDRESS',
    label: 'Physical Addresses',
    description: 'Street addresses, cities, postal codes',
    icon: '📍',
    enabled: false,  // Disabled by default (user can enable)
    color: 'orange'
  },
  {
    type: 'DATE_TIME',
    label: 'Dates',
    description: 'Birth dates, contract dates',
    icon: '📅',
    enabled: false,  // Often needed in legal docs
    color: 'pink'
  },
  {
    type: 'LOCATION',
    label: 'Locations',
    description: 'Cities, regions, countries',
    icon: '🗺️',
    enabled: false,
    color: 'teal'
  }
]

export default function ReviewPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { file, result, entities: passedEntities } = location.state || {}
  
  const [entities, setEntities] = useState<PIIEntity[]>([])
  const [groupedEntities, setGroupedEntities] = useState<GroupedPII[]>([])
  const [entityTypes, setEntityTypes] = useState<EntityTypeConfig[]>(DEFAULT_ENTITY_TYPES)
  const [manualText, setManualText] = useState('')
  const [processing, setProcessing] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.80) // P1: Confidence threshold
  const [exportAsTxt, setExportAsTxt] = useState(false) // Export as TXT for LLM use
  const [previewMode, setPreviewMode] = useState(false) // Preview redactions mode
  const [showTextPreview, setShowTextPreview] = useState(true) // Show text preview by default instead of PDF
  const [caseInsensitiveGrouping, setCaseInsensitiveGrouping] = useState(true) // Group case variations together
  const [showSettings, setShowSettings] = useState(false) // Custom patterns settings modal
  const [showLearnedEntities, setShowLearnedEntities] = useState(false) // Learned entities viewer modal
  const [learningDialog, setLearningDialog] = useState<{show: boolean, text: string, type: string, current?: 'always' | 'flag' | 'neutral' | 'never'} | null>(null)

  useEffect(() => {
    // Use passed entities from ProcessPage if available, otherwise initialize from result
    if (passedEntities && passedEntities.length > 0) {
      // Entities already have IDs and accept/reject status from ProcessPage
      console.log('✅ Using entities from ProcessPage:', passedEntities.length)
      setEntities(passedEntities)
      setGroupedEntities(groupEntitiesByText(passedEntities, caseInsensitiveGrouping))
    } else if (result?.entities) {
      // Initialize all detected entities as ACCEPTED by default
      // Add unique IDs for reliable mapping between grouped/filtered/full arrays
      // Use timestamp + random to ensure truly unique IDs
      const timestamp = Date.now()
      const initialEntities = result.entities.map((e: PIIEntity, idx: number) => ({
        ...e,
        accepted: true,  // Auto-accept all
        manual: false,
        _id: `${timestamp}-${idx}-${e.start}-${e.end}`  // Truly unique ID: timestamp + index + position
      }))

      console.log('═══════════════════════════════════════════════════')
      console.log('🚀 ENTITIES INITIALIZED WITH UNIQUE IDs')
      console.log('═══════════════════════════════════════════════════')
      console.log('Total entities:', initialEntities.length)
      console.log('First 5 entities with IDs:')
      initialEntities.slice(0, 5).forEach((e: PIIEntity, i: number) => {
        console.log(`  [${i}]`, {
          _id: e._id,
          text: e.text.substring(0, 30) + '...',
          type: e.entity_type,
          start: e.start,
          end: e.end
        })
      })
      console.log('═══════════════════════════════════════════════════')

      // Check for duplicate IDs
      const idSet = new Set(initialEntities.map((e: PIIEntity) => e._id))
      if (idSet.size !== initialEntities.length) {
        console.error('⚠️ DUPLICATE IDs DETECTED!')
      } else {
        console.log('✅ All IDs are unique')
      }

      setEntities(initialEntities)
      setGroupedEntities(groupEntitiesByText(initialEntities, caseInsensitiveGrouping))
    }
  }, [result, passedEntities, caseInsensitiveGrouping])

  // Re-group entities whenever they change or grouping mode changes
  useEffect(() => {
    if (entities.length > 0) {
      setGroupedEntities(groupEntitiesByText(entities, caseInsensitiveGrouping))
    }
  }, [entities, caseInsensitiveGrouping])

  // Toggle entity type on/off
  const toggleEntityType = (type: string) => {
    setEntityTypes(prev => prev.map(et => 
      et.type === type ? { ...et, enabled: !et.enabled } : et
    ))
    
    // Update all entities of this type
    setEntities(prev => prev.map(e => 
      e.entity_type === type && !e.manual 
        ? { ...e, accepted: !e.accepted } 
        : e
    ))
  }

  // Add manual redactions
  const handleAddManual = () => {
    if (!manualText.trim()) return

    // Split by lines
    const lines = manualText.split('\n').filter(l => l.trim())

    // Add each as a manual entity with unique ID
    const manualEntities: PIIEntity[] = lines.map((text) => ({
      entity_type: 'MANUAL',
      text: text.trim(),
      start: -1,  // Not from detection
      end: -1,
      score: 1.0,  // User-defined, 100% confidence
      accepted: true,
      manual: true,
      _id: `MANUAL--1--1-${text.trim().substring(0, 20)}-${Date.now()}`  // Unique ID using text + timestamp
    }))

    setEntities(prev => [...prev, ...manualEntities])
    setManualText('')  // Clear input
  }

  // Remove manual entity
  const removeManualEntity = (index: number) => {
    setEntities(prev => prev.filter((_, i) => i !== index))
  }

  // Handle manual selection from text preview
  const handleManualSelection = (text: string, start: number, end: number) => {
    // Check if this exact position is already an entity
    const existingEntity = entities.find(e => e.start === start && e.end === end)
    if (existingEntity) {
      alert('This text is already marked for redaction')
      return
    }

    // Create manual entity with position information
    const manualEntity: PIIEntity = {
      entity_type: 'MANUAL',
      text: text.trim(),
      start: start,
      end: end,
      score: 1.0,
      accepted: true,
      manual: true,
      _id: `MANUAL-${start}-${end}-${Date.now()}`
    }

    setEntities(prev => [...prev, manualEntity])
    console.log('✅ Added manual selection:', manualEntity)
  }

  // Handle manual selection from PDF viewer (coordinates-based)
  const handlePDFManualSelection = (text: string, page: number, bbox: {x0: number, y0: number, x1: number, y1: number}) => {
    // Create manual entity with PDF location information
    const manualEntity: PIIEntity = {
      entity_type: 'MANUAL',
      text: text,
      start: -1,  // Not from text extraction
      end: -1,
      score: 1.0,
      accepted: true,
      manual: true,
      _id: `MANUAL-PDF-${page}-${bbox.x0}-${bbox.y0}-${Date.now()}`,
      locations: [{
        page: page,
        rect: bbox
      }]
    }

    setEntities(prev => [...prev, manualEntity])
    console.log('✅ Added manual PDF selection:', manualEntity)
    alert(`✓ Manual redaction area added!\n\nThe selected area will be redacted in the final PDF.`)
  }

  // Toggle grouped entity (affects all instances with same text)
  const toggleGroupedEntity = (group: GroupedPII) => {
    const newAcceptedState = !group.accepted
    setEntities(prev => prev.map((e, i) =>
      group.entityIndices.includes(i) ? { ...e, accepted: newAcceptedState } : e
    ))
  }

  // Handle learning classification
  const handleLearningClassification = (text: string, entityType: string, classification: 'always' | 'flag' | 'neutral' | 'never') => {
    // Get custom config from localStorage
    const configStr = localStorage.getItem('custom_recognizer_config')
    const config = configStr ? JSON.parse(configStr) : { patterns: [], allow_lists: [], deny_lists: {} }

    // STEP 1: Remove from previous classification (if editing)
    // Remove from allow-lists
    config.allow_lists = config.allow_lists.map((al: any) => {
      if (al.entity_type === entityType) {
        return {
          ...al,
          terms: al.terms.filter((t: string) => t.toLowerCase() !== text.toLowerCase())
        }
      }
      return al
    }).filter((al: any) => al.terms.length > 0) // Remove empty lists

    // Remove from deny-lists
    if (config.deny_lists[entityType]) {
      config.deny_lists[entityType] = config.deny_lists[entityType].filter(
        (t: string) => t.toLowerCase() !== text.toLowerCase()
      )
      if (config.deny_lists[entityType].length === 0) {
        delete config.deny_lists[entityType]
      }
    }

    // STEP 2: Add to new classification
    if (classification === 'always') {
      // Add to allow-list (always redact)
      const existingList = config.allow_lists.find((al: any) => al.entity_type === entityType)
      if (existingList) {
        if (!existingList.terms.includes(text)) {
          existingList.terms.push(text)
        }
        existingList.flag_for_review = false // Ensure not flagged
      } else {
        config.allow_lists.push({
          entity_type: entityType,
          enabled: true,
          terms: [text],
          case_sensitive: false,
          flag_for_review: false
        })
      }
      console.log(`✓✓ Added "${text}" to ALWAYS REDACT (allow-list)`)
    } else if (classification === 'flag') {
      // Add to allow-list but flag for review (context-dependent)
      const existingList = config.allow_lists.find((al: any) => al.entity_type === entityType && al.flag_for_review === true)
      if (existingList) {
        if (!existingList.terms.includes(text)) {
          existingList.terms.push(text)
        }
      } else {
        config.allow_lists.push({
          entity_type: entityType,
          enabled: true,
          terms: [text],
          case_sensitive: false,
          flag_for_review: true
        })
      }
      console.log(`⚠ Added "${text}" to FLAG FOR REVIEW (allow-list with flag)`)
    } else if (classification === 'never') {
      // Add to deny-list
      if (!config.deny_lists[entityType]) {
        config.deny_lists[entityType] = []
      }
      if (!config.deny_lists[entityType].includes(text)) {
        config.deny_lists[entityType].push(text)
      }
      console.log(`✗✗ Added "${text}" to NEVER REDACT (deny-list)`)
    } else {
      // 'neutral' - removed from both lists above, no action needed
      console.log(`○ "${text}" set to NEUTRAL (no learning)`)
    }

    // STEP 3: Save updated config
    localStorage.setItem('custom_recognizer_config', JSON.stringify(config))

    // STEP 4: Update entity learning status in grouped entities
    setGroupedEntities(prev => prev.map(g =>
      g.text.toLowerCase() === text.toLowerCase() && g.entity_type === entityType
        ? { ...g, learningStatus: classification }
        : g
    ))

    // Close dialog
    setLearningDialog(null)

    // Show confirmation
    const messages = {
      always: '✓✓ This term will ALWAYS be redacted in future documents',
      flag: '⚠ This term will be FLAGGED for review (always detected, manual decision)',
      neutral: '○ Classification removed - standard AI detection',
      never: '✗✗ This term will NEVER be redacted in future documents'
    }
    alert(messages[classification])
  }

  // Toggle individual entity accept/reject (for preview clicks)
  // Uses unique _id field for guaranteed correct matching
  const handleEntityToggle = (entityId: string) => {
    console.log('🔄 Toggle clicked for entity ID:', entityId)

    setEntities(prev => {
      const matchingEntity = prev.find(e => e._id === entityId)

      if (matchingEntity) {
        console.log('   ✅ Found matching entity:', {
          _id: matchingEntity._id,
          text: matchingEntity.text,
          type: matchingEntity.entity_type,
          current_accepted: matchingEntity.accepted,
          will_toggle_to: !matchingEntity.accepted
        })
      } else {
        console.log('   ❌ NO MATCHING ENTITY FOUND for ID:', entityId)
        console.log('   Available IDs:', prev.slice(0, 5).map(e => e._id))
      }

      return prev.map((e) =>
        e._id === entityId
          ? { ...e, accepted: !e.accepted }
          : e
      )
    })
  }

  // Export redacted PDF
  const handleExport = async () => {
    setProcessing(true)
    
    try {
      // Get accepted entities (respecting entity type toggles)
      const acceptedEntities = entities.filter(e => {
        if (e.manual) return e.accepted  // Manual always use their own state
        
        const typeConfig = entityTypes.find(et => et.type === e.entity_type)
        return typeConfig?.enabled && e.accepted
      })
      
      if (acceptedEntities.length === 0) {
        alert('No entities selected for redaction')
        setProcessing(false)
        return
      }
      
      // Call Python backend to generate redacted document
      const exportResult = await window.electron.processDocument({
        action: 'export_redacted',
        file_path: file.path,
        entities: acceptedEntities,
        export_txt: exportAsTxt
      })

      if (exportResult.status === 'success' && 'output_path' in exportResult) {
        let message = `✅ Redacted PDF saved to:\n${exportResult.output_path}\n\n📊 Mapping table: ${exportResult.mapping_table_path}`

        if (exportResult.txt_output_path) {
          message += `\n\n📄 TXT for LLM: ${exportResult.txt_output_path}`
        }

        alert(message)
        navigate('/')
      } else {
        alert(`❌ Export failed: ${exportResult.error}`)
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('Failed to export document')
    } finally {
      setProcessing(false)
    }
  }

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

  // Calculate statistics
  const stats = {
    total: entities.length,
    byType: entities.reduce((acc, e) => {
      acc[e.entity_type] = (acc[e.entity_type] || 0) + 1
      return acc
    }, {} as Record<string, number>),
    avgScore: entities.length > 0 
      ? (entities.reduce((sum, e) => sum + e.score, 0) / entities.length) 
      : 0
  }

  // Filter entities based on type config AND confidence threshold
  const visibleEntities = entities.filter(e => {
    if (e.manual) return true  // Always show manual additions
    return e.score >= confidenceThreshold  // Filter by confidence
  })

  // Debug: Log visibleEntities to check state
  useEffect(() => {
    console.log('📊 visibleEntities updated:', visibleEntities.length, 'entities')
    console.log('First 5 visible entities:', visibleEntities.slice(0, 5).map(e => ({
      text: e.text,
      type: e.entity_type,
      start: e.start,
      end: e.end,
      accepted: e.accepted
    })))
  }, [visibleEntities])

  // Debug: Log full entities array
  useEffect(() => {
    if (entities.length > 0) {
      console.log('🗂️ Full entities array:', entities.length, 'total')
      console.log('First 5 full entities:', entities.slice(0, 5).map(e => ({
        text: e.text,
        type: e.entity_type,
        start: e.start,
        end: e.end,
        accepted: e.accepted
      })))
    }
  }, [entities])
  
  const hiddenByConfidence = entities.filter(e => 
    !e.manual && e.score < confidenceThreshold
  ).length
  
  const activeEntities = visibleEntities.filter(e => {
    if (e.manual) return e.accepted
    const typeConfig = entityTypes.find(et => et.type === e.entity_type)
    return typeConfig?.enabled && e.accepted
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-gray-100 rounded"
              data-testid="home-button"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-semibold">{file.name}</h1>
              <p className="text-sm text-gray-600">
                {stats.total} PII entities detected • {activeEntities.length} will be redacted
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowLearnedEntities(true)}
              className="flex items-center gap-2 px-4 py-2 text-purple-700 bg-purple-100 rounded-lg hover:bg-purple-200 transition-colors"
              title="View all learned entities"
            >
              <Database className="w-4 h-4" />
              <span className="text-sm font-medium">Learned Entities</span>
            </button>
            <button
              onClick={() => setShowSettings(true)}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              title="Configure custom detection rules"
            >
              <Settings className="w-4 h-4" />
              <span className="text-sm font-medium">Custom Rules</span>
            </button>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={exportAsTxt}
                onChange={(e) => setExportAsTxt(e.target.checked)}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span>Also export as TXT (for LLMs)</span>
            </label>
            <button
              onClick={handleExport}
              disabled={processing || activeEntities.length === 0}
              className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-5 h-5" />
              {processing ? 'Exporting...' : 'Export Redacted PDF'}
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-col h-[calc(100vh-5rem)]">
        {/* Document Preview - Toggle between Text and PDF view */}
        <div className="flex-1 bg-white border-b">
          {/* Preview Toggle Buttons */}
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 border-b">
            <button
              onClick={() => setShowTextPreview(true)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
                ${showTextPreview
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              <FileText className="w-4 h-4" />
              <span>Text Preview</span>
            </button>
            {result.file_type === 'pdf' && result.file_path && (
              <button
                onClick={() => setShowTextPreview(false)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
                  ${!showTextPreview
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <File className="w-4 h-4" />
                <span>PDF Preview</span>
              </button>
            )}
          </div>

          {/* Text Preview */}
          {showTextPreview && result.full_text && (
            <TextPreviewWithHighlights
              fullText={result.full_text}
              entities={visibleEntities}
              onEntityToggle={handleEntityToggle}
              onManualSelection={handleManualSelection}
            />
          )}

          {/* PDF Preview (for PDF files only) */}
          {!showTextPreview && result.file_type === 'pdf' && result.file_path && (
            <PDFViewerWithAnnotations
              filePath={result.file_path}
              entities={visibleEntities}
              onEntityToggle={handleEntityToggle}
              previewMode={previewMode}
              onPreviewModeChange={setPreviewMode}
              onManualSelection={handlePDFManualSelection}
            />
          )}
        </div>

        {/* Configuration Panel (Scrollable) */}
        <div className="flex-shrink-0 max-h-[40vh] overflow-y-auto bg-gray-50">
          <div className="max-w-6xl mx-auto p-6">
            {/* Quick Summary Card */}
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <h2 className="text-xl font-semibold">PII Detection Complete</h2>
            </div>
            
            {/* Settings: Confidence & Case Grouping */}
            <div className="flex items-center gap-6">
              {/* Case-Insensitive Grouping Toggle */}
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={caseInsensitiveGrouping}
                  onChange={(e) => setCaseInsensitiveGrouping(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <span className="text-gray-700 font-medium">
                  Group case variations
                  <span className="text-xs text-gray-500 ml-1">(e.g., "Mario" = "MARIO")</span>
                </span>
              </label>

              {/* P1: Confidence Threshold Slider */}
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-gray-700">
                  Confidence: {(confidenceThreshold * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={confidenceThreshold * 100}
                  onChange={(e) => setConfidenceThreshold(parseInt(e.target.value) / 100)}
                  className="w-32 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                {hiddenByConfidence > 0 && (
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {hiddenByConfidence} hidden
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600" data-testid="total-entities">{stats.total}</div>
              <div className="text-sm text-gray-600">Total Entities</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">{activeEntities.length}</div>
              <div className="text-sm text-gray-600">To Be Redacted</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">
                {(stats.avgScore * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-600">Avg. Confidence</div>
            </div>
          </div>

          <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800">
              <strong>All entities are auto-accepted for redaction.</strong> Review the categories below and untick any you don't want to redact. You can also add custom text to redact manually.
            </div>
          </div>
        </div>

        {/* Entity Type Selection */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Select Entity Types to Redact</h3>
          
          <div className="grid grid-cols-2 gap-3">
            {entityTypes.map(et => {
              const count = visibleEntities.filter(e => e.entity_type === et.type).length
              const totalCount = stats.byType[et.type] || 0
              const hiddenCount = totalCount - count
              return (
                <label
                  key={et.type}
                  className={`
                    flex items-start gap-3 p-4 border-2 rounded-lg cursor-pointer transition-all
                    ${et.enabled 
                      ? 'border-primary-500 bg-primary-50' 
                      : 'border-gray-200 bg-gray-50 opacity-60'
                    }
                  `}
                >
                  <input
                    type="checkbox"
                    checked={et.enabled}
                    onChange={() => toggleEntityType(et.type)}
                    className="mt-1 w-5 h-5 text-primary-600 rounded"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{et.icon}</span>
                      <span className="font-medium">{et.label}</span>
                      {count > 0 && (
                        <>
                          <span className={`
                            px-2 py-0.5 text-xs rounded-full
                            ${et.enabled ? 'bg-primary-600 text-white' : 'bg-gray-300 text-gray-600'}
                          `}>
                            {count} found
                          </span>
                          {hiddenCount > 0 && (
                            <span className="text-xs text-gray-400">
                              +{hiddenCount} hidden
                            </span>
                          )}
                        </>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{et.description}</p>
                  </div>
                </label>
              )
            })}
          </div>
        </div>

        {/* Manual Additions */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Manual Redactions</h3>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              {showAdvanced ? 'Hide' : 'Show'} Advanced Options
            </button>
          </div>

          {showAdvanced && (
            <>
              <p className="text-sm text-gray-600 mb-3">
                Add specific text strings to redact (one per line). Examples: contract amounts, specific addresses, company names.
              </p>
              
              <div className="flex gap-2 mb-4">
                <textarea
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  placeholder="Enter text to redact (one per line)&#10;Example:&#10;€50,000&#10;Via Milano 45&#10;ABC Legal Services"
                  className="flex-1 px-3 py-2 border rounded-lg resize-none"
                  rows={4}
                />
                <button
                  onClick={handleAddManual}
                  disabled={!manualText.trim()}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 h-fit"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>

              {/* Manual Entities List */}
              {entities.filter(e => e.manual).length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700">Custom Redactions ({entities.filter(e => e.manual).length}):</h4>
                  {entities.map((entity, idx) => entity.manual && (
                    <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded border">
                      <span className="flex-1 text-sm font-mono">{entity.text}</span>
                      <button
                        onClick={() => removeManualEntity(idx)}
                        className="p-1 hover:bg-red-100 rounded text-red-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Detailed Entity List (Collapsible) - Now shows UNIQUE values */}
        <details className="bg-white rounded-lg shadow-lg">
          <summary className="px-6 py-4 cursor-pointer font-semibold hover:bg-gray-50">
            📋 View Unique PII Values ({groupedEntities.length} unique, {stats.total} total occurrences)
          </summary>
          <div className="px-6 pb-6 max-h-96 overflow-y-auto">
            {Object.entries(stats.byType).map(([type, count]) => {
              const typeGroups = groupedEntities.filter(g => g.entity_type === type)
              if (typeGroups.length === 0) return null

              return (
                <div key={type} className="mb-4">
                  <h4 className="font-medium text-gray-700 mb-2">
                    {entityTypes.find(et => et.type === type)?.label || type} ({typeGroups.length} unique values)
                  </h4>
                  <div className="space-y-1">
                    {/* Accepted entities first */}
                    {typeGroups.filter(g => g.accepted).map((group, idx) => (
                      <div key={idx} className="flex flex-col gap-1 text-sm p-2 bg-gray-50 rounded hover:bg-gray-100">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={group.accepted}
                            onChange={() => toggleGroupedEntity(group)}
                            className="w-4 h-4 text-primary-600 rounded"
                          />
                          <span className="flex-1 font-mono">{group.text}</span>

                          {/* Learning Status Indicator */}
                          {group.learningStatus === 'always' && (
                            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium flex items-center gap-1" title="Always redact in future">
                              <CheckCircle2 className="w-3 h-3" />
                              Always
                            </span>
                          )}
                          {group.learningStatus === 'never' && (
                            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full font-medium flex items-center gap-1" title="Never redact in future">
                              <XCircle className="w-3 h-3" />
                              Never
                            </span>
                          )}
                          {group.learningStatus === 'flag' && (
                            <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full font-medium flex items-center gap-1" title="Flag for review (context-dependent)">
                              <AlertCircle className="w-3 h-3" />
                              Flag
                            </span>
                          )}
                          {group.learningStatus === 'neutral' && (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full font-medium flex items-center gap-1" title="Neutral - standard AI">
                              <div className="w-3 h-3 border-2 border-gray-500 rounded-full"></div>
                              Neutral
                            </span>
                          )}

                          {/* Teach/Edit button */}
                          {!group.manual && (
                            <button
                              onClick={() => setLearningDialog({
                                show: true,
                                text: group.text,
                                type: group.entity_type,
                                current: group.learningStatus
                              })}
                              className={`px-2 py-0.5 text-xs rounded-full font-medium hover:opacity-80 transition-colors ${
                                group.learningStatus
                                  ? 'bg-gray-200 text-gray-700'
                                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                              }`}
                              title={group.learningStatus ? 'Edit learning classification' : 'Teach system how to handle this term'}
                            >
                              {group.learningStatus ? 'Edit' : 'Teach'}
                            </button>
                          )}

                          {group.count > 1 && (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                              {group.count}x
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            {(group.avgScore * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        {/* Show variations if multiple case variations exist */}
                        {group.variations.length > 1 && (
                          <div className="ml-6 text-xs text-gray-500">
                            <span className="font-medium">Variations:</span>{' '}
                            {group.variations.map((v, i) => (
                              <span key={i}>
                                <span className="font-mono bg-gray-200 px-1 rounded">{v}</span>
                                {i < group.variations.length - 1 ? ', ' : ''}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Rejected entities at the bottom with red styling */}
                    {typeGroups.filter(g => !g.accepted).length > 0 && (
                      <>
                        <div className="mt-3 pt-3 border-t border-red-200">
                          <p className="text-xs text-red-600 font-medium mb-2">❌ Rejected (will NOT be redacted)</p>
                        </div>
                        {typeGroups.filter(g => !g.accepted).map((group, idx) => (
                          <div key={idx} className="flex flex-col gap-1 text-sm p-2 bg-red-50 rounded hover:bg-red-100 border border-red-200">
                            <div className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={group.accepted}
                                onChange={() => toggleGroupedEntity(group)}
                                className="w-4 h-4 text-red-600 rounded"
                              />
                              <X className="w-4 h-4 text-red-600 flex-shrink-0" />
                              <span className="flex-1 font-mono text-red-700 line-through">{group.text}</span>
                              {group.count > 1 && (
                                <span className="px-2 py-0.5 bg-red-200 text-red-800 text-xs rounded-full font-medium">
                                  {group.count}x
                                </span>
                              )}
                              <span className="text-xs text-red-500">
                                {(group.avgScore * 100).toFixed(0)}% confidence
                              </span>
                            </div>
                        {/* Show variations if multiple case variations exist */}
                        {group.variations.length > 1 && (
                          <div className="ml-6 text-xs text-gray-500">
                            <span className="font-medium">Variations:</span>{' '}
                            {group.variations.map((v, i) => (
                              <span key={i}>
                                <span className="font-mono bg-gray-200 px-1 rounded">{v}</span>
                                {i < group.variations.length - 1 ? ', ' : ''}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </>
                )}
                  </div>
                </div>
              )
            })}
          </div>
        </details>
          </div>
        </div>
      </div>

      {/* Custom Patterns Settings Modal */}
      {showSettings && (
        <CustomPatternsSettings
          onSave={(config) => {
            console.log('Custom config saved:', config)
            // Note: This will be picked up on next document load
            // Could optionally trigger re-analysis here
            alert('Settings saved! Changes will apply to the next document you analyze.')
          }}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* Learned Entities Viewer Modal */}
      {showLearnedEntities && (
        <LearnedEntitiesViewer
          isOpen={showLearnedEntities}
          onClose={() => setShowLearnedEntities(false)}
          onEditEntity={(text, entityType, newClassification) => {
            // Re-classify the entity
            handleLearningClassification(text, entityType, newClassification)
          }}
          onRemoveEntity={(text, entityType) => {
            // Remove entity from learning (set to neutral)
            handleLearningClassification(text, entityType, 'neutral')
          }}
        />
      )}

      {/* Entity Learning Dialog */}
      {learningDialog?.show && (
        <EntityLearningDialog
          entityText={learningDialog.text}
          entityType={learningDialog.type}
          currentClassification={learningDialog.current}
          onClassify={(classification) => handleLearningClassification(learningDialog.text, learningDialog.type, classification)}
          onClose={() => setLearningDialog(null)}
        />
      )}
    </div>
  )
}
