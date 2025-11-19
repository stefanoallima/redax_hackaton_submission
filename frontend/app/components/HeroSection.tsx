'use client'

import { useState, useRef, useEffect } from 'react'
import { Play, Pause, CheckCircle, Shield, Sparkles, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function HeroSection() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isVideoReady, setIsVideoReady] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    // Auto-play on load (muted)
    if (videoRef.current && isVideoReady) {
      videoRef.current.play().catch(() => {
        // Auto-play blocked, user interaction required
        setIsPlaying(false)
      })
    }
  }, [isVideoReady])

  const toggleVideo = () => {
    if (!videoRef.current) return

    if (videoRef.current.paused) {
      videoRef.current.play()
      setIsPlaying(true)
    } else {
      videoRef.current.pause()
      setIsPlaying(false)
    }
  }

  return (
    <section className="relative bg-gradient-to-br from-navy-900 via-navy-800 to-navy-900 pt-20 pb-32 overflow-hidden">
      {/* Animated background pattern */}
      <div className="absolute inset-0 bg-dot-pattern opacity-10" />

      {/* Gradient overlays for depth */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-navy-900/50" />
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl animate-pulse delay-1000" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left column: Copy */}
          <div className="space-y-8 animate-slide-up">
            {/* Trust badge */}
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white px-4 py-2 rounded-full text-sm font-medium shadow-soft hover:bg-white/15 transition-all group">
              <Shield className="w-4 h-4 text-primary-400 group-hover:scale-110 transition-transform" />
              <span>Trusted by over 47 Italian law firms</span>
            </div>

            {/* Main heading with gradient */}
            <div>
              <h1 className="text-5xl lg:text-7xl font-bold text-white mb-4 leading-tight">
                Redact legal documents
                <span className="block mt-2">
                  <span className="bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                    96% faster
                  </span>
                </span>
              </h1>
              <div className="flex items-start gap-2 mt-4">
                <Sparkles className="w-5 h-5 text-primary-400 mt-1 flex-shrink-0" />
                <p className="text-xl text-navy-200 leading-relaxed">
                  AI detection of personal data for Italian legal documents.
                  Reduce 2-4 hours of manual redaction to just 45 seconds.
                </p>
              </div>
            </div>

            {/* Stats with glassmorphism */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { value: '96%', label: 'Time saved', color: 'from-primary-400 to-primary-600' },
                { value: '98%', label: 'Accuracy', color: 'from-emerald-400 to-emerald-600' },
                { value: '4.8★', label: 'Rating', color: 'from-amber-400 to-amber-600' },
              ].map((stat, index) => (
                <div
                  key={stat.label}
                  className="glass backdrop-blur-md bg-white/10 border border-white/20 rounded-2xl p-5 hover:bg-white/15 transition-all hover:scale-105 hover:shadow-glow group"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className={`text-3xl lg:text-4xl font-bold bg-gradient-to-br ${stat.color} bg-clip-text text-transparent mb-1`}>
                    {stat.value}
                  </div>
                  <div className="text-xs lg:text-sm text-navy-300 font-medium">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Link
                href="/register"
                className="group inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl hover:from-primary-600 hover:to-primary-700 transition-all shadow-large hover:shadow-glow-lg hover:scale-105 transform"
              >
                Try 2 Free Redactions
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link
                href="/pricing"
                className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-white/10 backdrop-blur-sm border-2 border-white/30 rounded-xl hover:bg-white/20 transition-all"
              >
                See Pricing
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="flex flex-wrap gap-4 text-sm text-navy-300 pt-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>No credit card</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>2 free redactions</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Just 45 seconds</span>
              </div>
            </div>
          </div>

          {/* Right column: Video demo with floating effect */}
          <div className="relative z-10 animate-slide-up delay-200">
            <div className="relative rounded-3xl overflow-hidden shadow-large bg-navy-800/50 backdrop-blur-sm border border-white/10 hover:shadow-glow-lg transition-all duration-500 group">
              {/* Video player */}
              <div className="relative aspect-video bg-gradient-to-br from-navy-800 to-navy-900">
                {!isVideoReady && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-white text-center">
                      <div className="w-16 h-16 border-4 border-primary-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                      <p className="text-sm text-navy-300">Loading demo...</p>
                    </div>
                  </div>
                )}

                <video
                  ref={videoRef}
                  className={`w-full h-full object-cover ${!isVideoReady ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
                  poster="/videos/hero_demo_poster.jpg"
                  playsInline
                  muted
                  loop
                  onLoadedData={() => setIsVideoReady(true)}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                >
                  <source src="/videos/hero_demo.mp4" type="video/mp4" />
                  <source src="/videos/hero_demo.webm" type="video/webm" />
                  Your browser does not support video playback.
                </video>

                {/* Play/Pause overlay with better design */}
                {isVideoReady && (
                  <div
                    className={`absolute inset-0 flex items-center justify-center bg-gradient-to-b from-black/20 to-black/40 cursor-pointer transition-opacity duration-300 ${
                      isPlaying ? 'opacity-0 hover:opacity-100' : 'opacity-100'
                    }`}
                    onClick={toggleVideo}
                  >
                    <button
                      className="w-20 h-20 flex items-center justify-center bg-white/95 backdrop-blur-sm rounded-full shadow-large hover:bg-white transition-all transform hover:scale-110 group-hover:shadow-glow"
                      aria-label={isPlaying ? 'Pause video' : 'Play video'}
                    >
                      {isPlaying ? (
                        <Pause className="w-10 h-10 text-navy-900 ml-0" />
                      ) : (
                        <Play className="w-10 h-10 text-navy-900 ml-1" />
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Video caption with glassmorphism */}
              <div className="glass-dark px-6 py-4 border-t border-white/10">
                <div className="flex items-center justify-between">
                  <p className="text-white text-sm font-medium">
                    Watch: Redact a 25-page contract in 45 seconds
                  </p>
                  <span className="text-xs text-primary-400 bg-primary-500/10 px-3 py-1 rounded-full">
                    LIVE DEMO
                  </span>
                </div>
              </div>
            </div>

            {/* Floating badge with animation */}
            <div className="absolute -top-6 -right-6 bg-gradient-to-br from-emerald-400 to-emerald-600 text-white px-5 py-3 rounded-2xl shadow-large transform rotate-6 hover:rotate-12 transition-all animate-float hover:scale-110 cursor-default">
              <div className="text-center">
                <div className="text-sm font-bold">2 FREE</div>
                <div className="text-xs opacity-90">Redactions</div>
              </div>
            </div>

            {/* Decorative elements */}
            <div className="absolute -bottom-4 -left-4 w-24 h-24 bg-primary-500/20 rounded-full blur-2xl" />
            <div className="absolute -top-4 -right-4 w-32 h-32 bg-primary-600/10 rounded-full blur-2xl" />
          </div>
        </div>
      </div>

      {/* Trust indicators section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-24 relative z-10">
        <div className="text-center mb-8">
          <p className="text-sm text-navy-400 uppercase tracking-wider font-semibold">
            Certified for compliance
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center justify-items-center">
          {[
            { text: 'GDPR Compliant', icon: Shield },
            { text: 'ISO 27001', icon: Shield },
            { text: 'SOC 2 Type II', icon: Shield },
            { text: '100% On-Premise', icon: Shield },
          ].map((badge, index) => (
            <div
              key={badge.text}
              className="flex items-center gap-3 glass backdrop-blur-sm bg-white/5 border border-white/10 px-6 py-3 rounded-xl hover:bg-white/10 transition-all group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <badge.icon className="w-5 h-5 text-primary-400 group-hover:scale-110 transition-transform" />
              <span className="text-navy-200 font-semibold text-sm">{badge.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent" />
    </section>
  )
}
