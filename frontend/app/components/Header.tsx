'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Menu, X, Shield, Sparkles } from 'lucide-react'

export default function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-white/95 backdrop-blur-lg shadow-soft border-b border-navy-100'
          : 'bg-white border-b border-navy-100'
      }`}
    >
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-18">
          {/* Logo with enhanced design */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-soft group-hover:shadow-medium group-hover:scale-105 transition-all">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold text-navy-900 group-hover:text-primary-600 transition-colors">
                OscuraTestiAI<span className="text-primary-600">.it</span>
              </span>
            </div>
          </Link>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center gap-8">
            <Link
              href="/pricing"
              className="text-navy-600 hover:text-navy-900 font-semibold transition-colors relative group"
            >
              Prezzi
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary-600 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/features"
              className="text-navy-600 hover:text-navy-900 font-semibold transition-colors relative group"
            >
              Funzionalità
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary-600 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/docs"
              className="text-navy-600 hover:text-navy-900 font-semibold transition-colors relative group"
            >
              Documentazione
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary-600 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link
              href="/login"
              className="text-navy-600 hover:text-navy-900 font-semibold transition-colors"
            >
              Accedi
            </Link>
            <Link
              href="/register"
              className="group inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl hover:from-primary-600 hover:to-primary-700 font-semibold transition-all shadow-soft hover:shadow-medium hover:scale-105"
            >
              <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
              Prova Gratis
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 text-navy-600 hover:text-navy-900 hover:bg-navy-50 rounded-lg transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile menu with animation */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-6 border-t border-navy-100 animate-slide-down">
            <div className="flex flex-col gap-1">
              <Link
                href="/pricing"
                className="text-navy-600 hover:text-navy-900 hover:bg-navy-50 font-semibold transition-colors px-4 py-3 rounded-lg"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Prezzi
              </Link>
              <Link
                href="/features"
                className="text-navy-600 hover:text-navy-900 hover:bg-navy-50 font-semibold transition-colors px-4 py-3 rounded-lg"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Funzionalità
              </Link>
              <Link
                href="/docs"
                className="text-navy-600 hover:text-navy-900 hover:bg-navy-50 font-semibold transition-colors px-4 py-3 rounded-lg"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Documentazione
              </Link>
              <Link
                href="/login"
                className="text-navy-600 hover:text-navy-900 hover:bg-navy-50 font-semibold transition-colors px-4 py-3 rounded-lg"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Accedi
              </Link>
              <Link
                href="/register"
                className="mt-4 inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl hover:from-primary-600 hover:to-primary-700 font-semibold transition-all shadow-soft text-center"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Sparkles className="w-4 h-4" />
                Prova Gratis
              </Link>
            </div>
          </div>
        )}
      </nav>
    </header>
  )
}
