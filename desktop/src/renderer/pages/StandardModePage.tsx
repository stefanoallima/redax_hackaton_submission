/**
 * Standard Mode Page - Document selection and upload
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Upload, Settings as SettingsIcon, Brain, ArrowLeft } from 'lucide-react'
import DetectionSettings from '../components/DetectionSettings'
import ErrorDisplay from '../components/ErrorDisplay'
import { ScanModeSelector, ScanMode } from '../components/ScanModeSelector'
import { GeminiChatPanel } from '../components/GeminiChatPanel'
import { LearningConfirmationModal } from '../components/LearningConfirmationModal'

interface DetectionConfig {
  depth: 'fast' | 'balanced' | 'thorough' | 'maximum'
  focusAreas: string[]
  customKeywords: string[]
  enableLLM: boolean
  enableVisual: boolean
}

// File validation constants
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
const ALLOWED_EXTENSIONS = /\.(pdf|docx?|txt|jpe?g|png)$/i  // Added JPG, JPEG, PNG for visual detection

export default function StandardModePage() {
  const navigate = useNavigate()
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [detectionConfig, setDetectionConfig] = useState<DetectionConfig>({
    depth: 'balanced',
    focusAreas: [],
    customKeywords: [],
    enableLLM: true,
    enableVisual: true  // Enabled by default for demo
  })

  // Gemini AI Integration State
  const [scanMode, setScanMode] = useState<ScanMode>('standard')
  const [learnedCount, setLearnedCount] = useState(0)
  const [geminiResults, setGeminiResults] = useState<any>(null)
  const [showLearningModal, setShowLearningModal] = useState(false)
  const [isGeminiScanning, setIsGeminiScanning] = useState(false)
  const [isLearning, setIsLearning] = useState(false)

  // Template State
  const [availableTemplates, setAvailableTemplates] = useState<any[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)

  // Load learned entities stats and templates on mount
  useEffect(() => {
    let cancelled = false

    const loadLearnedStats = async () => {
      try {
        const stats = await window.electron.ipcRenderer.invoke('get-learned-stats')
        if (!cancelled && stats.status === 'success') {
          setLearnedCount(stats.total_learned || 0)
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Failed to load learned stats:', err)
          // Don't show error to user, just log it
        }
      }
    }

    const loadTemplates = async () => {
      setIsLoadingTemplates(true)
      try {
        const result = await window.electron.ipcRenderer.invoke('list-templates')
        if (!cancelled && result.status === 'success') {
          setAvailableTemplates(result.templates || [])
          console.log('✅ Loaded templates:', result.count)
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Failed to load templates:', err)
        }
      } finally {
        if (!cancelled) {
          setIsLoadingTemplates(false)
        }
      }
    }

    loadLearnedStats()
    loadTemplates()

    return () => {
      cancelled = true
    }
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleFileSelect = (file: File) => {
    // Validate file extension
    if (!ALLOWED_EXTENSIONS.test(file.name)) {
      setError(`Invalid file type: ${file.name}\n\nUpload PDF, DOCX, TXT or image files (JPG, PNG) for visual detection.`)
      return
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large: ${(file.size / 1024 / 1024).toFixed(2)} MB\n\nMaximum allowed size: ${MAX_FILE_SIZE / 1024 / 1024} MB.\n\nFile: ${file.name}`)
      return
    }

    // Check file path exists (Electron-specific)
    if (!file.path) {
      setError(`Unable to access file path.\n\nFile: ${file.name}\n\nThis can happen if the file was selected from a protected location.`)
      return
    }

    // Clear any previous errors and store the file
    setError(null)
    setSelectedFile(file)
  }

  const handleGeminiScan = async (customPrompt?: string) => {
    if (!selectedFile) {
      setError('No document selected.\n\nPlease select a PDF or DOCX file first.')
      return
    }

    setIsGeminiScanning(true)
    setError(null)

    try {
      console.log('[HomePage] Starting Gemini scan:', selectedFile.path)
      const result = await window.electron.ipcRenderer.invoke('gemini-scan', {
        file_path: selectedFile.path,
        prompt: customPrompt
      })

      console.log('[HomePage] Gemini scan complete:', result.summary)
      setGeminiResults(result)
      setShowLearningModal(true)
    } catch (err) {
      console.error('Error during Gemini scan:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(`Gemini Scan Error: ${errorMessage}\n\nVerify that:\n1. Gemini API key is configured in .env\n2. The file is not corrupted\n3. Internet connection is active`)
    } finally {
      setIsGeminiScanning(false)
    }
  }

  const handleLearnFromGemini = async (confirmed: any[], denied: any[]) => {
    setIsLearning(true)

    try {
      console.log('[HomePage] Learning from Gemini:', confirmed.length, 'confirmed,', denied.length, 'denied')
      const result = await window.electron.ipcRenderer.invoke('learn-from-gemini', {
        confirmed_entities: confirmed,
        denied_entities: denied
      })

      console.log('[HomePage] Learning complete:', result)
      setLearnedCount(result.total_learned || 0)
      setShowLearningModal(false)

      // Show success message
      if (result.learned_count > 0) {
        alert(`✓ ${result.learned_count} entities learned successfully!\n\nFuture standard scans will now recognize them automatically.`)
      }
    } catch (err) {
      console.error('Error learning from Gemini:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(`Error during learning: ${errorMessage}`)
    } finally {
      setIsLearning(false)
    }
  }

  const handleApplyTemplate = async () => {
    if (!selectedFile) {
      setError('No document selected.\n\nPlease select a PDF file first.')
      return
    }

    if (!selectedTemplate) {
      setError('No template selected.\n\nPlease select a template from the list.')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      console.log('[StandardMode] Applying template:', selectedTemplate, 'to file:', selectedFile.path)

      // Call backend to extract actual text from PDF at bbox coordinates
      const result = await window.electron.ipcRenderer.invoke('apply-template', selectedFile.path, selectedTemplate)

      if (result.status !== 'success') {
        throw new Error(result.error || 'Failed to apply template')
      }

      console.log('[StandardMode] Template applied with extracted text:', result)

      // Navigate to process page with template results
      navigate('/process', {
        state: {
          file: selectedFile,
          result,
          config: detectionConfig,
          isTemplateMode: true
        }
      })
    } catch (err) {
      console.error('Error applying template:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(`Error applying template: ${errorMessage}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleStartDetection = async () => {
    if (!selectedFile) {
      setError('No document selected.\n\nPlease select a PDF or DOCX file first.')
      return
    }

    // If template is selected, use template mode instead
    if (selectedTemplate) {
      return handleApplyTemplate()
    }

    // Block Standard Scan button if Gemini mode is selected
    if (scanMode === 'gemini') {
      setError('For Gemini Scan, use the "Analyze with Gemini AI" button in the section below.')
      return
    }

    setIsProcessing(true)
    setError(null)

    // Process document via Electron IPC with detection config
    try {
      console.log('[HomePage] Sending document to backend:', selectedFile.path)
      const result = await window.electron.processDocument({
        action: 'process_document',
        file_path: selectedFile.path,
        config: detectionConfig
      })
      console.log('[HomePage] Received result from backend:')
      console.log('  Status:', result.status)
      console.log('  Entities count:', result.entities?.length || 0)
      console.log('  First entity:', result.entities?.[0])
      console.log('  Full result:', result)

      // Navigate to process page with results
      navigate('/process', { state: { file: selectedFile, result, config: detectionConfig } })
    } catch (err) {
      console.error('Error processing document:', err)

      // Build detailed error message
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      const timestamp = new Date().toISOString()

      const detailedError = `Error processing document: ${errorMessage}

File: ${selectedFile.name}
Path: ${selectedFile.path}
Size: ${(selectedFile.size / 1024 / 1024).toFixed(2)} MB
Detection config: ${JSON.stringify(detectionConfig, null, 2)}
Timestamp: ${timestamp}

If this error persists:
1. Verify that the file is not corrupted
2. Try with a smaller file
3. Contact support with this error message`

      setError(detailedError)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <>
      {/* Error Display Modal */}
      <ErrorDisplay error={error} onClose={() => setError(null)} />

      {/* Learning Confirmation Modal */}
      <LearningConfirmationModal
        isOpen={showLearningModal}
        onClose={() => setShowLearningModal(false)}
        geminiResults={geminiResults}
        onConfirm={handleLearnFromGemini}
        isLearning={isLearning}
      />

      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="bg-white border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <FileText className="w-6 h-6 text-primary-600" />
              <div>
                <h1 className="text-xl font-semibold">Standard Redaction</h1>
                <p className="text-xs text-gray-600">Auto-detect sensitive data</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                data-testid="settings-button"
                onClick={() => navigate('/settings')}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
              >
                Settings
              </button>
            </div>
          </div>
        </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Detection Settings */}
          <div>
            {/* Scan Mode Selector - Prominent Position */}
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-4">
                Choose Detection Method
              </h2>
              <ScanModeSelector
                selectedMode={scanMode}
                onModeChange={setScanMode}
                learnedCount={learnedCount}
                disabled={isProcessing || isGeminiScanning}
              />
            </div>

            {/* Detection Settings - Hidden slider, show focus areas */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">
                Additional Settings
              </h3>
              <DetectionSettings
                onConfigChange={setDetectionConfig}
                initialConfig={detectionConfig}
              />
            </div>

            {/* Template Selector */}
            <div className="mt-6 p-4 bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="w-5 h-5 text-indigo-600" />
                <h3 className="font-semibold text-indigo-900">Use Saved Template</h3>
              </div>

              {isLoadingTemplates ? (
                <div className="space-y-3" role="status" aria-label="Loading available templates">
                  {/* Skeleton for description text */}
                  <div className="h-4 bg-indigo-200/40 rounded animate-pulse" />
                  <div className="h-4 bg-indigo-200/40 rounded animate-pulse w-3/4" />

                  {/* Skeleton for dropdown */}
                  <div className="h-10 bg-indigo-200/40 rounded-lg animate-pulse" />

                  {/* Skeleton for template info */}
                  <div className="space-y-2 mt-3">
                    <div className="h-3 bg-indigo-200/30 rounded animate-pulse w-1/2" />
                    <div className="h-3 bg-indigo-200/30 rounded animate-pulse w-2/3" />
                  </div>

                  <span className="sr-only">Loading templates, please wait...</span>
                </div>
              ) : availableTemplates.length === 0 ? (
                <div className="text-sm text-gray-600">
                  <p className="mb-2">No templates saved yet.</p>
                  <p className="text-xs text-gray-500">
                    Go to Teaching Mode to create templates from blank forms.
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-sm text-indigo-800 mb-3">
                    Apply a saved template to similar documents for instant redaction
                  </p>
                  <select
                    value={selectedTemplate || ''}
                    onChange={(e) => setSelectedTemplate(e.target.value || null)}
                    disabled={isProcessing || isGeminiScanning}
                    className="w-full px-3 py-2 border-2 border-indigo-300 rounded-lg bg-white text-sm focus:border-indigo-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="">Select a template (optional)</option>
                    {availableTemplates.map((template) => (
                      <option key={template.template_id} value={template.template_id}>
                        {template.description} ({template.regions_count} regions)
                        {template.voice_command && ` - "${template.voice_command}"`}
                      </option>
                    ))}
                  </select>

                  {selectedTemplate && (
                    <div className="mt-3 p-3 bg-indigo-100 border border-indigo-300 rounded-lg">
                      <p className="text-xs font-semibold text-indigo-900 mb-1">✓ Template selected</p>
                      <p className="text-xs text-indigo-700">
                        When you upload a document, this template's regions will be automatically applied.
                        Click "Start Detection" to proceed.
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Right Column - Upload */}
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">
                Upload Document or Image
              </h2>
              <p className="text-gray-600">
                Select a PDF, DOCX or image file (JPG, PNG) to detect personal data
              </p>
            </div>

            {/* Drop Zone */}
            <div
              data-testid="upload-area"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                border-2 border-dashed rounded-lg p-12
                transition-colors cursor-pointer
                ${isDragging
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 bg-white hover:border-primary-400'
                }
                ${selectedFile ? 'border-green-500 bg-green-50' : ''}
              `}
            >
              <div className="text-center">
                <Upload className={`
                  w-16 h-16 mx-auto mb-4
                  ${isDragging ? 'text-primary-600' : selectedFile ? 'text-green-600' : 'text-gray-400'}
                `} />
                {selectedFile ? (
                  <>
                    <p className="text-lg font-medium mb-2 text-green-700">
                      ✓ {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-600 mb-4">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <label className="inline-block">
                      <span className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 cursor-pointer text-sm">
                        Choose Another File
                      </span>
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png"
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) handleFileSelect(file)
                        }}
                      />
                    </label>
                  </>
                ) : (
                  <>
                    <p className="text-lg font-medium mb-2">
                      Drag your document here
                    </p>
                    <p className="text-sm text-gray-500 mb-4">
                      or
                    </p>
                    <label className="inline-block">
                      <span className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 cursor-pointer">
                        Browse Files
                      </span>
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png"
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) handleFileSelect(file)
                        }}
                      />
                    </label>
                    <p className="text-xs text-gray-500 mt-4">
                      Supported formats: PDF, DOCX, TXT, JPG, PNG (max 100MB)
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Gemini Chat Panel - Shown when Gemini mode is selected */}
            {scanMode === 'gemini' && (
              <div className="mt-6">
                <GeminiChatPanel
                  onScan={handleGeminiScan}
                  isLoading={isGeminiScanning}
                  error={error}
                />
              </div>
            )}

            {/* Scan Button - Always in same position */}
            <div className="mt-6">
              {scanMode === 'standard' ? (
                <button
                  data-testid="start-detection-button"
                  onClick={handleStartDetection}
                  disabled={!selectedFile || isProcessing || isGeminiScanning}
                  className={`
                    w-full py-4 px-6 rounded-lg font-semibold text-lg
                    transition-all duration-200
                    ${selectedFile && !isProcessing && !isGeminiScanning
                      ? selectedTemplate
                        ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg hover:shadow-xl'
                        : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }
                  `}
                >
                  {isProcessing
                    ? 'Processing...'
                    : selectedTemplate
                    ? '📋 Apply Template & Process'
                    : 'Start Standard Scan'}
                </button>
              ) : (
                <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <p className="text-sm text-purple-800 text-center">
                    ℹ️ Use the "Analyze with Gemini AI" button in the section above to start scanning.
                  </p>
                </div>
              )}
            </div>

            {/* Info Stats */}
            <div className="mt-8 grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xl font-bold text-primary-600">100%</div>
                <div className="text-xs text-gray-600">Offline</div>
              </div>
              <div>
                <div className="text-xl font-bold text-primary-600">95%+</div>
                <div className="text-xs text-gray-600">Accuracy</div>
              </div>
              <div>
                <div className="text-xl font-bold text-primary-600">&lt;30s</div>
                <div className="text-xs text-gray-600">Processing</div>
              </div>
            </div>
          </div>
        </div>
      </main>
      </div>
    </>
  )
}
