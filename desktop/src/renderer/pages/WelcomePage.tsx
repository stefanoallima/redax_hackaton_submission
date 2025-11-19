/**
 * Welcome Page - Choose Redaction Workflow
 * Routing page for selecting how to interact with the app
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Brain,
  ArrowRight,
  FileCheck,
  Settings as SettingsIcon
} from 'lucide-react'
import OnboardingWizard from '../components/OnboardingWizard'
import redaxLogo from '../../../redax_logo.svg'

const ONBOARDING_STORAGE_KEY = 'redaxai_onboarding_completed'

export default function WelcomePage() {
  const navigate = useNavigate()
  const [showOnboarding, setShowOnboarding] = useState(false)

  // Check if this is first time user
  useEffect(() => {
    const hasCompletedOnboarding = localStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (!hasCompletedOnboarding) {
      // Show onboarding on first launch
      setShowOnboarding(true)
    }
  }, [])

  const handleOnboardingComplete = () => {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, 'true')
    setShowOnboarding(false)
  }

  const handleOnboardingSkip = () => {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, 'true')
    setShowOnboarding(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={redaxLogo} alt="RedaxAI Logo" className="w-10 h-10" />
            <h1 className="text-xl font-semibold">RedaxAI</h1>
          </div>
          <button
            onClick={() => navigate('/settings')}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 flex items-center gap-2"
          >
            <SettingsIcon className="w-4 h-4" />
            Settings
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            AI Cloud Intelligence meet Local Privacy Control
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Boost Local redaction via learning from AI 
            You are in control of the data and redaction
          </p>
        </div>

        {/* Workflow Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Standard Redaction */}
          <div
            onClick={() => navigate('/standard')}
            className="group bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-blue-500"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <FileCheck className="w-8 h-8 text-white" />
            </div>

            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Standard Redaction
            </h3>

            <p className="text-gray-600 mb-6">
              Upload a document and automatically detect sensitive data.
              You are in control review and adjust the redaction.
              Boost accuracy via Google Gemini AI Multimodal (text + Images) via the Cloud  
            </p>

            <ul className="space-y-2 mb-6 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>Auto-detect names, SSNs, addresses</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>Review and confirm entities</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>Export redacted PDF instantly</span>
              </li>
            </ul>

            <div className="flex items-center justify-between text-blue-600 font-medium group-hover:translate-x-2 transition-transform">
              <span>Start Redacting</span>
              <ArrowRight className="w-5 h-5" />
            </div>
          </div>

          {/* Create Redaction Template by chatting with Gemini */}
          <div
            onClick={() => navigate('/teaching')}
            className="group bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-purple-500"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Brain className="w-8 h-8 text-white" />
            </div>

            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              Create Redaction Templates with Gemini AI
            </h3>

            <p className="text-gray-600 mb-6">
              Chat-guided redaction template creation.
            </p>

            <ul className="space-y-2 mb-6 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>Describe what you want to redact to Gemini AI</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>Click & drag to select fields</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-1">•</span>
                <span>Save the redaction template to use it in the Standard Redaction</span>
              </li>
            </ul>

            <div className="flex items-center justify-between text-purple-600 font-medium group-hover:translate-x-2 transition-transform">
              <span>Create Template</span>
              <ArrowRight className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="bg-white rounded-2xl p-8 shadow-lg">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Which Mode Should I Use?
          </h3>

          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div className="border-r border-gray-200 pr-6">
              <h4 className="font-semibold text-blue-600 mb-3">Standard Redaction</h4>
              <p className="text-gray-600 mb-2">
                <strong>Best for:</strong>
              </p>
              <ul className="space-y-1 text-gray-700">
                <li>• One-time documents</li>
                <li>• Quick redactions</li>
                <li>• Templated redaction Optional</li>
                <li>• Send the file to Gemini To increase accuracy of redaction</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-purple-600 mb-3">Teaching Mode</h4>
              <p className="text-gray-600 mb-2">
                <strong>Best for:</strong>
              </p>
              <ul className="space-y-1 text-gray-700">
                <li>• Creating new templates</li>
                <li>• Blank forms/contracts</li>
                <li>• AI covnersation-guided workflow</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-12 grid grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold text-primary-600">100%</div>
            <div className="text-sm text-gray-600 mt-1">Local Processing</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-primary-600">95%+</div>
            <div className="text-sm text-gray-600 mt-1">Accuracy</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-primary-600">&lt;30s</div>
            <div className="text-sm text-gray-600 mt-1">Per Document</div>
          </div>
        </div>
      </main>

      {/* Onboarding Wizard Modal - Shows on first launch */}
      {showOnboarding && (
        <OnboardingWizard
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}
    </div>
  )
}
