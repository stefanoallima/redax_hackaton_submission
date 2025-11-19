/**
 * Teaching Mode Page - AI-Guided Visual Template Learning
 * Users describe what fields to find, Gemini analyzes and annotates the template
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TemplateAnnotator } from '../components/TemplateAnnotator'
import {
  Upload,
  FileText,
  Brain,
  ArrowLeft,
  Info
} from 'lucide-react'

interface Region {
  id: string
  bbox: [number, number, number, number]
  field_name: string
  entity_type: string
  confidence: number
  user_label: string
}

export const TeachingModePage: React.FC = () => {
  const navigate = useNavigate()
  const [templateFile, setTemplateFile] = useState<File | null>(null)
  const [templateUrl, setTemplateUrl] = useState<string | null>(null)

  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.type.includes('pdf') && !file.type.includes('image')) {
      alert('Please upload a PDF or image file')
      return
    }

    setTemplateFile(file)

    // Create object URL for preview
    const url = URL.createObjectURL(file)
    setTemplateUrl(url)
  }

  // Handle save template
  const handleSaveTemplate = async (regions: Region[]) => {
    if (!templateFile) return

    try {
      console.log('Saving template with regions:', regions)

      // Call backend to save template
      const response = await window.electron.ipcRenderer.invoke('save-template', {
        template_id: `template_${Date.now()}`,
        cache_name: `cache_${templateFile.name}`,
        description: templateFile.name,
        regions: regions,
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 3600000).toISOString(), // 1 hour
        voice_command: 'Manual annotation'
      })

      if (response.status === 'success') {
        alert(`✅ Template saved successfully!\n\nTemplate ID: ${response.template_id}\n\nYou can now use this template for batch processing.`)
      } else {
        throw new Error(response.error || 'Failed to save template')
      }
    } catch (error: any) {
      console.error('Save template error:', error)
      alert(`❌ Error saving template: ${error.message}`)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-purple-50 to-blue-50">
      {/* Header */}
      <div className="flex-shrink-0 p-6 bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Redaction Templates Creation
                </h1>
                <p className="text-sm text-gray-600">
                  AI-guided template learning with Gemini
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto min-h-full">
          {!templateUrl ? (
            // File Upload Screen
            <div className="h-full flex items-center justify-center">
              <div className="max-w-2xl w-full">
                {/* Info Banner */}
                <div className="mb-6 p-6 bg-blue-50 border-2 border-blue-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <Info className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                    <div>
                      <h3 className="font-semibold text-blue-900 mb-2">
                        How Redaction Templates Creation Works
                      </h3>
                      <ol className="text-sm text-blue-800 space-y-2">
                        <li><strong>1. Describe Fields:</strong> Type what fields you want to find (e.g., "Find tenant names and phone numbers")</li>
                        <li><strong>2. AI Analysis:</strong> Gemini analyzes the document and identifies field locations</li>
                        <li><strong>3. Review & Adjust:</strong> Verify and refine the detected areas/text</li>
                        <li><strong>4. Save Template:</strong> Use for local offline Stadard Redaction</li>
                      </ol>
                    </div>
                  </div>
                </div>

                {/* Upload Card */}
                <div className="bg-white rounded-xl p-8 shadow-xl border-2 border-gray-200">
                  <label className="flex flex-col items-center gap-4 cursor-pointer hover:bg-gray-50 p-8 rounded-lg border-2 border-dashed border-gray-300 transition-colors">
                    <Upload className="w-16 h-16 text-purple-600" />
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-900 mb-1">
                        Upload Document (either an example or a blank template)
                      </p>
                      <p className="text-sm text-gray-600">
                        PDF or Image (no sensitive data)
                      </p>
                    </div>
                    <div className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium">
                      Choose File
                    </div>
                    <input
                      type="file"
                      accept=".pdf,image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>

                  {/* Example Templates */}
                  <div className="mt-6 p-4 bg-purple-50 rounded-lg">
                    <p className="text-xs font-semibold text-purple-900 mb-2">
                      💡 Example Templates:
                    </p>
                    <ul className="text-xs text-purple-800 space-y-1">
                      <li>• Lease agreement</li>
                      <li>• Medical intake form</li>
                      <li>• Bank statement template</li>
                      <li>• Employment contract</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Template Annotation Screen
            <div className="h-full">
              <TemplateAnnotator
                templateUrl={templateUrl}
                templateFile={templateFile || undefined}
                onSaveTemplate={handleSaveTemplate}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
