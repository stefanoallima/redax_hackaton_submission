/**
 * Detection Settings Component
 * Allows users to configure detection depth and focus areas
 */
import React, { useState } from 'react'
import { Settings, Zap, Target, Eye, Brain, Image, Info, Lock } from 'lucide-react'

interface DetectionConfig {
  depth: 'fast' | 'balanced' | 'thorough' | 'maximum'
  focusAreas: string[]
  customKeywords: string[]
  enableLLM: boolean
  enableVisual: boolean
}

interface DetectionSettingsProps {
  onConfigChange: (config: DetectionConfig) => void
  initialConfig?: DetectionConfig
  documentPages?: number  // Number of pages in uploaded document
}

const DEPTH_LEVELS = {
  fast: {
    label: 'Fast',
    icon: Zap,
    description: 'Fast search',
    time: '~5-10s',
    coverage: '40-60%',
    methods: ['Ricerca Pattern'],
    color: 'blue'
  },
  balanced: {
    label: 'Balanced',
    icon: Target,
    description: 'Look for keywords and context',
    time: '~15-30s',
    coverage: '60-70%',
    methods: ['Keyowrd matching + Context'],
    color: 'green'
  },
  thorough: {
    label: 'Deeper',
    icon: Brain,
    description: 'Analysis with visual verification of important sections',
    time: '~30-60s',
    coverage: '95-98%',
    methods: ['Pattern + Contesto + Verifica Visiva'],
    color: 'purple'
  },
  maximum: {
    label: 'Massimo',
    icon: Eye,
    description: 'Massima accuratezza: analisi completa di ogni pagina',
    time: '~60-120s',
    coverage: '98-99%',
    methods: ['Analisi Completa'],
    color: 'red'
  }
}

const FOCUS_AREAS = [
  { id: 'iban', label: 'IBAN / Bank Account', keywords: ['iban', 'account', 'banking'] },
  { id: 'cf', label: 'SSN', keywords: ['Social Security Number', 'SSN', 'ssn'] },
  { id: 'contact', label: 'Contact Details', keywords: ['phone', 'email', 'telephone', 'fax'] },
  { id: 'address', label: 'Address', keywords: ['address', 'residence', 'domicile', 'street', 'square', 'city', 'province', 'zip', 'postal', 'zipcode'] },
  { id: 'personal', label: 'Personal Data', keywords: [ 'birth', 'age', 'gender'] },
  { id: 'financial', label: 'Financial Data', keywords: ['salary', 'payment', 'amount', 'euro', 'dollars', '$'] }
]

export default function DetectionSettings({ onConfigChange, initialConfig, documentPages }: DetectionSettingsProps) {
  const [config, setConfig] = useState<DetectionConfig>(initialConfig || {
    depth: 'balanced',
    focusAreas: [],
    customKeywords: [],
    enableLLM: true,
    enableVisual: true  // Changed to true for demo
  })

  const [showAdvanced, setShowAdvanced] = useState(false)
  const [customKeywordInput, setCustomKeywordInput] = useState('')

  const handleDepthChange = (depth: 'fast' | 'balanced' | 'maximum') => {
    const newConfig = {
      ...config,
      depth,
      enableLLM: depth !== 'fast',
      enableVisual: depth === 'maximum'
    }
    setConfig(newConfig)
    onConfigChange(newConfig)
  }

  const handleFocusAreaToggle = (areaId: string) => {
    const newFocusAreas = config.focusAreas.includes(areaId)
      ? config.focusAreas.filter(id => id !== areaId)
      : [...config.focusAreas, areaId]
    
    const newConfig = { ...config, focusAreas: newFocusAreas }
    setConfig(newConfig)
    onConfigChange(newConfig)
  }

  const handleAddCustomKeyword = () => {
    if (customKeywordInput.trim()) {
      const keywords = customKeywordInput.split(',').map(k => k.trim()).filter(k => k)
      const newConfig = {
        ...config,
        customKeywords: [...config.customKeywords, ...keywords]
      }
      setConfig(newConfig)
      onConfigChange(newConfig)
      setCustomKeywordInput('')
    }
  }

  const handleRemoveKeyword = (keyword: string) => {
    const newConfig = {
      ...config,
      customKeywords: config.customKeywords.filter(k => k !== keyword)
    }
    setConfig(newConfig)
    onConfigChange(newConfig)
  }

  const currentDepth = DEPTH_LEVELS[config.depth]
  const DepthIcon = currentDepth.icon

  // Calculate time estimate based on document size
  const calculateTimeEstimate = () => {
    if (!documentPages) return null

    const TIME_PER_PAGE = {
      regex: 0.1,
      llm: 0.5,
      visual: 2.0
    }

    // Estimate pages that will trigger LLM (based on typical documents)
    const estimatedKeywordPages = Math.ceil(documentPages * 0.2) // ~20% have keywords
    const priorityPages = Math.min(6, documentPages) // First 3 + last 3

    let totalTime = 0
    let breakdown = {
      regex: 0,
      llm: 0,
      visual: 0
    }

    // Regex always runs on all pages
    breakdown.regex = documentPages * TIME_PER_PAGE.regex
    totalTime += breakdown.regex

    // LLM based on depth
    if (config.depth === 'fast') {
      breakdown.llm = 0
    } else if (config.depth === 'maximum') {
      breakdown.llm = documentPages * TIME_PER_PAGE.llm
    } else {
      // Balanced or thorough: LLM on priority + keyword pages
      const llmPages = Math.min(priorityPages + estimatedKeywordPages, documentPages)
      breakdown.llm = llmPages * TIME_PER_PAGE.llm
    }
    totalTime += breakdown.llm

    // Visual based on depth
    if (config.depth === 'fast' || config.depth === 'balanced') {
      breakdown.visual = 0
    } else if (config.depth === 'maximum') {
      breakdown.visual = documentPages * TIME_PER_PAGE.visual
    } else {
      // Thorough: visual on priority pages only
      breakdown.visual = priorityPages * TIME_PER_PAGE.visual
    }
    totalTime += breakdown.visual

    return {
      total: totalTime,
      breakdown,
      formatted: formatTime(totalTime)
    }
  }

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.ceil(seconds)}s`
    } else if (seconds < 120) {
      return `~${Math.ceil(seconds / 60)} minute`
    } else {
      return `~${Math.ceil(seconds / 60)} minutes`
    }
  }

  const timeEstimate = calculateTimeEstimate()

  return (
    <div className="bg-white rounded-lg shadow-lg p-6" data-testid="detection-settings">
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <Settings className="w-6 h-6 text-gray-700" />
        <h2 className="text-xl font-semibold">Settings</h2>
      </div>

      {/* Detection Depth Slider - HIDDEN */}
      <div className="mb-8 hidden">
        <div className="flex items-center justify-between mb-4">
          <label className="text-sm font-medium text-gray-700">Level of accuracy</label>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full bg-${currentDepth.color}-100 text-${currentDepth.color}-700`}>
            <DepthIcon className="w-4 h-4" />
            <span className="text-sm font-medium">{currentDepth.label}</span>
          </div>
        </div>

        {/* Slider */}
        <div className="relative">
          <input
            type="range"
            min="0"
            max="3"
            value={['fast', 'balanced', 'maximum'].indexOf(config.depth)}
            onChange={(e) => {
              const depths: ('fast' | 'balanced' | 'maximum')[] = ['fast', 'balanced', 'maximum']
              handleDepthChange(depths[parseInt(e.target.value)])
            }}
            data-testid="depth-slider"
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
          
          {/* Slider Labels */}
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>Fast</span>
            <span>Balanced</span>
            <span>Maximum</span>
          </div>
        </div>

        {/* Current Depth Info */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-700 mb-2">{currentDepth.description}</p>
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-gray-500">Time:</span>
                  <span className="ml-1 font-medium">
                    {timeEstimate ? timeEstimate.formatted : currentDepth.time}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Coverage:</span>
                  <span className="ml-1 font-medium">{currentDepth.coverage}</span>
                </div>
                <div>
                  <span className="text-gray-500">Methods:</span>
                  <span className="ml-1 font-medium">{currentDepth.methods.join(', ')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Time Estimate (if document uploaded) */}
        {timeEstimate && documentPages && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-blue-900">
                Tempo di Elaborazione Stimato
              </span>
              <span className="text-lg font-bold text-blue-600">
                {timeEstimate.formatted}
              </span>
            </div>
            <div className="text-xs text-blue-700 space-y-1">
              <div className="flex justify-between">
                <span>Document: {documentPages} pagine</span>
                <span>Base search: {Math.ceil(timeEstimate.breakdown.regex)}s</span>
              </div>
              {timeEstimate.breakdown.llm > 0 && (
                <div className="flex justify-between">
                  <span>Intelligent analysis:</span>
                  <span>{Math.ceil(timeEstimate.breakdown.llm)}s</span>
                </div>
              )}
              {timeEstimate.breakdown.visual > 0 && (
                <div className="flex justify-between">
                  <span>Visual scan:</span>
                  <span>{Math.ceil(timeEstimate.breakdown.visual)}s</span>
                </div>
              )}
            </div>

            {/* Speed comparison */}
            {config.depth !== 'fast' && (
              <div className="mt-2 pt-2 border-t border-blue-200">
                <div className="flex items-center gap-2 text-xs text-blue-600">
                  <Zap className="w-3 h-3" />
                  <span>
                    Fast mode will requires about ~{Math.ceil(documentPages * 0.1)}s
                    ({Math.round((1 - (documentPages * 0.1) / timeEstimate.total) * 100)}% più veloce)
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Focus Areas */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <label className="text-sm font-medium text-gray-700">
            Focused areas
            <span className="ml-2 text-xs text-gray-500">(Activate Deeper Scan)</span>
          </label>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                const allSelected = config.focusAreas.length === FOCUS_AREAS.length
                const newConfig = {
                  ...config,
                  focusAreas: allSelected ? [] : FOCUS_AREAS.map(a => a.id)
                }
                setConfig(newConfig)
                onConfigChange(newConfig)
              }}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium"
            >
              {config.focusAreas.length === FOCUS_AREAS.length ? 'Deselect All' : 'Select All'}
            </button>
            <span className="text-xs text-gray-500">
              {config.focusAreas.length} selected
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {FOCUS_AREAS.map(area => (
            <label
              key={area.id}
              className={`
                flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all
                ${config.focusAreas.includes(area.id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
                }
              `}
            >
              <input
                type="checkbox"
                checked={config.focusAreas.includes(area.id)}
                onChange={() => handleFocusAreaToggle(area.id)}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{area.label}</div>
                <div className="text-xs text-gray-500">
                  {area.keywords.slice(0, 2).join(', ')}
                  {area.keywords.length > 2 && '...'}
                </div>
              </div>
            </label>
          ))}
        </div>

        {config.focusAreas.length > 0 && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-700">
              <strong>Deep scan</strong> will be activted on pages that contains the following words in the text.
              The scan will be deeper for higher accuracy and deeper in these areas.
            </p>
          </div>
        )}
      </div>

      {/* Advanced Options */}
      <div className="border-t pt-4">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-2"
        >
          <Settings className="w-4 h-4" />
          {showAdvanced ? 'Nascondi' : 'Mostra'} Advanced Options
        </button>

        {showAdvanced && (
          <div className="mt-4 space-y-4">
            {/* Custom Keywords */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Keywords to look for for redaction purposes
                <span className="ml-2 text-xs text-gray-500">(Please separate keywords with a comma )</span>
              </label>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={customKeywordInput}
                  onChange={(e) => setCustomKeywordInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddCustomKeyword()}
                  placeholder="es., società, contratto, cliente"
                  className="flex-1 px-3 py-2 border rounded-lg text-sm"
                />
                <button
                  onClick={handleAddCustomKeyword}
                  disabled={!customKeywordInput.trim()}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
                >
                  Add
                </button>
              </div>

              {config.customKeywords.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {config.customKeywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                    >
                      {keyword}
                      <button
                        onClick={() => handleRemoveKeyword(keyword)}
                        className="text-gray-500 hover:text-red-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Manual Toggles */}
            <div className="space-y-2">
              <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer bg-white hover:bg-gray-50 transition-colors">
                <input
                  type="checkbox"
                  checked={config.enableLLM}
                  onChange={(e) => {
                    const newConfig = { ...config, enableLLM: e.target.checked }
                    setConfig(newConfig)
                    onConfigChange(newConfig)
                  }}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">Advanced intelligent analysis</span>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                      <Brain className="w-3 h-3" />
                      Active
                    </span>
                  </div>
                  <div className="text-xs text-gray-600">
                    Use GLiNER (multilanguage) to find match also in non standard formats
                  </div>
                </div>
              </label>

              <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer bg-white hover:bg-gray-50 transition-colors">
                <input
                  type="checkbox"
                  checked={config.enableVisual}
                  onChange={(e) => {
                    const newConfig = { ...config, enableVisual: e.target.checked }
                    setConfig(newConfig)
                    onConfigChange(newConfig)
                  }}
                  className="w-4 h-4 text-primary-600 rounded"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">Enable Visual Recognition</span>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                      <Image className="w-3 h-3" />
                      ATTIVO
                    </span>
                  </div>
                  <div className="text-xs text-gray-600">
                    Use Google Gemini to find text to redact inside images, tables e visual content
                  </div>
                </div>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Summary of the detection</h3>
        <ul className="text-xs text-gray-700 space-y-1">
          <li>✓ Automatic search on <strong>all pages</strong></li>
          <li>✓ Optimized for Italian legal documents</li>
          {config.focusAreas.length > 0 && (
            <li>✓ Enhanced detection for {config.focusAreas.length} focus area/s</li>
          )}
          {config.customKeywords.length > 0 && (
            <li>✓ Custom keywords to detect: {config.customKeywords.length} keywords</li>
          )}
        </ul>
      </div>
    </div>
  )
}
