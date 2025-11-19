'use client'

import Link from 'next/link'
import { Shield, Mail, Twitter, Linkedin, Github, Heart } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gradient-to-b from-navy-900 to-navy-950 text-navy-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-medium">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">
                OscuraTestiAI<span className="text-primary-400">.it</span>
              </span>
            </div>
            <p className="text-sm text-navy-400 mb-6 leading-relaxed">
              AI legale privacy-first per avvocati italiani. Oscura documenti 96% più veloce.
            </p>
            <div className="flex gap-3">
              <a
                href="https://twitter.com/oscuratestiai"
                className="w-10 h-10 flex items-center justify-center bg-navy-800 hover:bg-primary-600 text-navy-400 hover:text-white rounded-lg transition-all hover:scale-110"
                aria-label="Twitter"
              >
                <Twitter className="w-5 h-5" />
              </a>
              <a
                href="https://linkedin.com/company/oscuratestiai"
                className="w-10 h-10 flex items-center justify-center bg-navy-800 hover:bg-primary-600 text-navy-400 hover:text-white rounded-lg transition-all hover:scale-110"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-5 h-5" />
              </a>
              <a
                href="https://github.com/oscuratestiai"
                className="w-10 h-10 flex items-center justify-center bg-navy-800 hover:bg-primary-600 text-navy-400 hover:text-white rounded-lg transition-all hover:scale-110"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-white font-bold mb-5 text-sm uppercase tracking-wider">Prodotto</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/pricing" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Prezzi
                </Link>
              </li>
              <li>
                <Link href="/features" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Funzionalità
                </Link>
              </li>
              <li>
                <Link href="/desktop" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  App Desktop
                </Link>
              </li>
              <li>
                <Link href="/research" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Ricerca Legale
                </Link>
              </li>
              <li>
                <Link href="/changelog" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Changelog
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-white font-bold mb-5 text-sm uppercase tracking-wider">Risorse</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/docs" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Documentazione
                </Link>
              </li>
              <li>
                <Link href="/guides" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Guide
                </Link>
              </li>
              <li>
                <Link href="/support" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Supporto
                </Link>
              </li>
              <li>
                <Link href="/blog" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Blog
                </Link>
              </li>
              <li>
                <Link href="/api" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Riferimento API
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-bold mb-5 text-sm uppercase tracking-wider">Legale</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/privacy" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Termini di Servizio
                </Link>
              </li>
              <li>
                <Link href="/gdpr" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Conformità GDPR
                </Link>
              </li>
              <li>
                <Link href="/security" className="hover:text-primary-400 transition-colors hover:pl-2 inline-block duration-200">
                  Sicurezza
                </Link>
              </li>
            </ul>
            <div className="mt-6">
              <a
                href="mailto:support@redaxai.app"
                className="flex items-center gap-2 text-sm hover:text-primary-400 transition-colors group"
              >
                <Mail className="w-4 h-4 group-hover:scale-110 transition-transform" />
                support@redaxai.app
              </a>
            </div>
          </div>
        </div>

        {/* Bottom bar with gradient border */}
        <div className="pt-8 border-t border-navy-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-navy-400 flex items-center gap-2">
              © {new Date().getFullYear()} redaxai.app. Tutti i diritti riservati.
              <span className="hidden md:inline-flex items-center gap-1">
                • Fatto con <Heart className="w-3 h-3 text-red-500 fill-current" /> in Italia
              </span>
            </p>
            <div className="flex gap-6 text-sm">
              <Link href="/privacy" className="hover:text-primary-400 transition-colors">
                Privacy
              </Link>
              <Link href="/terms" className="hover:text-primary-400 transition-colors">
                Termini
              </Link>
              <Link href="/cookies" className="hover:text-primary-400 transition-colors">
                Cookie
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
