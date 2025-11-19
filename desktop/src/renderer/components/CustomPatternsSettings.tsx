/**
 * Custom Patterns Settings Component
 * Allows users to configure custom recognizers, allow-lists, and deny-lists
 */
import React, { useState, useEffect } from 'react'
import { Plus, X, Save, Settings, AlertCircle, CheckCircle } from 'lucide-react'

interface Pattern {
  name: string
  regex: string
  score: number
}

interface PatternConfig {
  entity_type: string
  enabled: boolean
  patterns: Pattern[]
  context: string[]
}

interface AllowListConfig {
  entity_type: string
  enabled: boolean
  terms: string[]
  case_sensitive: boolean
}

interface CustomConfig {
  patterns: PatternConfig[]
  allow_lists: AllowListConfig[]
  deny_lists: Record<string, string[]>
}

interface CustomPatternsSettingsProps {
  onSave?: (config: CustomConfig) => void
  onClose?: () => void
}

const ENTITY_TYPES = [
  { value: 'PERSON', label: 'Person Names' },
  { value: 'ORGANIZATION', label: 'Organizations' },
  { value: 'LOCATION', label: 'Locations' },
  { value: 'MONETARY_AMOUNT', label: 'Monetary Amounts' },
  { value: 'IT_CASE_NUMBER', label: 'Case Numbers' },
  { value: 'CUSTOM', label: 'Custom Entity' }
]

export default function CustomPatternsSettings({ onSave, onClose }: CustomPatternsSettingsProps) {
  const [config, setConfig] = useState<CustomConfig>({
    patterns: [],
    allow_lists: [],
    deny_lists: {}
  })
  const [activeTab, setActiveTab] = useState<'patterns' | 'allow' | 'deny'>('allow')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')

  // Load saved configuration from localStorage
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const saved = localStorage.getItem('custom_recognizer_config')
        if (saved) {
          setConfig(JSON.parse(saved))
        } else {
          // Load default configuration
          setConfig(getDefaultConfig())
        }
      } catch (error) {
        console.error('Failed to load custom config:', error)
        setConfig(getDefaultConfig())
      }
    }
    loadConfig()
  }, [])

  const getDefaultConfig = (): CustomConfig => {
    return {
      patterns: [
        {
          entity_type: 'IT_CASE_NUMBER',
          enabled: true,
          patterns: [
            { name: 'case_basic', regex: '\\b\\d{1,6}/\\d{4}\\b', score: 0.85 }
          ],
          context: ['sentenza', 'procedimento', 'causa']
        }
      ],
      allow_lists: [],
      deny_lists: {
        'PERSON': ['Giudice', 'Avvocato', 'Procuratore', 'Notaio', 'Presidente'],
        'LOCATION': ['Italia', 'Repubblica Italiana', 'Unione Europea'],
        'ORGANIZATION': ['Tribunale', 'Corte', 'Procura']
      }
    }
  }

  const handleSave = () => {
    setSaveStatus('saving')

    // Save to localStorage
    localStorage.setItem('custom_recognizer_config', JSON.stringify(config))

    // Notify parent component
    if (onSave) {
      onSave(config)
    }

    setSaveStatus('saved')
    setTimeout(() => setSaveStatus('idle'), 2000)
  }

  // Allow-list management
  const addAllowList = () => {
    setConfig(prev => ({
      ...prev,
      allow_lists: [
        ...prev.allow_lists,
        {
          entity_type: 'PERSON',
          enabled: true,
          terms: [],
          case_sensitive: false
        }
      ]
    }))
  }

  const removeAllowList = (index: number) => {
    setConfig(prev => ({
      ...prev,
      allow_lists: prev.allow_lists.filter((_, i) => i !== index)
    }))
  }

  const updateAllowList = (index: number, updates: Partial<AllowListConfig>) => {
    setConfig(prev => ({
      ...prev,
      allow_lists: prev.allow_lists.map((item, i) =>
        i === index ? { ...item, ...updates } : item
      )
    }))
  }

  const addTermToAllowList = (index: number, term: string) => {
    if (!term.trim()) return
    updateAllowList(index, {
      terms: [...config.allow_lists[index].terms, term.trim()]
    })
  }

  const removeTermFromAllowList = (listIndex: number, termIndex: number) => {
    updateAllowList(listIndex, {
      terms: config.allow_lists[listIndex].terms.filter((_, i) => i !== termIndex)
    })
  }

  // Deny-list management
  const addEntityTypeToDenyList = (entityType: string) => {
    if (!config.deny_lists[entityType]) {
      setConfig(prev => ({
        ...prev,
        deny_lists: {
          ...prev.deny_lists,
          [entityType]: []
        }
      }))
    }
  }

  const addTermToDenyList = (entityType: string, term: string) => {
    if (!term.trim()) return
    setConfig(prev => ({
      ...prev,
      deny_lists: {
        ...prev.deny_lists,
        [entityType]: [...(prev.deny_lists[entityType] || []), term.trim()]
      }
    }))
  }

  const removeTermFromDenyList = (entityType: string, termIndex: number) => {
    setConfig(prev => ({
      ...prev,
      deny_lists: {
        ...prev.deny_lists,
        [entityType]: prev.deny_lists[entityType].filter((_, i) => i !== termIndex)
      }
    }))
  }

  const removeDenyListEntityType = (entityType: string) => {
    setConfig(prev => {
      const newDenyLists = { ...prev.deny_lists }
      delete newDenyLists[entityType]
      return {
        ...prev,
        deny_lists: newDenyLists
      }
    })
  }

  // Pattern management
  const addPattern = () => {
    setConfig(prev => ({
      ...prev,
      patterns: [
        ...prev.patterns,
        {
          entity_type: 'CUSTOM',
          enabled: true,
          patterns: [{ name: 'pattern_1', regex: '', score: 0.85 }],
          context: []
        }
      ]
    }))
  }

  const removePattern = (index: number) => {
    setConfig(prev => ({
      ...prev,
      patterns: prev.patterns.filter((_, i) => i !== index)
    }))
  }

  const updatePattern = (index: number, updates: Partial<PatternConfig>) => {
    setConfig(prev => ({
      ...prev,
      patterns: prev.patterns.map((item, i) =>
        i === index ? { ...item, ...updates } : item
      )
    }))
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-semibold">Custom Detection Rules</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b bg-gray-50 px-6">
          <button
            onClick={() => setActiveTab('allow')}
            className={`px-4 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'allow'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Always Detect (Allow-list)
          </button>
          <button
            onClick={() => setActiveTab('deny')}
            className={`px-4 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'deny'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Never Detect (Deny-list)
          </button>
          <button
            onClick={() => setActiveTab('patterns')}
            className={`px-4 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'patterns'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Custom Patterns (Advanced)
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Allow-list Tab */}
          {activeTab === 'allow' && (
            <div className="space-y-4">
              <div className="flex items-start gap-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <strong>Allow-list:</strong> Force-detect specific terms that should always be redacted,
                  even if AI doesn't detect them. Useful for company names, specific addresses, etc.
                </div>
              </div>

              {config.allow_lists.map((allowList, index) => (
                <AllowListEditor
                  key={index}
                  config={allowList}
                  onUpdate={(updates) => updateAllowList(index, updates)}
                  onRemove={() => removeAllowList(index)}
                  onAddTerm={(term) => addTermToAllowList(index, term)}
                  onRemoveTerm={(termIndex) => removeTermFromAllowList(index, termIndex)}
                />
              ))}

              <button
                onClick={addAllowList}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-gray-600 hover:text-primary-600 font-medium flex items-center justify-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Add Allow-list
              </button>
            </div>
          )}

          {/* Deny-list Tab */}
          {activeTab === 'deny' && (
            <div className="space-y-4">
              <div className="flex items-start gap-2 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-amber-800">
                  <strong>Deny-list:</strong> Prevent specific terms from being detected as PII.
                  Useful for filtering out common false positives like "Giudice", "Tribunale", etc.
                </div>
              </div>

              {Object.entries(config.deny_lists).map(([entityType, terms]) => (
                <DenyListEditor
                  key={entityType}
                  entityType={entityType}
                  terms={terms}
                  onAddTerm={(term) => addTermToDenyList(entityType, term)}
                  onRemoveTerm={(termIndex) => removeTermFromDenyList(entityType, termIndex)}
                  onRemove={() => removeDenyListEntityType(entityType)}
                />
              ))}

              <select
                onChange={(e) => {
                  if (e.target.value) {
                    addEntityTypeToDenyList(e.target.value)
                    e.target.value = ''
                  }
                }}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-gray-600 font-medium"
              >
                <option value="">+ Add Deny-list for Entity Type...</option>
                {ENTITY_TYPES.map(et => (
                  <option key={et.value} value={et.value} disabled={!!config.deny_lists[et.value]}>
                    {et.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Patterns Tab */}
          {activeTab === 'patterns' && (
            <div className="space-y-4">
              <div className="flex items-start gap-2 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-purple-800">
                  <strong>Custom Patterns:</strong> Advanced regex patterns for detecting structured data
                  like case numbers (123/2024), amounts (€50,000), etc.
                </div>
              </div>

              {config.patterns.map((pattern, index) => (
                <PatternEditor
                  key={index}
                  config={pattern}
                  onUpdate={(updates) => updatePattern(index, updates)}
                  onRemove={() => removePattern(index)}
                />
              ))}

              <button
                onClick={addPattern}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-gray-600 hover:text-primary-600 font-medium flex items-center justify-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Add Custom Pattern
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {saveStatus === 'saved' && (
              <span className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                Settings saved successfully
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saveStatus === 'saving'}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saveStatus === 'saving' ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Sub-components

function AllowListEditor({ config, onUpdate, onRemove, onAddTerm, onRemoveTerm }: any) {
  const [newTerm, setNewTerm] = useState('')

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1">
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) => onUpdate({ enabled: e.target.checked })}
            className="w-5 h-5 text-primary-600 rounded"
          />
          <select
            value={config.entity_type}
            onChange={(e) => onUpdate({ entity_type: e.target.value })}
            className="px-3 py-2 border rounded-lg"
          >
            {ENTITY_TYPES.map(et => (
              <option key={et.value} value={et.value}>{et.label}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={config.case_sensitive}
              onChange={(e) => onUpdate({ case_sensitive: e.target.checked })}
              className="w-4 h-4 text-primary-600 rounded"
            />
            Case-sensitive
          </label>
        </div>
        <button
          onClick={onRemove}
          className="p-2 hover:bg-red-100 rounded-lg text-red-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newTerm}
          onChange={(e) => setNewTerm(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onAddTerm(newTerm)
              setNewTerm('')
            }
          }}
          placeholder="Add term to always detect..."
          className="flex-1 px-3 py-2 border rounded-lg"
        />
        <button
          onClick={() => {
            onAddTerm(newTerm)
            setNewTerm('')
          }}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {config.terms.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {config.terms.map((term: string, index: number) => (
            <span
              key={index}
              className="inline-flex items-center gap-2 px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
            >
              {term}
              <button
                onClick={() => onRemoveTerm(index)}
                className="hover:bg-primary-200 rounded-full p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function DenyListEditor({ entityType, terms, onAddTerm, onRemoveTerm, onRemove }: any) {
  const [newTerm, setNewTerm] = useState('')
  const entityLabel = ENTITY_TYPES.find(et => et.value === entityType)?.label || entityType

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <div className="flex items-start justify-between mb-3">
        <h4 className="font-medium text-gray-900">{entityLabel}</h4>
        <button
          onClick={onRemove}
          className="p-2 hover:bg-red-100 rounded-lg text-red-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newTerm}
          onChange={(e) => setNewTerm(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onAddTerm(newTerm)
              setNewTerm('')
            }
          }}
          placeholder="Add term to ignore..."
          className="flex-1 px-3 py-2 border rounded-lg"
        />
        <button
          onClick={() => {
            onAddTerm(newTerm)
            setNewTerm('')
          }}
          className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {terms.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {terms.map((term: string, index: number) => (
            <span
              key={index}
              className="inline-flex items-center gap-2 px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm"
            >
              {term}
              <button
                onClick={() => onRemoveTerm(index)}
                className="hover:bg-amber-200 rounded-full p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function PatternEditor({ config, onUpdate, onRemove }: any) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1">
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) => onUpdate({ enabled: e.target.checked })}
            className="w-5 h-5 text-primary-600 rounded"
          />
          <select
            value={config.entity_type}
            onChange={(e) => onUpdate({ entity_type: e.target.value })}
            className="px-3 py-2 border rounded-lg flex-1"
          >
            {ENTITY_TYPES.map(et => (
              <option key={et.value} value={et.value}>{et.label}</option>
            ))}
          </select>
        </div>
        <button
          onClick={onRemove}
          className="p-2 hover:bg-red-100 rounded-lg text-red-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {config.patterns.map((pattern: Pattern, index: number) => (
        <div key={index} className="space-y-2 mb-3">
          <input
            type="text"
            value={pattern.regex}
            onChange={(e) => {
              const newPatterns = [...config.patterns]
              newPatterns[index] = { ...pattern, regex: e.target.value }
              onUpdate({ patterns: newPatterns })
            }}
            placeholder="Regular expression (e.g., \b\d{1,6}/\d{4}\b)"
            className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
          />
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-700">Confidence:</label>
            <input
              type="range"
              min="50"
              max="100"
              value={pattern.score * 100}
              onChange={(e) => {
                const newPatterns = [...config.patterns]
                newPatterns[index] = { ...pattern, score: parseInt(e.target.value) / 100 }
                onUpdate({ patterns: newPatterns })
              }}
              className="flex-1"
            />
            <span className="text-sm font-medium text-gray-900">{Math.round(pattern.score * 100)}%</span>
          </div>
        </div>
      ))}

      <div className="mt-3 pt-3 border-t">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Context keywords (optional, comma-separated):
        </label>
        <input
          type="text"
          value={config.context.join(', ')}
          onChange={(e) => {
            const keywords = e.target.value.split(',').map(k => k.trim()).filter(Boolean)
            onUpdate({ context: keywords })
          }}
          placeholder="e.g., sentenza, procedimento, causa"
          className="w-full px-3 py-2 border rounded-lg text-sm"
        />
      </div>
    </div>
  )
}
