'use client'

import Link from 'next/link'
import { ArrowRight, Download, CreditCard, CheckCircle2, Sparkles, Zap } from 'lucide-react'

export default function CTASection() {
  return (
    <section className="relative py-32 bg-gradient-to-br from-navy-900 via-navy-800 to-navy-900 overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 bg-dot-pattern opacity-10" />
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-soft animate-slide-down">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Join 47+ Italian law firms</span>
          </div>

          {/* Heading with gradient */}
          <h2 className="text-4xl md:text-6xl font-bold text-white leading-tight">
            Ready to redact
            <span className="block mt-2 bg-gradient-to-r from-primary-400 via-primary-500 to-primary-600 bg-clip-text text-transparent">
              96% faster?
            </span>
          </h2>

          <p className="text-xl md:text-2xl text-navy-200 max-w-3xl mx-auto leading-relaxed">
            Start with 2 free redactions. No credit card required.
            Upgrade to unlimited when you're ready.
          </p>

          {/* CTAs with enhanced design */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center pt-4">
            <Link
              href="/register"
              className="group inline-flex items-center justify-center px-10 py-5 text-lg font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl hover:from-primary-600 hover:to-primary-700 transition-all shadow-large hover:shadow-glow-lg hover:scale-105 transform"
            >
              <Zap className="mr-3 w-6 h-6 group-hover:rotate-12 transition-transform" />
              Try 2 Free Redactions
              <ArrowRight className="ml-3 w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </Link>

            <Link
              href="/pricing"
              className="inline-flex items-center justify-center px-10 py-5 text-lg font-bold text-white bg-white/10 backdrop-blur-sm border-2 border-white/30 rounded-2xl hover:bg-white/20 hover:border-white/40 transition-all shadow-medium hover:shadow-large"
            >
              See Pricing
            </Link>
          </div>

          {/* Trust indicators */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center text-navy-300 text-sm pt-4">
            <div className="flex items-center gap-2.5 bg-white/5 backdrop-blur-sm px-5 py-3 rounded-xl border border-white/10">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span className="font-medium">No credit card</span>
            </div>
            <div className="flex items-center gap-2.5 bg-white/5 backdrop-blur-sm px-5 py-3 rounded-xl border border-white/10">
              <Download className="w-5 h-5 text-primary-400" />
              <span className="font-medium">2 free redactions</span>
            </div>
            <div className="flex items-center gap-2.5 bg-white/5 backdrop-blur-sm px-5 py-3 rounded-xl border border-white/10">
              <Zap className="w-5 h-5 text-amber-400" />
              <span className="font-medium">Just 45 seconds</span>
            </div>
          </div>

          {/* Stats bar with glassmorphism */}
          <div className="mt-20 glass-dark backdrop-blur-lg border border-white/10 rounded-3xl p-10 shadow-large">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              <div className="text-center group">
                <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium group-hover:scale-110 transition-transform">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <div className="text-5xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent mb-2">
                  47+
                </div>
                <div className="text-navy-300 font-medium">Italian law firms</div>
              </div>
              <div className="text-center group">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium group-hover:scale-110 transition-transform">
                  <CheckCircle2 className="w-8 h-8 text-white" />
                </div>
                <div className="text-5xl font-bold bg-gradient-to-r from-emerald-400 to-emerald-600 bg-clip-text text-transparent mb-2">
                  8,942
                </div>
                <div className="text-navy-300 font-medium">Documents redacted</div>
              </div>
              <div className="text-center group">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-500 to-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium group-hover:scale-110 transition-transform">
                  <Download className="w-8 h-8 text-white" />
                </div>
                <div className="text-5xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent mb-2">
                  4.8★
                </div>
                <div className="text-navy-300 font-medium">Average rating</div>
              </div>
            </div>
          </div>

          {/* Final trust message */}
          <p className="text-navy-400 text-sm pt-8">
            Over 8,942 documents redacted • Saved over 580 hours this month • GDPR protection guaranteed
          </p>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent" />
    </section>
  )
}
