'use client'

import Link from 'next/link'
import {
  Zap, Brain, Lock, FileCheck, Users, Shield,
  CheckCircle, ArrowRight, Download, Clock,
  BarChart3, FileText, Eye, Sparkles
} from 'lucide-react'

export default function FeaturesPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              Built for Italian Legal Professionals
            </div>
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Everything you need to redact documents
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Multi-layer AI detection, 100% offline processing, and intelligent workflow automation
            </p>
            <div className="flex gap-4 justify-center">
              <Link
                href="/register"
                className="inline-flex items-center px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold transition"
              >
                Try 2 Free Redactions
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center px-8 py-4 border-2 border-gray-300 text-gray-700 rounded-lg hover:border-gray-400 font-semibold transition"
              >
                View Pricing
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">
            Core Features
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Brain,
                title: 'Multi-Layer AI Detection',
                description: 'Combines regex patterns, LLM validation (Llama 3.2), and visual analysis (Qwen-VL) for 98% accuracy.',
                features: [
                  'Rule-based regex for speed',
                  'LLM verification for context',
                  'Visual detection for scanned docs',
                  'Italian-specific entity recognition'
                ]
              },
              {
                icon: Lock,
                title: '100% Offline Processing',
                description: 'Desktop app runs entirely on your machine. Documents never touch the cloud.',
                features: [
                  'No internet required',
                  'Zero cloud uploads',
                  'GDPR Article 32 compliant',
                  'Client data stays private'
                ]
              },
              {
                icon: Zap,
                title: 'Lightning Fast',
                description: 'Process 25-page contracts in under 45 seconds. Reduce 2-4 hours of work to minutes.',
                features: [
                  'Fast mode: 15 seconds',
                  'Balanced: 30 seconds',
                  'Thorough: 60 seconds',
                  'Maximum: 120 seconds'
                ]
              },
              {
                icon: FileCheck,
                title: 'Italian Legal Focus',
                description: 'Purpose-built for Italian legal documents with specialized entity detection.',
                features: [
                  'Codice Fiscale detection',
                  'IBAN validation',
                  'Italian address formats',
                  'Legal terminology aware'
                ]
              },
              {
                icon: Eye,
                title: 'Visual Review Interface',
                description: 'See exactly what will be redacted with inline highlights and side-by-side comparison.',
                features: [
                  'Click to accept/reject entities',
                  'Confidence scores shown',
                  'Batch operations (accept all)',
                  'Before/after preview'
                ]
              },
              {
                icon: Users,
                title: 'Team Collaboration',
                description: 'Share redaction templates, track team usage, and collaborate on sensitive documents.',
                features: [
                  'Shared templates library',
                  'Team analytics dashboard',
                  'Usage tracking per member',
                  'Role-based permissions'
                ]
              }
            ].map((feature) => {
              const Icon = feature.icon
              return (
                <div key={feature.title} className="bg-white border-2 border-gray-100 rounded-2xl p-8 hover:border-blue-200 hover:shadow-lg transition">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {feature.description}
                  </p>
                  <ul className="space-y-2">
                    {feature.features.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Detection Depth */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Choose Your Detection Depth
            </h2>
            <p className="text-xl text-gray-600">
              Balance speed and thoroughness based on your needs
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                name: 'Fast',
                time: '~15s',
                coverage: '80-85%',
                description: 'Quick scan for obvious PII',
                icon: Zap,
                color: 'green'
              },
              {
                name: 'Balanced',
                time: '~30s',
                coverage: '90-95%',
                description: 'Recommended for most documents',
                icon: CheckCircle,
                color: 'blue',
                recommended: true
              },
              {
                name: 'Thorough',
                time: '~60s',
                coverage: '95-98%',
                description: 'Deep analysis with context',
                icon: Shield,
                color: 'purple'
              },
              {
                name: 'Maximum',
                time: '~120s',
                coverage: '98-99%',
                description: 'Highest accuracy, slowest',
                icon: Brain,
                color: 'orange'
              }
            ].map((mode) => {
              const Icon = mode.icon
              return (
                <div
                  key={mode.name}
                  className={`relative bg-white rounded-2xl p-6 border-2 ${
                    mode.recommended ? 'border-blue-500' : 'border-gray-200'
                  } hover:shadow-lg transition`}
                >
                  {mode.recommended && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Recommended
                    </div>
                  )}
                  <div className={`w-12 h-12 bg-${mode.color}-100 rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className={`w-6 h-6 text-${mode.color}-600`} />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {mode.name}
                  </h3>
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-2xl font-bold text-gray-900">{mode.time}</span>
                    <span className="text-sm text-gray-500">per 25 pages</span>
                  </div>
                  <div className="text-sm font-semibold text-blue-600 mb-3">
                    {mode.coverage} coverage
                  </div>
                  <p className="text-sm text-gray-600">
                    {mode.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Entity Types */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              15+ Entity Types Detected
            </h2>
            <p className="text-xl text-gray-600">
              Specialized detection for Italian legal documents
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                category: 'Personal Identity',
                entities: ['Full Names', 'Codice Fiscale', 'Date of Birth', 'Place of Birth', 'Tax ID']
              },
              {
                category: 'Contact Information',
                entities: ['Email Addresses', 'Phone Numbers', 'Mobile Numbers', 'Fax Numbers', 'Addresses']
              },
              {
                category: 'Financial Data',
                entities: ['IBAN', 'Credit Card Numbers', 'Bank Account Info', 'Tax Numbers', 'Invoice Numbers']
              },
              {
                category: 'Professional Info',
                entities: ['Company Names', 'VAT Numbers', 'Professional Titles', 'Signatures', 'Stamps']
              },
              {
                category: 'Medical Data',
                entities: ['Health Conditions', 'Medical IDs', 'Hospital Names', 'Doctor Names', 'Prescriptions']
              },
              {
                category: 'Legal References',
                entities: ['Case Numbers', 'Court Names', 'Contract Numbers', 'License Plates', 'Property IDs']
              }
            ].map((group) => (
              <div key={group.category} className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {group.category}
                </h3>
                <ul className="space-y-2">
                  {group.entities.map((entity) => (
                    <li key={entity} className="flex items-center gap-2 text-sm text-gray-600">
                      <div className="w-1.5 h-1.5 bg-blue-600 rounded-full" />
                      {entity}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Complete Workflow
            </h2>
            <p className="text-xl text-gray-600">
              From upload to export in 4 simple steps
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            {[
              {
                step: 1,
                title: 'Upload Document',
                description: 'Drag and drop your PDF or select from your computer',
                icon: Download,
                details: ['Supports multi-page PDFs', 'No file size limits', 'Encrypted upload']
              },
              {
                step: 2,
                title: 'AI Analysis',
                description: 'Multi-layer detection finds all PII in your document',
                icon: Brain,
                details: ['Regex pattern matching', 'LLM context validation', 'Visual text recognition']
              },
              {
                step: 3,
                title: 'Review & Edit',
                description: 'Accept or reject detected entities with visual highlights',
                icon: Eye,
                details: ['Click to toggle entities', 'Confidence scores shown', 'Batch accept/reject']
              },
              {
                step: 4,
                title: 'Export Redacted',
                description: 'Download your professionally redacted PDF',
                icon: FileText,
                details: ['Permanent black boxes', 'Metadata cleaned', 'Original preserved']
              }
            ].map((step, index) => {
              const Icon = step.icon
              return (
                <div key={step.step} className="relative mb-8 last:mb-0">
                  {index < 3 && (
                    <div className="absolute left-8 top-20 w-0.5 h-24 bg-gray-200" />
                  )}
                  <div className="flex gap-6 items-start">
                    <div className="flex-shrink-0 w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold relative z-10">
                      {step.step}
                    </div>
                    <div className="flex-1 bg-white rounded-xl p-6 shadow-md">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Icon className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold text-gray-900 mb-2">
                            {step.title}
                          </h3>
                          <p className="text-gray-600 mb-4">
                            {step.description}
                          </p>
                          <ul className="space-y-1">
                            {step.details.map((detail) => (
                              <li key={detail} className="flex items-center gap-2 text-sm text-gray-500">
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                {detail}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-br from-blue-600 to-blue-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to try it yourself?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Start with 2 free redactions. No credit card required.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-gray-50 font-semibold transition shadow-xl"
            >
              Try 2 Free Redactions
              <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center px-8 py-4 bg-blue-700/50 border-2 border-white/30 text-white rounded-lg hover:bg-blue-700 font-semibold transition"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
