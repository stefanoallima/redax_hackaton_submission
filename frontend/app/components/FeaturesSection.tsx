'use client'

import { Shield, Zap, Users, FileCheck, Brain, Lock, ArrowRight, CheckCircle2 } from 'lucide-react'

const features = [
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Process 25-page contracts in less than 45 seconds. Reduce 2-4 hours of manual work to just minutes.',
    stat: '96% faster',
    color: 'from-amber-400 to-orange-500',
    bgColor: 'from-amber-50 to-orange-50',
  },
  {
    icon: Brain,
    title: 'AI Detection',
    description: 'Multi-layer PII detection: Regex + LLM validation + visual analysis for 98% accuracy.',
    stat: '98% accuracy',
    color: 'from-purple-400 to-pink-500',
    bgColor: 'from-purple-50 to-pink-50',
  },
  {
    icon: Lock,
    title: '100% Private',
    description: 'The desktop app works completely offline. Your documents never leave your machine.',
    stat: 'Zero cloud uploads',
    color: 'from-emerald-400 to-teal-500',
    bgColor: 'from-emerald-50 to-teal-50',
  },
  {
    icon: FileCheck,
    title: 'Italian Legal Focus',
    description: 'Detects Codice Fiscale, IBAN, legal addresses and Italian-specific PII patterns.',
    stat: '15+ entity types',
    color: 'from-blue-400 to-cyan-500',
    bgColor: 'from-blue-50 to-cyan-50',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Share redaction templates, track team usage and collaborate on sensitive documents.',
    stat: 'Law Firm Plan',
    color: 'from-indigo-400 to-purple-500',
    bgColor: 'from-indigo-50 to-purple-50',
  },
  {
    icon: Shield,
    title: 'GDPR Compliant',
    description: 'Built for Italian law firms. Meets GDPR Article 32 requirements for data protection.',
    stat: 'Fully compliant',
    color: 'from-green-400 to-emerald-500',
    bgColor: 'from-green-50 to-emerald-50',
  },
]

export default function FeaturesSection() {
  return (
    <section className="py-24 bg-gradient-to-b from-white via-navy-50/30 to-white relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-primary-100/40 rounded-full blur-3xl -z-0" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-100/40 rounded-full blur-3xl -z-0" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-semibold mb-4">
            <CheckCircle2 className="w-4 h-4" />
            Complete Features
          </div>
          <h2 className="text-4xl lg:text-5xl font-bold text-navy-900 leading-tight">
            Everything you need to
            <span className="block mt-2 bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
              redact legal documents
            </span>
          </h2>
          <p className="text-xl text-navy-600 leading-relaxed">
            Built specifically for Italian lawyers handling sensitive client information daily
          </p>
        </div>

        {/* Features grid with stagger animation */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="group relative bg-white border border-navy-100 rounded-3xl p-8 hover:border-transparent hover:shadow-large transition-all duration-500 hover:-translate-y-2"
                style={{
                  animationDelay: `${index * 100}ms`,
                }}
              >
                {/* Gradient overlay on hover */}
                <div className={`absolute inset-0 rounded-3xl bg-gradient-to-br ${feature.bgColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10`} />

                {/* Icon with gradient background */}
                <div className="relative mb-6">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center shadow-soft group-hover:shadow-medium group-hover:scale-110 transition-all duration-300`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  {/* Floating dot decoration */}
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-primary-400 rounded-full animate-pulse" />
                </div>

                {/* Content */}
                <h3 className="text-2xl font-bold text-navy-900 mb-3 group-hover:text-navy-800 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-navy-600 mb-6 leading-relaxed">
                  {feature.description}
                </p>

                {/* Stat badge */}
                <div className={`inline-flex items-center gap-2 bg-gradient-to-r ${feature.color} text-white text-sm font-bold px-4 py-2 rounded-xl shadow-soft`}>
                  <span>{feature.stat}</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>

                {/* Corner accent */}
                <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${feature.color} opacity-5 rounded-tr-3xl rounded-bl-3xl transition-opacity group-hover:opacity-10`} />
              </div>
            )
          })}
        </div>

        {/* How it works section */}
        <div className="mt-32">
          <div className="text-center mb-16">
            <h3 className="text-3xl lg:text-4xl font-bold text-navy-900 mb-4">
              How it works
            </h3>
            <p className="text-lg text-navy-600 max-w-2xl mx-auto">
              From upload to export in 4 simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-8 relative">
            {/* Connecting line for desktop */}
            <div className="hidden md:block absolute top-12 left-0 right-0 h-1 bg-gradient-to-r from-primary-200 via-primary-300 to-primary-200 -z-10" />

            {[
              {
                step: '1',
                title: 'Upload PDF',
                description: 'Drag your legal document into the desktop app',
                icon: '📄',
              },
              {
                step: '2',
                title: 'AI Analyzes',
                description: 'Multi-layer detection finds all PII in 15-45 seconds',
                icon: '🤖',
              },
              {
                step: '3',
                title: 'Review & Edit',
                description: 'Accept/reject detected entities with visual highlights',
                icon: '✓',
              },
              {
                step: '4',
                title: 'Export Redacted',
                description: 'Download professional redacted PDF',
                icon: '⬇',
              },
            ].map((item, index) => (
              <div key={item.step} className="text-center relative group">
                {/* Step number badge with gradient */}
                <div className="relative z-10 w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-3xl flex flex-col items-center justify-center text-3xl font-bold mx-auto mb-6 shadow-medium group-hover:shadow-glow group-hover:scale-110 transition-all duration-300">
                  <span className="text-5xl mb-1">{item.icon}</span>
                  <span className="text-xs font-semibold opacity-80">STEP {item.step}</span>
                </div>

                {/* Content card */}
                <div className="bg-white rounded-2xl p-6 border border-navy-100 shadow-soft group-hover:shadow-medium transition-all duration-300 group-hover:-translate-y-1">
                  <h4 className="font-bold text-navy-900 mb-2 text-lg">{item.title}</h4>
                  <p className="text-sm text-navy-600 leading-relaxed">{item.description}</p>
                </div>

                {/* Arrow connector (hidden on mobile and last item) */}
                {index < 3 && (
                  <div className="hidden md:block absolute top-12 -right-4 z-20">
                    <ArrowRight className="w-8 h-8 text-primary-400" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
