/**
 * Template Annotator - Text-Guided Visual Selection
 * User clicks PDF regions, describes them via text, Gemini classifies
 */
import React, { useState, useRef, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Save, Trash2, Eye, CheckCircle2, ZoomIn, ZoomOut, Send, MessageSquare } from 'lucide-react'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Configure PDF.js worker - use local bundled worker for offline operation
// In production (Electron), use the bundled worker from the app directory
// In development, Vite serves it from the public directory
if (import.meta.env.DEV) {
  // Development: served from public directory by Vite dev server
  pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'
} else {
  // Production: bundled in dist/renderer directory
  pdfjs.GlobalWorkerOptions.workerSrc = './pdf.worker.min.mjs'
}

interface Region {
  id: string
  bbox: [number, number, number, number] // [x, y, width, height] in PDF units
  field_name: string
  entity_type: string
  confidence: number
  user_label: string // What user said via voice
}

interface TemplateAnnotatorProps {
  templateUrl: string // Blob URL for PDF preview
  templateFile?: File // Original file for accessing file path
  onSaveTemplate: (regions: Region[]) => void
}

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  timestamp: Date
}

export const TemplateAnnotator: React.FC<TemplateAnnotatorProps> = ({
  templateUrl,
  templateFile,
  onSaveTemplate
}) => {
  const [regions, setRegions] = useState<Region[]>([])
  const [isSelecting, setIsSelecting] = useState(false)
  const [isNaming, setIsNaming] = useState(false)
  const [currentRegion, setCurrentRegion] = useState<Partial<Region> | null>(null)
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null)

  // Chat state (replaces voice conversation)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [textInput, setTextInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // PDF state
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [isPdf, setIsPdf] = useState<boolean>(false)
  const [pageWidth, setPageWidth] = useState<number>(0)
  const [pageHeight, setPageHeight] = useState<number>(0)

  // Drawing state
  const [isDrawing, setIsDrawing] = useState<boolean>(false)
  const [drawStart, setDrawStart] = useState<{x: number, y: number} | null>(null)
  const [drawCurrent, setDrawCurrent] = useState<{x: number, y: number} | null>(null)

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null)

  // Detect if file is PDF or image
  useEffect(() => {
    // Check if the blob URL is a PDF by trying to fetch it
    fetch(templateUrl)
      .then(response => response.blob())
      .then(blob => {
        const isPdfFile = blob.type === 'application/pdf'
        setIsPdf(isPdfFile)
        console.log(`📄 Template type: ${isPdfFile ? 'PDF' : 'Image'}`)
      })
      .catch(err => {
        console.error('Failed to detect file type:', err)
        setIsPdf(false)
      })
  }, [templateUrl])

  // PDF handlers
  const [pdfError, setPdfError] = useState<string | null>(null)

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setPdfError(null)
    console.log(`📄 PDF loaded: ${numPages} pages`)
  }

  const onDocumentLoadError = (error: Error) => {
    console.error('❌ PDF load error:', error)
    setPdfError(error.message || 'Failed to load PDF. Please try a different file.')
  }

  const onPageLoadSuccess = (page: any) => {
    setPageWidth(page.width)
    setPageHeight(page.height)
    console.log(`📄 Page ${pageNumber} loaded: ${page.width}x${page.height}`)
  }

  // Load image into canvas (for non-PDF files)
  useEffect(() => {
    if (isPdf) return // Skip if PDF

    const img = new Image()
    img.src = templateUrl
    img.onload = () => {
      if (canvasRef.current) {
        imageRef.current = img
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')
        if (ctx) {
          canvas.width = img.width
          canvas.height = img.height
          ctx.drawImage(img, 0, 0)
          drawRegions(ctx)
        }
      }
    }
  }, [templateUrl, isPdf])

  // Draw existing regions
  const drawRegions = (ctx: CanvasRenderingContext2D) => {
    regions.forEach(region => {
      ctx.strokeStyle = region.id === selectedRegionId ? '#10B981' : '#8B5CF6'
      ctx.lineWidth = 3
      ctx.strokeRect(...region.bbox)

      // Label
      ctx.fillStyle = region.id === selectedRegionId ? '#10B981' : '#8B5CF6'
      ctx.fillRect(region.bbox[0], region.bbox[1] - 25, 200, 25)
      ctx.fillStyle = 'white'
      ctx.font = '14px sans-serif'
      ctx.fillText(region.field_name || region.user_label, region.bbox[0] + 5, region.bbox[1] - 8)
    })
  }

  // PDF Mouse Handlers (for SVG overlay)
  const handlePDFMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    console.log('🖱️ Mouse down - isSelecting:', isSelecting)
    if (!isSelecting) return

    const svg = e.currentTarget
    const rect = svg.getBoundingClientRect()
    const x = (e.clientX - rect.left) / scale
    const y = (e.clientY - rect.top) / scale

    console.log('✅ Starting draw at:', { x, y, scale })
    setIsDrawing(true)
    setDrawStart({ x, y })
  }

  const handlePDFMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawing || !drawStart) return

    const svg = e.currentTarget
    const rect = svg.getBoundingClientRect()
    const x = (e.clientX - rect.left) / scale
    const y = (e.clientY - rect.top) / scale

    setDrawCurrent({ x, y })
  }

  const handlePDFMouseUp = (e: React.MouseEvent<SVGSVGElement>) => {
    console.log('🖱️ Mouse up - isDrawing:', isDrawing, 'drawStart:', drawStart, 'drawCurrent:', drawCurrent)

    if (!isDrawing || !drawStart) {
      console.log('❌ Not drawing or no start point')
      return
    }

    const svg = e.currentTarget
    const rect = svg.getBoundingClientRect()
    const endX = (e.clientX - rect.left) / scale
    const endY = (e.clientY - rect.top) / scale

    const width = Math.abs(endX - drawStart.x)
    const height = Math.abs(endY - drawStart.y)

    console.log('📐 Box dimensions:', { width, height })

    if (width > 10 && height > 10) {
      const bbox: [number, number, number, number] = [
        Math.min(drawStart.x, endX),
        Math.min(drawStart.y, endY),
        width,
        height
      ]

      console.log('✅ Creating region with bbox:', bbox)

      // Create new region (awaiting voice name)
      const newRegion = {
        id: `region_${Date.now()}`,
        bbox,
        field_name: '',
        entity_type: 'UNKNOWN',
        confidence: 0,
        user_label: ''
      }

      setCurrentRegion(newRegion)
      setIsNaming(true)
      console.log('✅ Region created, ready for voice input')
    } else {
      console.log('❌ Box too small:', { width, height })
    }

    setIsDrawing(false)
    setDrawStart(null)
    setDrawCurrent(null)
    setIsSelecting(false)
  }

  // Canvas Mouse Handlers (for images)
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isSelecting) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setStartPos({ x, y })
  }

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isSelecting || !startPos) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const endX = e.clientX - rect.left
    const endY = e.clientY - rect.top

    const bbox: [number, number, number, number] = [
      Math.min(startPos.x, endX),
      Math.min(startPos.y, endY),
      Math.abs(endX - startPos.x),
      Math.abs(endY - startPos.y)
    ]

    // Create new region (awaiting voice name)
    setCurrentRegion({
      id: `region_${Date.now()}`,
      bbox,
      field_name: '',
      entity_type: 'UNKNOWN',
      confidence: 0,
      user_label: ''
    })

    setIsSelecting(false)
    setIsNaming(true)
    setStartPos(null)
  }

  // Manual text input state (fallback for voice)
  const [manualInput, setManualInput] = useState('')
  const [templateFilePath, setTemplateFilePath] = useState<string | null>(null)

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle sending text message
  const handleSendMessage = async () => {
    if (!textInput.trim() || isProcessing) return

    const userText = textInput.trim()
    setTextInput('')
    setIsProcessing(true)

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      text: userText,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      // Get AI response
      const response = await handleAIConversation(userText)

      // Add AI response
      const aiMessage: ChatMessage = {
        role: 'assistant',
        text: response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error processing message:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsProcessing(false)
    }
  }

  // Convert blob URL to file path for Gemini API
  useEffect(() => {
    if (!templateUrl) return

    // For now, we'll need to save the blob as a temp file
    // The actual file should be passed from TeachingModePage
    console.log('📄 Template URL:', templateUrl)
  }, [templateUrl])

  // Handle AI conversation
  const handleAIConversation = async (userMessage: string): Promise<string> => {
    console.log('🤖 AI processing user request:', userMessage)

    // Check if PDF page is loaded with dimensions
    if (isPdf && (pageWidth === 0 || pageHeight === 0)) {
      console.warn('⚠️ PDF page dimensions not loaded yet')
      return `Please wait for the PDF to fully load before using AI analysis. The page dimensions are needed to map coordinates correctly.`
    }

    // Check if we have the file path (needed for Gemini scan)
    const filePath = (templateFile as any)?.path // Electron File objects have .path property

    if (!filePath) {
      console.warn('⚠️ No file path available for Gemini scan')
      return `I can't analyze the template yet. Please make sure you uploaded a file from your computer (not a URL). You can still use manual selection to draw rectangles around the fields you want.`
    }

    try {
      // Build prompt for template analysis
      const analysisPrompt = `
You are analyzing a BLANK TEMPLATE document (not a filled document) for PII field detection.

User request: "${userMessage}"

Task:
1. Identify ALL fields in this blank template that match the user's requested entity types
2. For each field, provide the exact bounding box coordinates [x0, y0, x1, y1]
3. Classify each field's entity type (PERSON, US_SSN, PHONE_NUMBER, EMAIL_ADDRESS, IT_ADDRESS, DATE_TIME, etc.)
4. Return fields with high confidence (>0.8)

Important:
- This is a BLANK TEMPLATE - look for field labels, placeholders, and form fields
- Detect based on field names like "Tenant Name:", "SSN:", "Phone:", "Email:", etc.
- Be thorough - find ALL instances of requested entity types

Return only detected fields, no other text.
`

      console.log('📂 Using file path for template teaching:', filePath)
      console.log('🎤 Voice command:', userMessage)

      // Call Teach Template API to get bounding boxes
      const result = await window.electron.ipcRenderer.invoke('teach-template', {
        file_path: filePath, // Use real file path, not blob URL
        voice_command: userMessage, // User's request
        description: 'Teaching Mode template'
      })

      console.log('🤖 Teach Template result:', result)

      if (result.status === 'error') {
        throw new Error(result.error || 'Template teaching failed')
      }

      // Convert template regions (0-1000 scale) to PDF pixel coordinates
      const detectedRegions: Region[] = (result.regions || []).map((region: any, idx: number) => {
        if (!region.bbox || region.bbox.length !== 4) {
          console.warn('⚠️ Region missing bbox:', region)
          return null
        }

        // bbox from Gemini is [ymin, xmin, ymax, xmax] in 0-1000 normalized scale
        const [ymin, xmin, ymax, xmax] = region.bbox

        // Calculate separate scale factors for X and Y axes
        // (PDFs are rarely square, so we need independent scaling)
        // CRITICAL FIX: Check if page dimensions are loaded, otherwise skip this region
        if (pageWidth === 0 || pageHeight === 0) {
          console.warn('⚠️ Page dimensions not loaded yet, cannot convert coordinates')
          return null
        }

        const scaleX = pageWidth / 1000
        const scaleY = pageHeight / 1000

        // CRITICAL: PDFs use bottom-left origin (0,0 at bottom-left)
        // SVG/web uses top-left origin (0,0 at top-left)
        // We need to flip the Y coordinate: y_svg = pageHeight - y_pdf
        // Since Gemini gives us normalized coordinates (0-1000), we flip after scaling

        const convertedBbox: [number, number, number, number] = [
          xmin * scaleX,                    // X position (left edge)
          ymin * scaleY,                    // Y position (top edge) - Using top-left origin since react-pdf uses standard web coordinates
          (xmax - xmin) * scaleX,          // width
          (ymax - ymin) * scaleY           // height
        ]

        console.log('📍 Gemini bbox conversion:')
        console.log('  Input (0-1000 scale):', { ymin, xmin, ymax, xmax })
        console.log('  Page dimensions:', { pageWidth, pageHeight })
        console.log('  Scale factors:', { scaleX, scaleY })
        console.log('  Output (pixel coords):', {
          x: convertedBbox[0],
          y: convertedBbox[1],
          width: convertedBbox[2],
          height: convertedBbox[3]
        })

        return {
          id: `taught_${Date.now()}_${idx}`,
          bbox: convertedBbox,
          field_name: region.field_name || region.entity_type,
          entity_type: region.entity_type,
          confidence: region.confidence || 0.9,
          user_label: region.field_name || `AI detected ${region.entity_type}`
        }
      }).filter((r: Region | null) => r !== null)

      console.log(`✅ Detected ${detectedRegions.length} regions with bounding boxes`)

      // Check if regions were found but without proper coordinates
      const regionsWithoutBbox = (result.regions || []).filter((r: any) =>
        !r.bbox || r.bbox.length !== 4
      )

      console.log(`📊 Total regions found: ${result.regions?.length || 0}`)
      console.log(`⚠️ Regions without bbox: ${regionsWithoutBbox.length}`)

      // Add all detected regions with coordinates
      setRegions(prev => [...prev, ...detectedRegions])

      // Generate conversational response
      const entityTypeCounts: Record<string, number> = {}
      detectedRegions.forEach(r => {
        entityTypeCounts[r.entity_type] = (entityTypeCounts[r.entity_type] || 0) + 1
      })

      const countSummary = Object.entries(entityTypeCounts)
        .map(([type, count]) => `${count} ${type.replace(/_/g, ' ')}`)
        .join(', ')

      // If we have regions with coordinates, show success
      if (detectedRegions.length > 0) {
        return `Great! I found ${detectedRegions.length} fields with coordinates: ${countSummary}. I've highlighted them on the PDF for you.`
      }

      // If regions were found but without coordinates
      if (regionsWithoutBbox.length > 0) {
        const detectedFields = regionsWithoutBbox
          .map((r: any) => `"${r.field_name || r.entity_type}"`)
          .slice(0, 3)
          .join(', ')

        const moreCount = regionsWithoutBbox.length > 3 ? ` and ${regionsWithoutBbox.length - 3} more` : ''

        return `I found ${regionsWithoutBbox.length} field labels: ${detectedFields}${moreCount}. However, I couldn't determine their exact positions on the page. Please make sure you uploaded a BLANK template with clear field labels like "Name: ____" or "Email: ____". You can also draw rectangles manually on the PDF.`
      }

      // No regions found at all
      return `I couldn't find any fields matching your request in this template. Try describing them differently (e.g., "Find name, email, and phone number fields"), or use manual selection to draw rectangles around the fields you want.`
    } catch (error: any) {
      console.error('❌ AI conversation error:', error)
      return `Sorry, I encountered an error: ${error.message}. You can still use manual selection to annotate the template.`
    }
  }

  // Handle voice transcript for naming
  const handleVoiceTranscript = async (text: string, isFinal: boolean) => {
    if (!isFinal || !currentRegion) return

    console.log('🎤 User named region via voice:', text)
    await processFieldName(text)
  }

  // Handle manual text input
  const handleManualSubmit = async () => {
    if (!manualInput.trim() || !currentRegion) return

    console.log('⌨️ User named region via text:', manualInput)
    await processFieldName(manualInput)
    setManualInput('')
  }

  // Process field name (from voice or text)
  const processFieldName = async (text: string) => {
    if (!currentRegion) return

    // Simple classification based on keywords (no API call needed)
    let entityType = 'PERSON'
    const lowerText = text.toLowerCase()

    if (lowerText.includes('ssn') || lowerText.includes('social security')) {
      entityType = 'US_SSN'
    } else if (lowerText.includes('phone') || lowerText.includes('tel')) {
      entityType = 'PHONE_NUMBER'
    } else if (lowerText.includes('email') || lowerText.includes('e-mail')) {
      entityType = 'EMAIL_ADDRESS'
    } else if (lowerText.includes('address') || lowerText.includes('street')) {
      entityType = 'IT_ADDRESS'
    } else if (lowerText.includes('date') || lowerText.includes('birth')) {
      entityType = 'DATE_TIME'
    } else if (lowerText.includes('name') || lowerText.includes('tenant') || lowerText.includes('landlord')) {
      entityType = 'PERSON'
    }

    // Add region with classification
    const newRegion: Region = {
      ...currentRegion as Region,
      user_label: text,
      field_name: text.toLowerCase().replace(/\s+/g, '_'),
      entity_type: entityType,
      confidence: 0.9
    }

    console.log('✅ Adding region:', newRegion)
    setRegions(prev => [...prev, newRegion])
    setCurrentRegion(null)
    setIsNaming(false)

    // Redraw canvas for images
    if (!isPdf) {
      const canvas = canvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')
        if (ctx && imageRef.current) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
          ctx.drawImage(imageRef.current, 0, 0)
          drawRegions(ctx)
        }
      }
    }
  }

  // Delete region
  const handleDeleteRegion = (regionId: string) => {
    setRegions(prev => prev.filter(r => r.id !== regionId))
    setSelectedRegionId(null)
  }

  // Save template
  const handleSave = () => {
    if (regions.length === 0) {
      alert('Please annotate at least one region')
      return
    }
    onSaveTemplate(regions)
  }

  return (
    <div className="grid grid-cols-2 gap-6 min-h-[600px]">
      {/* LEFT: AI Text Conversation */}
      <div className="col-span-1 flex flex-col h-[calc(100vh-200px)] min-h-[600px] border border-gray-200 rounded-lg">
        {/* Chat Header */}
        <div className="flex items-center gap-2 p-4 border-b border-gray-200 bg-gray-50">
          <MessageSquare className="w-5 h-5 text-purple-600" />
          <h3 className="font-semibold">AI Assistant</h3>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>Describe what fields you want to find...</p>
              <p className="text-sm mt-2">Example: "Find tenant names and phone numbers"</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="text-sm">{msg.text}</p>
                  <p className="text-xs mt-1 opacity-70">
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your request..."
              disabled={!templateUrl || isProcessing}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={handleSendMessage}
              disabled={!templateUrl || isProcessing || !textInput.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isProcessing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Send</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT: PDF Viewer (larger) */}
      <div className="col-span-1 space-y-4 overflow-y-auto max-h-[calc(100vh-200px)]">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Template Annotation</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setIsSelecting(!isSelecting)}
              className={`
                px-4 py-2 rounded-lg font-medium transition-colors
                ${isSelecting
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }
              `}
            >
              {isSelecting ? '🎯 Click to Select Region' : '✏️ Start Selecting'}
            </button>

            <button
              onClick={handleSave}
              disabled={regions.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              Save Template
            </button>
          </div>
        </div>

        {/* PDF or Canvas Viewer */}
        <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-gray-50">
          {isPdf ? (
            // PDF Viewer with SVG Overlay
            <div className="relative inline-block" ref={containerRef}>
              <Document
                file={templateUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <div className="flex items-center justify-center p-8">
                    <div className="text-center">
                      <div className="inline-block w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-2" />
                      <p className="text-sm text-gray-600">Loading PDF...</p>
                    </div>
                  </div>
                }
                error={
                  pdfError ? (
                    <div className="p-8 text-center">
                      <div className="text-red-600 mb-2">⚠️ Failed to load PDF</div>
                      <p className="text-sm text-gray-600">{pdfError}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        Make sure the file is a valid PDF and try uploading again.
                      </p>
                    </div>
                  ) : undefined
                }
                className="pdf-document"
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  onLoadSuccess={onPageLoadSuccess}
                  className="pdf-page"
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                />
              </Document>

              {/* SVG Overlay for Drawing */}
              <svg
                className={`absolute top-0 left-0 ${isSelecting ? 'cursor-crosshair' : 'cursor-default'}`}
                width={pageWidth * scale}
                height={pageHeight * scale}
                onMouseDown={handlePDFMouseDown}
                onMouseMove={handlePDFMouseMove}
                onMouseUp={handlePDFMouseUp}
                style={{ pointerEvents: (isSelecting && !isNaming) ? 'all' : 'none' }}
              >
                {/* Existing regions with labels */}
                {regions.map(region => (
                  <g key={region.id}>
                    <rect
                      x={region.bbox[0] * scale}
                      y={region.bbox[1] * scale}
                      width={region.bbox[2] * scale}
                      height={region.bbox[3] * scale}
                      fill="rgba(139, 92, 246, 0.2)"
                      stroke={selectedRegionId === region.id ? '#10B981' : '#8B5CF6'}
                      strokeWidth="3"
                      className="cursor-pointer"
                      onClick={() => setSelectedRegionId(region.id)}
                    />
                    {/* Label on rectangle */}
                    <text
                      x={region.bbox[0] * scale + 5}
                      y={region.bbox[1] * scale + 18}
                      fill="#4C1D95"
                      fontSize="14"
                      fontWeight="bold"
                      className="pointer-events-none"
                    >
                      {region.user_label}
                    </text>
                    <text
                      x={region.bbox[0] * scale + 5}
                      y={region.bbox[1] * scale + 35}
                      fill="#6B21A8"
                      fontSize="11"
                      className="pointer-events-none"
                    >
                      {region.entity_type} • {Math.round(region.confidence * 100)}%
                    </text>
                  </g>
                ))}

                {/* Current drawing rectangle */}
                {isDrawing && drawStart && drawCurrent && (
                  <rect
                    x={Math.min(drawStart.x, drawCurrent.x) * scale}
                    y={Math.min(drawStart.y, drawCurrent.y) * scale}
                    width={Math.abs(drawCurrent.x - drawStart.x) * scale}
                    height={Math.abs(drawCurrent.y - drawStart.y) * scale}
                    fill="rgba(99, 102, 241, 0.3)"
                    stroke="#6366F1"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                  />
                )}

                {/* Pending region (waiting for name) */}
                {currentRegion && currentRegion.bbox && (
                  <g>
                    <rect
                      x={currentRegion.bbox[0] * scale}
                      y={currentRegion.bbox[1] * scale}
                      width={currentRegion.bbox[2] * scale}
                      height={currentRegion.bbox[3] * scale}
                      fill="rgba(168, 85, 247, 0.4)"
                      stroke="#A855F7"
                      strokeWidth="4"
                      strokeDasharray="10,5"
                      className="animate-pulse"
                    />
                    <text
                      x={currentRegion.bbox[0] * scale + 10}
                      y={currentRegion.bbox[1] * scale - 10}
                      fill="#A855F7"
                      fontSize="16"
                      fontWeight="bold"
                      className="animate-pulse"
                    >
                      ⚡ TYPE NAME BELOW →
                    </text>
                  </g>
                )}
              </svg>

              {/* Zoom Controls */}
              <div className="absolute top-4 right-4 flex gap-2">
                <button
                  onClick={() => setScale(s => Math.max(0.5, s - 0.2))}
                  className="p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 shadow"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setScale(s => Math.min(2.0, s + 0.2))}
                  className="p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 shadow"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            // Canvas for Images
            <canvas
              ref={canvasRef}
              onMouseDown={handleCanvasMouseDown}
              onMouseUp={handleCanvasMouseUp}
              className={`max-w-full ${isSelecting ? 'cursor-crosshair' : 'cursor-default'}`}
            />
          )}
        </div>

        {/* Instructions */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">📋 How to Annotate:</h4>
          <ol className="text-xs text-blue-800 space-y-1">
            <li>1. Talk to AI or click "Start Selecting" to manually draw regions</li>
            <li>2. For manual: Click and drag to select a field</li>
            <li>3. Type what the field represents</li>
            <li>4. All regions appear directly on the PDF with labels</li>
            <li>5. Click "Save Template" when done</li>
          </ol>
        </div>

        {/* Floating Manual Input (when user draws a region) */}
        {isNaming && currentRegion && (
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 p-6 rounded-xl bg-gradient-to-br from-purple-50 to-indigo-50 border-4 border-purple-500 shadow-2xl animate-pulse w-96">
            <h4 className="font-bold mb-3 text-lg text-purple-900">
              ⚡ Name This Field
            </h4>
            <p className="text-sm mb-4 font-medium text-purple-800">
              Type what this manually selected field represents:
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={manualInput}
                onChange={(e) => setManualInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') handleManualSubmit()
                }}
                placeholder="e.g., tenant name, SSN, phone..."
                className="flex-1 px-4 py-3 rounded-lg border-2 border-purple-300 bg-white focus:border-purple-500 focus:outline-none text-sm"
                autoFocus
              />
              <button
                onClick={handleManualSubmit}
                disabled={!manualInput.trim()}
                className={`
                  px-6 py-3 rounded-lg font-semibold text-sm transition-colors
                  ${manualInput.trim()
                    ? 'bg-purple-600 text-white hover:bg-purple-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }
                `}
              >
                Add
              </button>
            </div>
          </div>
        )}

        {/* Region count badge */}
        {regions.length > 0 && (
          <div className="p-3 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg">
            <p className="text-sm font-semibold text-green-900">
              ✅ {regions.length} region{regions.length !== 1 ? 's' : ''} detected (visible on PDF)
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
