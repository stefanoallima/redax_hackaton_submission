/**
 * Learned Entities Viewer Component
 * Displays all learned entities (allow-list and deny-list) with 4-state classification
 * Allows users to view, edit, and remove learned terms
 */
import React, { useState, useEffect } from 'react'
import { CheckCircle2, AlertCircle, XCircle, Circle, Trash2, Edit2, Search, Filter, X } from 'lucide-react'

interface LearnedEntity {
  text: string
  entityType: string
  classification: 'always' | 'flag' | 'neutral' | 'never'
  flag_for_review?: boolean
}

interface LearnedEntitiesViewerProps {
  isOpen: boolean
  onClose: () => void
  onEditEntity?: (text: string, entityType: string, newClassification: 'always' | 'flag' | 'neutral' | 'never') => void
  onRemoveEntity?: (text: string, entityType: string) => void
}

const CLASSIFICATION_INFO = {
  always: {
    label: '✓✓ Always Redact',
    color: 'green',
    icon: CheckCircle2,
    description: 'Auto-detected and redacted in all documents'
  },
  flag: {
    label: '⚠ Flag to Review',
    color: 'orange',
    icon: AlertCircle,
    description: 'Always detected, manual review required (context-dependent)'
  },
  neutral: {
    label: '○ Neutral',
    color: 'gray',
    icon: Circle,
    description: 'Standard AI detection, no preference'
  },
  never: {
    label: '✗✗ Never Redact',
    color: 'red',
    icon: XCircle,
    description: 'Permanently ignored in all documents'
  }
}

export default function LearnedEntitiesViewer({
  isOpen,
  onClose,
  onEditEntity,
  onRemoveEntity
}: LearnedEntitiesViewerProps) {
  const [entities, setEntities] = useState<LearnedEntity[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [filterClassification, setFilterClassification] = useState<string>('all')

  // Load entities from localStorage
  useEffect(() => {
    if (!isOpen) return

    const loadEntities = () => {
      const configStr = localStorage.getItem('custom_recognizer_config')
      if (!configStr) {
        setEntities([])
        return
      }

      const config = JSON.parse(configStr)
      const loadedEntities: LearnedEntity[] = []

      // Load from allow-lists (ALWAYS and FLAG)
      if (config.allow_lists && Array.isArray(config.allow_lists)) {
        config.allow_lists.forEach((allowList: any) => {
          const entityType = allowList.entity_type || 'UNKNOWN'
          const terms = allowList.terms || []
          const flagForReview = allowList.flag_for_review || false

          terms.forEach((term: string) => {
            loadedEntities.push({
              text: term,
              entityType: entityType,
              classification: flagForReview ? 'flag' : 'always',
              flag_for_review: flagForReview
            })
          })
        })
      }

      // Load from deny-lists (NEVER)
      if (config.deny_lists && typeof config.deny_lists === 'object') {
        Object.entries(config.deny_lists).forEach(([entityType, terms]) => {
          if (Array.isArray(terms)) {
            terms.forEach((term: string) => {
              loadedEntities.push({
                text: term,
                entityType: entityType,
                classification: 'never'
              })
            })
          }
        })
      }

      setEntities(loadedEntities)
    }

    loadEntities()
  }, [isOpen])

  // Filter entities
  const filteredEntities = entities.filter(entity => {
    // Search filter
    if (searchTerm && !entity.text.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }

    // Entity type filter
    if (filterType !== 'all' && entity.entityType !== filterType) {
      return false
    }

    // Classification filter
    if (filterClassification !== 'all' && entity.classification !== filterClassification) {
      return false
    }

    return true
  })

  // Get unique entity types
  const entityTypes = Array.from(new Set(entities.map(e => e.entityType))).sort()

  // Group by entity type
  const groupedEntities = filteredEntities.reduce((acc, entity) => {
    if (!acc[entity.entityType]) {
      acc[entity.entityType] = []
    }
    acc[entity.entityType].push(entity)
    return acc
  }, {} as Record<string, LearnedEntity[]>)

  // Handle remove
  const handleRemove = (text: string, entityType: string) => {
    if (!confirm(`Rimuovere "${text}" dalla lista di apprendimento?`)) {
      return
    }

    if (onRemoveEntity) {
      onRemoveEntity(text, entityType)
    }

    // Reload entities
    const event = new Event('storage')
    window.dispatchEvent(event)
  }

  // Statistics
  const stats = {
    total: entities.length,
    always: entities.filter(e => e.classification === 'always').length,
    flag: entities.filter(e => e.classification === 'flag').length,
    never: entities.filter(e => e.classification === 'never').length
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Entità Apprese</h2>
              <p className="text-sm text-gray-600 mt-1">
                Gestisci le tue preferenze di classificazione
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              title="Chiudi"
            >
              <X className="w-6 h-6 text-gray-600" />
            </button>
          </div>

          {/* Statistics */}
          <div className="mt-4 grid grid-cols-4 gap-3">
            <div className="bg-white p-3 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
              <div className="text-xs text-gray-600">Totale</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg border border-green-200">
              <div className="text-2xl font-bold text-green-700">{stats.always}</div>
              <div className="text-xs text-green-600">Always Redact</div>
            </div>
            <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
              <div className="text-2xl font-bold text-orange-700">{stats.flag}</div>
              <div className="text-xs text-orange-600">Flag to Review</div>
            </div>
            <div className="bg-red-50 p-3 rounded-lg border border-red-200">
              <div className="text-2xl font-bold text-red-700">{stats.never}</div>
              <div className="text-xs text-red-600">Never Redact</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 border-b bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Cerca entità..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border rounded-lg text-sm"
              />
            </div>

            {/* Entity Type Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border rounded-lg text-sm appearance-none"
              >
                <option value="all">Tutti i tipi</option>
                {entityTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            {/* Classification Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filterClassification}
                onChange={(e) => setFilterClassification(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border rounded-lg text-sm appearance-none"
              >
                <option value="all">Tutte le classificazioni</option>
                <option value="always">✓✓ Always Redact</option>
                <option value="flag">⚠ Flag to Review</option>
                <option value="never">✗✗ Never Redact</option>
              </select>
            </div>
          </div>
        </div>

        {/* Entities List */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredEntities.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <Circle className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                {searchTerm || filterType !== 'all' || filterClassification !== 'all'
                  ? 'Nessun risultato'
                  : 'Nessuna entità appresa'}
              </h3>
              <p className="text-sm text-gray-500">
                {searchTerm || filterType !== 'all' || filterClassification !== 'all'
                  ? 'Prova a modificare i filtri di ricerca'
                  : 'Inizia a classificare le entità durante la revisione dei documenti'}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedEntities).sort().map(([entityType, typeEntities]) => (
                <div key={entityType}>
                  {/* Entity Type Header */}
                  <div className="flex items-center gap-2 mb-3">
                    <h3 className="text-sm font-semibold text-gray-900">{entityType}</h3>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                      {typeEntities.length}
                    </span>
                  </div>

                  {/* Entities Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {typeEntities.sort((a, b) => a.text.localeCompare(b.text)).map((entity, idx) => {
                      const classInfo = CLASSIFICATION_INFO[entity.classification]
                      const IconComponent = classInfo.icon

                      return (
                        <div
                          key={`${entity.text}-${idx}`}
                          className={`
                            p-3 rounded-lg border-2 bg-${classInfo.color}-50 border-${classInfo.color}-200
                            hover:shadow-md transition-all
                          `}
                        >
                          {/* Entity Text */}
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1 min-w-0">
                              <div className="font-mono text-sm font-semibold text-gray-900 truncate">
                                "{entity.text}"
                              </div>
                            </div>
                            <div className="flex gap-1 ml-2">
                              {onEditEntity && (
                                <button
                                  onClick={() => {
                                    // TODO: Open edit dialog
                                    console.log('Edit:', entity.text)
                                  }}
                                  className={`p-1 hover:bg-${classInfo.color}-200 rounded transition-colors`}
                                  title="Modifica classificazione"
                                >
                                  <Edit2 className="w-3 h-3 text-gray-600" />
                                </button>
                              )}
                              <button
                                onClick={() => handleRemove(entity.text, entity.entityType)}
                                className={`p-1 hover:bg-red-200 rounded transition-colors`}
                                title="Rimuovi"
                              >
                                <Trash2 className="w-3 h-3 text-red-600" />
                              </button>
                            </div>
                          </div>

                          {/* Classification Badge */}
                          <div className={`flex items-center gap-2 text-${classInfo.color}-700`}>
                            <IconComponent className="w-4 h-4" />
                            <span className="text-xs font-medium">{classInfo.label}</span>
                          </div>

                          {/* Description */}
                          <p className={`text-xs text-${classInfo.color}-600 mt-1`}>
                            {classInfo.description}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {filteredEntities.length === entities.length ? (
                <span>Visualizzando tutte le {entities.length} entità</span>
              ) : (
                <span>
                  Visualizzando {filteredEntities.length} di {entities.length} entità
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Chiudi
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
