/**
 * Onboarding Wizard - First-Time User Experience
 * Guides users through their first document redaction
 */
import React, { useState } from 'react'
import { X, ArrowRight, ArrowLeft, Check, FileText, Eye, Download, Sparkles } from 'lucide-react'

interface OnboardingStep {
  id: string
  title: string
  description: string
  content: React.ReactNode
}

interface OnboardingWizardProps {
  onComplete: () => void
  onSkip: () => void
}

export default function OnboardingWizard({ onComplete, onSkip }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [sampleDocProcessed, setSampleDocProcessed] = useState(false)

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete()
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleProcessSample = () => {
    // Simulate processing
    setTimeout(() => {
      setSampleDocProcessed(true)
    }, 2000)
  }

  const STEPS: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to CodiceCivile Redact',
      description: 'Let\'s redact your first document in 3 easy steps',
      content: (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-12 h-12 text-primary-600" />
          </div>
          <h2 className="text-3xl font-bold mb-4">Welcome!</h2>
          <p className="text-gray-600 max-w-md mx-auto mb-8">
            CodiceCivile Redact uses AI to automatically detect and redact personal information
            in Italian legal documents. Let us show you how it works.
          </p>
          <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="font-semibold mb-1">1. Upload</h3>
              <p className="text-sm text-gray-600">Select your document</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Eye className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="font-semibold mb-1">2. Review</h3>
              <p className="text-sm text-gray-600">Verify detections</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Download className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-semibold mb-1">3. Export</h3>
              <p className="text-sm text-gray-600">Download redacted PDF</p>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'sample',
      title: 'Try it with a sample document',
      description: 'Process a sample Italian legal document to see how it works',
      content: (
        <div className="py-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-gray-50 rounded-lg p-8 mb-6">
              <div className="flex items-start gap-4">
                <FileText className="w-12 h-12 text-gray-400" />
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-2">
                    Contratto_Lavoro_Sample.pdf
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Sample employment contract • 3 pages • Contains typical PII
                  </p>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-500">Expected PII:</div>
                      <div className="font-medium">12-15 entities</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Processing time:</div>
                      <div className="font-medium">~15 seconds</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Detection mode:</div>
                      <div className="font-medium">Balanced</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {!sampleDocProcessed ? (
              <div className="text-center">
                <button
                  onClick={handleProcessSample}
                  className="px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-semibold text-lg"
                >
                  Process Sample Document
                </button>
                <p className="text-sm text-gray-500 mt-3">
                  This will take about 15 seconds
                </p>
              </div>
            ) : (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Check className="w-6 h-6 text-green-600" />
                  <h4 className="font-semibold text-green-900">Processing Complete!</h4>
                </div>
                <p className="text-sm text-green-800 mb-4">
                  Detected 14 PII entities: 4 names, 3 addresses, 2 Codice Fiscale,
                  3 phone numbers, 1 email, 1 IBAN
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleNext}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                  >
                    Review Detections →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )
    },
    {
      id: 'review',
      title: 'Review and verify detected PII',
      description: 'Accept or reject each detection before exporting',
      content: (
        <div className="py-8">
          <div className="max-w-3xl mx-auto">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h4 className="font-semibold text-blue-900 mb-2">How to review:</h4>
              <ul className="space-y-2 text-sm text-blue-800">
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-green-600 mt-0.5" />
                  <span><strong>Green:</strong> Entity will be redacted</span>
                </li>
                <li className="flex items-start gap-2">
                  <X className="w-4 h-4 text-red-600 mt-0.5" />
                  <span><strong>Red:</strong> Entity will be ignored</span>
                </li>
                <li className="flex items-start gap-2">
                  <ArrowRight className="w-4 h-4 text-blue-600 mt-0.5" />
                  <span>Click any entity to toggle accept/reject</span>
                </li>
                <li className="flex items-start gap-2">
                  <ArrowRight className="w-4 h-4 text-blue-600 mt-0.5" />
                  <span>Use bulk actions to accept/reject all at once</span>
                </li>
              </ul>
            </div>

            {/* Mock Entity List */}
            <div className="bg-white rounded-lg border p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold">Detected Entities (14)</h4>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-sm border border-green-600 text-green-600 rounded hover:bg-green-50">
                    Accept All
                  </button>
                  <button className="px-3 py-1 text-sm border border-red-600 text-red-600 rounded hover:bg-red-50">
                    Reject All
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                {[
                  { type: 'PERSON', text: 'Mario Rossi', accepted: true },
                  { type: 'CODICE_FISCALE', text: 'RSSMRA80A01H501X', accepted: true },
                  { type: 'EMAIL', text: 'mario.rossi@email.it', accepted: true },
                  { type: 'PHONE', text: '+39 02 1234567', accepted: false }
                ].map((entity, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center justify-between p-3 border-l-4 rounded ${
                      entity.accepted
                        ? 'border-green-500 bg-green-50'
                        : 'border-red-500 bg-red-50'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-sm">{entity.text}</div>
                      <div className="text-xs text-gray-600">{entity.type}</div>
                    </div>
                    <div className="flex gap-1">
                      <button className={`p-1 rounded ${entity.accepted ? 'bg-green-200' : ''}`}>
                        <Check className="w-4 h-4" />
                      </button>
                      <button className={`p-1 rounded ${!entity.accepted ? 'bg-red-200' : ''}`}>
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
                <div className="text-center text-sm text-gray-500 py-2">
                  + 10 more entities...
                </div>
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <p className="text-sm text-purple-800">
                <strong>Pro Tip:</strong> Hover over any entity to see its context in the document.
                You can also edit entity types by clicking on them.
              </p>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'export',
      title: 'Export your redacted document',
      description: 'Generate a PDF with redacted information',
      content: (
        <div className="py-8">
          <div className="max-w-2xl mx-auto text-center">
            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Download className="w-12 h-12 text-green-600" />
            </div>

            <h2 className="text-2xl font-bold mb-4">You're all set!</h2>
            <p className="text-gray-600 mb-8">
              Your redacted document is ready to download. All personal information
              has been replaced with semantic placeholders like [PERSONA_A], [INDIRIZZO_1], etc.
            </p>

            <div className="bg-gray-50 rounded-lg p-6 mb-8">
              <div className="grid grid-cols-2 gap-6">
                <div className="text-left">
                  <div className="text-sm text-gray-600 mb-1">Original Document:</div>
                  <div className="font-medium">Contratto_Lavoro_Sample.pdf</div>
                </div>
                <div className="text-left">
                  <div className="text-sm text-gray-600 mb-1">Redacted File:</div>
                  <div className="font-medium">Contratto_Lavoro_Sample_REDACTED.pdf</div>
                </div>
                <div className="text-left">
                  <div className="text-sm text-gray-600 mb-1">Entities Redacted:</div>
                  <div className="font-medium">13 of 14 detected</div>
                </div>
                <div className="text-left">
                  <div className="text-sm text-gray-600 mb-1">Processing Time:</div>
                  <div className="font-medium">16 seconds</div>
                </div>
              </div>
            </div>

            <button
              onClick={handleNext}
              className="px-8 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold text-lg mb-4 transition-all"
              aria-label="Continue to complete the onboarding tutorial"
            >
              <Download className="w-5 h-5 inline mr-2" />
              Download Redacted PDF
            </button>

            <p className="text-sm text-gray-500">
              <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium mb-2">
                Demo Mode
              </span>
              <br />
              This is a simulated download. In real use, clicking here will download your redacted PDF.
            </p>
          </div>
        </div>
      )
    },
    {
      id: 'complete',
      title: 'Tutorial complete!',
      description: 'You\'re ready to redact real documents',
      content: (
        <div className="py-12 text-center">
          <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-12 h-12 text-primary-600" />
          </div>

          <h2 className="text-3xl font-bold mb-4">
            Congratulations! 🎉
          </h2>
          <p className="text-gray-600 max-w-md mx-auto mb-8">
            You've successfully completed your first redaction.
            You're now ready to start processing real documents.
          </p>

          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-8 max-w-2xl mx-auto mb-8">
            <h3 className="font-semibold text-lg mb-4">What's next?</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-semibold mb-2">📄 Upload your documents</h4>
                <p className="text-sm text-gray-600">
                  Start redacting your real legal documents with the same easy workflow
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-semibold mb-2">⚙️ Customize settings</h4>
                <p className="text-sm text-gray-600">
                  Adjust detection depth, focus areas, and custom keywords
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-semibold mb-2">🔍 Customise the learning redaction database</h4>
                <p className="text-sm text-gray-600">
                  All redacted terms/words can be added to the local learning redaction database so to always redact them locally (i.e. personal bank account, phone number)
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-semibold mb-2">💬 Create templated redaction</h4>
                <p className="text-sm text-gray-600">
                  Use templated redaction of file with same layout/structure like invoices.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-4">
            <button
              onClick={onComplete}
              className="px-8 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-semibold text-lg"
            >
              Start Redacting
            </button>
            <button
              onClick={onComplete}
              className="px-8 py-4 border-2 border-gray-300 rounded-lg hover:bg-gray-50 font-semibold text-lg"
            >
              View Documentation
            </button>
          </div>
        </div>
      )
    }
  ]

  const currentStepData = STEPS[currentStep]
  const progress = ((currentStep + 1) / STEPS.length) * 100

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-8 py-6 border-b">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold">{currentStepData.title}</h2>
              <p className="text-gray-600">{currentStepData.description}</p>
            </div>
            <button
              onClick={onSkip}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="Skip tutorial"
            >
              <X className="w-6 h-6 text-gray-400" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-600 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-sm text-gray-600 font-medium">
              {currentStep + 1} / {STEPS.length}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-8">
          {currentStepData.content}
        </div>

        {/* Footer */}
        <div className="px-8 py-6 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <button
              onClick={currentStep === 0 ? onSkip : handleBack}
              className="px-6 py-2 text-gray-600 hover:text-gray-900 font-medium"
              disabled={currentStep === 0 && sampleDocProcessed}
            >
              {currentStep === 0 ? 'Skip Tutorial' : (
                <>
                  <ArrowLeft className="w-4 h-4 inline mr-2" />
                  Back
                </>
              )}
            </button>

            <button
              onClick={handleNext}
              disabled={currentStep === 1 && !sampleDocProcessed}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentStep === STEPS.length - 1 ? 'Finish' : (
                <>
                  Continue
                  <ArrowRight className="w-4 h-4 inline ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
