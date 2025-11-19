/**
 * PDF Viewer with Interactive Entity Annotations
 * Displays PDF with overlay rectangles for detected entities
 * Click to toggle accept/reject, preview mode shows redactions
 */
import React, { useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Eye, EyeOff } from 'lucide-react'
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

interface EntityLocation {
  page: number
  rect: {
    x0: number
    y0: number
    x1: number
    y1: number
  }
}

interface Entity {
  entity_type: string
  text: string
  start: number
  end: number
  score: number
  accepted: boolean
  locations?: EntityLocation[]
  manual?: boolean
  _id?: string
}

interface PDFViewerProps {
  filePath: string
  entities: Entity[]
  onEntityToggle: (entityId: string) => void
  previewMode?: boolean
  onPreviewModeChange?: (enabled: boolean) => void
  onManualSelection?: (text: string, page: number, bbox: {x0: number, y0: number, x1: number, y1: number}) => void
}

// Entity type color mapping
const ENTITY_COLORS: Record<string, string> = {
  'PERSON': '#10b981',           // green
  'CODICE_FISCALE': '#ef4444',   // red
  'PHONE_NUMBER': '#3b82f6',     // blue
  'EMAIL_ADDRESS': '#8b5cf6',    // purple
  'IBAN': '#f59e0b',             // amber
  'IT_ADDRESS': '#ec4899',       // pink
  'DATE_TIME': '#06b6d4',        // cyan
  'LOCATION': '#14b8a6',         // teal
  'MANUAL': '#6366f1'            // indigo
}

export default function PDFViewerWithAnnotations({
  filePath,
  entities,
  onEntityToggle,
  previewMode = false,
  onPreviewModeChange,
  onManualSelection
}: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.2)
  const [pageWidth, setPageWidth] = useState<number>(0)
  const [pageHeight, setPageHeight] = useState<number>(0)

  // Manual selection state
  const [isDrawing, setIsDrawing] = useState<boolean>(false)
  const [drawStart, setDrawStart] = useState<{x: number, y: number} | null>(null)
  const [drawCurrent, setDrawCurrent] = useState<{x: number, y: number} | null>(null)
  const [manualBoxes, setManualBoxes] = useState<Array<{x: number, y: number, width: number, height: number}>>([])
  const [selectionMode, setSelectionMode] = useState<boolean>(false)
  const pdfContainerRef = useState<HTMLDivElement | null>(null)

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  const onPageLoadSuccess = (page: any) => {
    setPageWidth(page.width)
    setPageHeight(page.height)
  }

  // Group entities by page
  const entitiesByPage = entities.reduce((acc, entity) => {
    entity.locations?.forEach((location) => {
      if (!acc[location.page]) {
        acc[location.page] = []
      }
      acc[location.page].push({
        entity,
        location
      })
    })
    return acc
  }, {} as Record<number, any[]>)

  // Get entities for current page (0-indexed)
  const pageEntities = entitiesByPage[pageNumber - 1] || []

  // Handle zoom
  const handleZoomIn = () => setScale(Math.min(3.0, scale + 0.2))
  const handleZoomOut = () => setScale(Math.max(0.5, scale - 0.2))
  const handleZoomReset = () => setScale(1.2)

  // Handle page navigation
  const goToPrevPage = () => setPageNumber(Math.max(1, pageNumber - 1))
  const goToNextPage = () => setPageNumber(Math.min(numPages, pageNumber + 1))

  // Get entity color
  const getEntityColor = (entityType: string): string => {
    return ENTITY_COLORS[entityType] || '#6b7280' // gray as fallback
  }

  // Get entity count by acceptance state
  const acceptedCount = entities.filter(e => e.accepted).length
  const rejectedCount = entities.length - acceptedCount

  // Handle mouse events for drawing selection boxes
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!selectionMode || previewMode) return

    const svg = e.currentTarget
    const rect = svg.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setIsDrawing(true)
    setDrawStart({ x, y })
    setDrawCurrent({ x, y })
  }

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawing || !drawStart || !selectionMode) return

    const svg = e.currentTarget
    const rect = svg.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setDrawCurrent({ x, y })
  }

  const handleMouseUp = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawing || !drawStart || !drawCurrent || !selectionMode) return

    const width = Math.abs(drawCurrent.x - drawStart.x)
    const height = Math.abs(drawCurrent.y - drawStart.y)

    // Only create box if minimum size (avoid accidental clicks)
    if (width > 10 && height > 10) {
      const x = Math.min(drawStart.x, drawCurrent.x)
      const y = Math.min(drawStart.y, drawCurrent.y)

      // Convert screen coordinates to PDF coordinates
      const pdfX0 = x / scale
      const pdfY1 = pageHeight - (y / scale)  // Flip Y axis
      const pdfX1 = (x + width) / scale
      const pdfY0 = pageHeight - ((y + height) / scale)  // Flip Y axis

      // Call callback with PDF coordinates
      if (onManualSelection) {
        onManualSelection(
          '[Manual Selection]',
          pageNumber - 1,  // 0-indexed
          { x0: pdfX0, y0: pdfY0, x1: pdfX1, y1: pdfY1 }
        )
      }

      // Add to local manual boxes for visualization
      setManualBoxes(prev => [...prev, { x, y, width, height }])
    }

    setIsDrawing(false)
    setDrawStart(null)
    setDrawCurrent(null)
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b shadow-sm">
        {/* Page Navigation */}
        <div className="flex items-center gap-3">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
            title="Previous page"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <input
              type="number"
              value={pageNumber}
              onChange={(e) => {
                const page = parseInt(e.target.value)
                if (page >= 1 && page <= numPages) {
                  setPageNumber(page)
                }
              }}
              min={1}
              max={numPages}
              className="w-16 px-2 py-1 text-center border rounded"
            />
            <span className="text-sm text-gray-600">/ {numPages}</span>
          </div>

          <button
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
            title="Next page"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 rounded hover:bg-gray-100"
            title="Zoom out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>

          <button
            onClick={handleZoomReset}
            className="px-3 py-1 text-sm font-medium rounded hover:bg-gray-100"
            title="Reset zoom"
          >
            {Math.round(scale * 100)}%
          </button>

          <button
            onClick={handleZoomIn}
            className="p-2 rounded hover:bg-gray-100"
            title="Zoom in"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
        </div>

        {/* Selection Mode & Preview Mode Toggles */}
        <div className="flex items-center gap-2">
          {/* Selection Mode Toggle */}
          {onManualSelection && !previewMode && (
            <button
              onClick={() => setSelectionMode(!selectionMode)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
                ${selectionMode
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
              title={selectionMode ? 'Exit drawing mode' : 'Draw rectangles to select areas for redaction'}
            >
              {selectionMode ? (
                <>
                  <span className="text-lg">✏️</span>
                  <span>Drawing Mode ON</span>
                </>
              ) : (
                <>
                  <span className="text-lg">✏️</span>
                  <span>Enable Drawing</span>
                </>
              )}
            </button>
          )}

          {/* Preview Mode Toggle */}
          <button
            onClick={() => onPreviewModeChange?.(!previewMode)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
              ${previewMode
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            {previewMode ? (
              <>
                <Eye className="w-4 h-4" />
                <span>Preview Redactions</span>
              </>
            ) : (
              <>
                <EyeOff className="w-4 h-4" />
                <span>Review Mode</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 overflow-auto p-8">
        <div className="flex justify-center">
          <div className="relative inline-block bg-white shadow-2xl">
            <Document
              file={`file://${filePath}`}
              onLoadSuccess={onDocumentLoadSuccess}
              className="max-w-full"
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={false}
                onLoadSuccess={onPageLoadSuccess}
              />
            </Document>

            {/* Entity Overlays */}
            <svg
              className="absolute top-0 left-0"
              width={pageWidth * scale}
              height={pageHeight * scale}
              style={{ pointerEvents: selectionMode && !previewMode ? 'auto' : 'none', cursor: selectionMode ? 'crosshair' : 'default' }}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            >
              {pageEntities.map((item, idx) => {
                const { entity, location } = item
                const rect = location.rect

                // Convert PDF coordinates to canvas coordinates
                // PDF origin is bottom-left, canvas is top-left
                const x = rect.x0 * scale
                const y = (pageHeight - rect.y1) * scale  // Flip Y axis
                const width = (rect.x1 - rect.x0) * scale
                const height = (rect.y1 - rect.y0) * scale

                // Get color based on entity type
                const baseColor = getEntityColor(entity.entity_type)

                // Determine appearance based on mode and state
                let fillColor: string
                let fillOpacity: number
                let strokeColor: string
                let strokeWidth: number

                if (previewMode) {
                  // Preview mode: Show black boxes for accepted entities only
                  if (!entity.accepted) return null

                  fillColor = '#000000'
                  fillOpacity = 1.0
                  strokeColor = '#000000'
                  strokeWidth = 0
                } else {
                  // Review mode: Show colored overlays
                  fillColor = entity.accepted ? baseColor : '#ef4444' // red for rejected
                  fillOpacity = 0.25
                  strokeColor = entity.accepted ? baseColor : '#ef4444'
                  strokeWidth = 2
                }

                return (
                  <g key={`${entity._id || `${entity.start}-${entity.end}`}-${idx}`}>
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
                      fill={fillColor}
                      fillOpacity={fillOpacity}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      className="cursor-pointer transition-opacity hover:fill-opacity-40"
                      style={{ pointerEvents: previewMode ? 'none' : 'auto' }}
                      onClick={() => {
                        if (!previewMode && entity._id) {
                          console.log('👆 Clicked entity in PDF viewer:', {
                            _id: entity._id,
                            text: entity.text,
                            type: entity.entity_type
                          })
                          onEntityToggle(entity._id)
                        }
                      }}
                    />

                    {/* Show placeholder text in preview mode */}
                    {previewMode && (
                      <text
                        x={x + width / 2}
                        y={y + height / 2}
                        fill="white"
                        fontSize={Math.min(10 * scale, height * 0.6)}
                        fontWeight="bold"
                        textAnchor="middle"
                        dominantBaseline="middle"
                        style={{ pointerEvents: 'none' }}
                      >
                        [{entity.entity_type}]
                      </text>
                    )}

                    {/* Tooltip (only in review mode) */}
                    {!previewMode && (
                      <title>
                        {entity.entity_type}: "{entity.text}" ({Math.round(entity.score * 100)}%)
                        {'\n'}
                        Click to {entity.accepted ? 'reject' : 'accept'}
                      </title>
                    )}
                  </g>
                )
              })}

              {/* Draw manual selection boxes */}
              {manualBoxes.map((box, idx) => (
                <rect
                  key={`manual-box-${idx}`}
                  x={box.x}
                  y={box.y}
                  width={box.width}
                  height={box.height}
                  fill="#6366f1"
                  fillOpacity={0.3}
                  stroke="#6366f1"
                  strokeWidth={3}
                  strokeDasharray="5,5"
                />
              ))}

              {/* Current drawing rectangle (while dragging) */}
              {isDrawing && drawStart && drawCurrent && (
                <rect
                  x={Math.min(drawStart.x, drawCurrent.x)}
                  y={Math.min(drawStart.y, drawCurrent.y)}
                  width={Math.abs(drawCurrent.x - drawStart.x)}
                  height={Math.abs(drawCurrent.y - drawStart.y)}
                  fill="#6366f1"
                  fillOpacity={0.2}
                  stroke="#6366f1"
                  strokeWidth={2}
                  strokeDasharray="5,5"
                />
              )}
            </svg>
          </div>
        </div>
      </div>

      {/* Drawing Mode Banner */}
      {selectionMode && !previewMode && (
        <div className="px-4 py-3 bg-indigo-50 border-t border-indigo-200">
          <div className="text-sm text-indigo-900 text-center font-medium">
            <span className="text-lg mr-2">✏️</span>
            <strong>DRAWING MODE:</strong> Click and drag on the PDF to draw a rectangle around text you want to redact
          </div>
        </div>
      )}

      {/* Status Bar */}
      <div className="px-4 py-3 bg-white border-t">
        <div className="flex items-center justify-between">
          {/* Entity Legend */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-4 h-4 bg-green-500 border-2 border-green-600 opacity-40"></div>
              <span className="text-gray-700">
                Accepted: <strong>{acceptedCount}</strong>
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-4 h-4 bg-red-500 border-2 border-red-600 opacity-40"></div>
              <span className="text-gray-700">
                Rejected: <strong>{rejectedCount}</strong>
              </span>
            </div>
            {previewMode && (
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 bg-black"></div>
                <span className="text-gray-700">Redacted Area</span>
              </div>
            )}
          </div>

          {/* Page Info */}
          <div className="text-sm text-gray-600">
            {pageEntities.length} {pageEntities.length === 1 ? 'entity' : 'entities'} on this page
          </div>
        </div>
      </div>
    </div>
  )
}
