/**
 * Type definitions for IPC communication between Electron and Python backend
 * Replaces `any` types with proper TypeScript interfaces for type safety
 */

export interface DetectionConfig {
  depth: 'fast' | 'balanced' | 'thorough' | 'maximum'
  focusAreas: string[]
  customKeywords: string[]
  enableLLM: boolean
  enableVisual: boolean
}

export interface PIIEntity {
  entity_type: string
  text: string
  start: number
  end: number
  score: number
  accepted?: boolean
  manual?: boolean
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

export interface ProcessDocumentCommand {
  action: 'process_document'
  file_path: string
  config: DetectionConfig
}

export interface ExportRedactedCommand {
  action: 'export_redacted'
  file_path: string
  entities: PIIEntity[]
  export_txt: boolean
}

export type IPCCommand = ProcessDocumentCommand | ExportRedactedCommand

// Response types
export interface ProcessDocumentResponse {
  status: 'success' | 'error'
  entities?: PIIEntity[]
  summary?: {
    total: number
    byType: Record<string, number>
  }
  full_text?: string
  metadata?: Record<string, any>
  file_path?: string
  file_type?: string
  error?: string
}

export interface ExportRedactedResponse {
  status: 'success' | 'error'
  output_path?: string
  mapping_table_path?: string
  txt_output_path?: string
  entities_redacted?: number
  unique_entities?: number
  error?: string
}
