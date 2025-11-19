'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Book, Download, Video, FileText, HelpCircle,
  ChevronRight, Search, ExternalLink
} from 'lucide-react'

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const sections = [
    {
      title: 'Getting Started',
      icon: Book,
      articles: [
        { title: 'Quick Start Guide', href: '#quickstart', duration: '5 min read' },
        { title: 'Installation & Setup', href: '#installation', duration: '10 min read' },
        { title: 'Your First Redaction', href: '#first-redaction', duration: '8 min read' },
        { title: 'Understanding Detection Modes', href: '#detection-modes', duration: '12 min read' }
      ]
    },
    {
      title: 'Desktop App',
      icon: Download,
      articles: [
        { title: 'Download & Install', href: '#download', duration: '5 min read' },
        { title: 'System Requirements', href: '#requirements', duration: '3 min read' },
        { title: 'Offline Mode', href: '#offline', duration: '7 min read' },
        { title: 'Keyboard Shortcuts', href: '#shortcuts', duration: '5 min read' }
      ]
    },
    {
      title: 'Features',
      icon: FileText,
      articles: [
        { title: 'Entity Types & Detection', href: '#entities', duration: '15 min read' },
        { title: 'Custom Keywords', href: '#keywords', duration: '10 min read' },
        { title: 'Batch Processing', href: '#batch', duration: '12 min read' },
        { title: 'Export Formats', href: '#export', duration: '8 min read' }
      ]
    },
    {
      title: 'Video Tutorials',
      icon: Video,
      articles: [
        { title: 'Desktop App Overview', href: '#video-overview', duration: '5 min watch' },
        { title: 'Reviewing Detected Entities', href: '#video-review', duration: '7 min watch' },
        { title: 'Team Collaboration Setup', href: '#video-team', duration: '10 min watch' },
        { title: 'Advanced Settings', href: '#video-advanced', duration: '12 min watch' }
      ]
    }
  ]

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-600 to-blue-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <h1 className="text-5xl font-bold mb-6">
              Documentation
            </h1>
            <p className="text-xl text-blue-100 mb-8">
              Everything you need to know about using CodiceCivile.ai for document redaction
            </p>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                icon: Download,
                title: 'Download Desktop App',
                description: 'Get started with offline redaction',
                href: '/download',
                color: 'blue'
              },
              {
                icon: Video,
                title: 'Watch Demo',
                description: '5-minute video tutorial',
                href: '#demo',
                color: 'purple'
              },
              {
                icon: Book,
                title: 'Quick Start',
                description: 'Redact your first document',
                href: '#quickstart',
                color: 'green'
              },
              {
                icon: HelpCircle,
                title: 'Get Support',
                description: 'Contact our team',
                href: '/support',
                color: 'orange'
              }
            ].map((link) => {
              const Icon = link.icon
              return (
                <Link
                  key={link.title}
                  href={link.href}
                  className="flex gap-4 p-6 rounded-xl border-2 border-gray-100 hover:border-blue-200 hover:shadow-md transition group"
                >
                  <div className={`w-12 h-12 bg-${link.color}-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-${link.color}-600 transition`}>
                    <Icon className={`w-6 h-6 text-${link.color}-600 group-hover:text-white transition`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition">
                      {link.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {link.description}
                    </p>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* Documentation Sections */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-8">
            {sections.map((section) => {
              const Icon = section.icon
              return (
                <div key={section.title} className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      {section.title}
                    </h2>
                  </div>

                  <div className="space-y-3">
                    {section.articles.map((article) => (
                      <Link
                        key={article.title}
                        href={article.href}
                        className="flex items-center justify-between p-4 rounded-lg hover:bg-gray-50 transition group"
                      >
                        <div>
                          <h3 className="font-medium text-gray-900 group-hover:text-blue-600 transition">
                            {article.title}
                          </h3>
                          <p className="text-sm text-gray-500 mt-1">
                            {article.duration}
                          </p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition" />
                      </Link>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Popular Articles */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">
            Popular Articles
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                title: 'How to redact Codice Fiscale',
                excerpt: 'Learn the best practices for detecting and redacting Italian tax codes in legal documents.',
                views: '12.5K views',
                category: 'Tutorial'
              },
              {
                title: 'Understanding Detection Accuracy',
                excerpt: 'Deep dive into how our multi-layer AI achieves 98% accuracy on Italian documents.',
                views: '8.2K views',
                category: 'Technical'
              },
              {
                title: 'GDPR Compliance Guide',
                excerpt: 'How CodiceCivile.ai helps you meet GDPR Article 32 requirements for data protection.',
                views: '10.1K views',
                category: 'Compliance'
              }
            ].map((article) => (
              <Link
                key={article.title}
                href="#"
                className="block bg-gray-50 rounded-xl p-6 hover:shadow-lg transition group"
              >
                <div className="inline-block bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full mb-4">
                  {article.category}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 group-hover:text-blue-600 transition">
                  {article.title}
                </h3>
                <p className="text-gray-600 mb-4 line-clamp-2">
                  {article.excerpt}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">{article.views}</span>
                  <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-blue-600 transition" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Still need help? */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Still need help?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Our support team is here to assist you
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/support"
              className="inline-flex items-center px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold transition"
            >
              Contact Support
            </Link>
            <Link
              href="mailto:support@codicecivile.ai"
              className="inline-flex items-center px-8 py-4 border-2 border-gray-300 text-gray-700 rounded-lg hover:border-gray-400 font-semibold transition"
            >
              Email Us
            </Link>
          </div>
          <p className="text-sm text-gray-500 mt-6">
            Average response time: 4 hours
          </p>
        </div>
      </section>
    </main>
  )
}
