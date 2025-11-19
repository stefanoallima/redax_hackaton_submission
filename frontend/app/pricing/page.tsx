/**
 * Pricing Page - Subscription Plans
 * Optimized for conversion with clear value proposition
 */
'use client'

import { useState } from 'react'
import { Check, X, Zap, Users, Building2, Sparkles, Lock, Shield, CreditCard, Star, CheckCircle2 } from 'lucide-react'

interface PricingPlan {
  id: string
  name: string
  price: number | null
  annualPrice: number | null
  description: string
  icon: React.ReactNode
  popular?: boolean
  features: {
    included: string[]
    notIncluded?: string[]
  }
  limits: {
    documents: string
    searches: string
    chat: string
    users: number
  }
  cta: string
  color: string
  gradient: string
}

const PLANS: PricingPlan[] = [
  {
    id: 'free',
    name: 'Gratuito',
    price: 0,
    annualPrice: 0,
    description: 'Prova prima di acquistare',
    icon: <Sparkles className="w-6 h-6" />,
    features: {
      included: [
        'Ricerca legale basata sul web',
        '10 ricerche al mese',
        'Accesso al Codice Civile Italiano',
        'Supporto della community'
      ],
      notIncluded: [
        'App desktop di oscuramento',
        'Assistente chat AI',
        'Supporto prioritario'
      ]
    },
    limits: {
      documents: 'Solo Web',
      searches: '10/mese',
      chat: 'Nessun accesso',
      users: 1
    },
    cta: 'Inizia Gratis',
    color: 'gray',
    gradient: 'from-gray-400 to-gray-600',
  },
  {
    id: 'professional',
    name: 'Professionale',
    price: 25,
    annualPrice: 240,
    description: 'Per professionisti individuali',
    icon: <Zap className="w-6 h-6" />,
    popular: true,
    features: {
      included: [
        'App desktop di oscuramento',
        'Elaborazione documenti illimitata',
        '100 ricerche al mese',
        'Chat AI (50 messaggi/mese)',
        'Rilevamento PII offline',
        'Precisione 95%+',
        'Supporto email (risposta 24h)',
        'Aggiornamenti regolari'
      ]
    },
    limits: {
      documents: 'Illimitato',
      searches: '100/mese',
      chat: '50 messaggi/mese',
      users: 1
    },
    cta: 'Inizia Prova 14 Giorni',
    color: 'blue',
    gradient: 'from-primary-500 to-primary-700',
  },
  {
    id: 'studio',
    name: 'Studio',
    price: 69,
    annualPrice: 660,
    description: 'Per piccoli studi',
    icon: <Users className="w-6 h-6" />,
    features: {
      included: [
        'Tutto in Professionale',
        'Fino a 3 membri del team',
        'Ricerche illimitate',
        'Chat AI illimitata',
        'Template di oscuramento condivisi',
        'Dashboard analisi utilizzo',
        'Supporto email prioritario (risposta 12h)',
        'Chiamata di onboarding'
      ]
    },
    limits: {
      documents: 'Illimitato',
      searches: 'Illimitato',
      chat: 'Illimitato',
      users: 3
    },
    cta: 'Inizia Prova 14 Giorni',
    color: 'purple',
    gradient: 'from-purple-500 to-pink-600',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    annualPrice: null,
    description: 'Per studi legali',
    icon: <Building2 className="w-6 h-6" />,
    features: {
      included: [
        'Tutto in Studio',
        'Membri del team illimitati',
        'Integrazioni personalizzate',
        'Accesso API',
        'SSO (Single Sign-On)',
        'Account manager dedicato',
        'SLA personalizzato',
        'Supporto telefonico 24/7',
        'Opzione distribuzione on-premise'
      ]
    },
    limits: {
      documents: 'Illimitato',
      searches: 'Illimitato',
      chat: 'Illimitato',
      users: 999
    },
    cta: 'Contatta Vendite',
    color: 'green',
    gradient: 'from-emerald-500 to-teal-600',
  }
]

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly')
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  const handleSelectPlan = async (planId: string) => {
    setSelectedPlan(planId)

    if (planId === 'free') {
      window.location.href = '/signup'
      return
    }

    if (planId === 'enterprise') {
      window.location.href = '/contact?plan=enterprise'
      return
    }

    try {
      const response = await fetch('/api/v1/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          plan: planId,
          period: billingPeriod
        })
      })

      const { checkout_url } = await response.json()
      window.location.href = checkout_url

    } catch (error) {
      console.error('Checkout failed:', error)
      alert('Impossibile avviare il checkout. Riprova.')
    } finally {
      setSelectedPlan(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-navy-50 to-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-navy-900 via-navy-800 to-navy-900 pt-20 pb-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-dot-pattern opacity-10" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl" />

        <div className="max-w-7xl mx-auto px-4 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-soft">
              <Star className="w-4 h-4 text-amber-400 fill-current" />
              <span>Fidato da 47+ studi legali italiani</span>
            </div>

            <h1 className="text-5xl lg:text-6xl font-bold text-white leading-tight">
              Prezzi semplici e
              <span className="block mt-2 bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                trasparenti
              </span>
            </h1>

            <p className="text-xl text-navy-200 leading-relaxed">
              Scegli il piano che si adatta al tuo studio. Cancella in qualsiasi momento.
            </p>

            {/* Billing Toggle */}
            <div className="inline-flex items-center gap-2 p-2 bg-navy-800/50 backdrop-blur-sm border border-white/10 rounded-2xl shadow-medium">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-8 py-3 rounded-xl font-semibold transition-all ${
                  billingPeriod === 'monthly'
                    ? 'bg-white text-navy-900 shadow-soft'
                    : 'text-navy-300 hover:text-white'
                }`}
              >
                Mensile
              </button>
              <button
                onClick={() => setBillingPeriod('annual')}
                className={`px-8 py-3 rounded-xl font-semibold transition-all relative ${
                  billingPeriod === 'annual'
                    ? 'bg-white text-navy-900 shadow-soft'
                    : 'text-navy-300 hover:text-white'
                }`}
              >
                Annuale
                <span className="absolute -top-3 -right-3 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white text-xs px-3 py-1 rounded-full shadow-medium font-bold">
                  Risparmia 20%
                </span>
              </button>
            </div>

            {/* Trust Indicators */}
            <div className="flex flex-wrap justify-center gap-6 text-sm text-navy-300 pt-4">
              <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/10">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span>Crittografato SSL</span>
              </div>
              <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/10">
                <Shield className="w-4 h-4 text-primary-400" />
                <span>Conforme GDPR</span>
              </div>
              <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/10">
                <CreditCard className="w-4 h-4 text-amber-400" />
                <span>Pagamento Sicuro</span>
              </div>
              <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/10">
                <CheckCircle2 className="w-4 h-4 text-primary-400" />
                <span>Rimborso 30 Giorni</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-7xl mx-auto px-4 -mt-12 pb-24 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {PLANS.map((plan) => {
            const price = billingPeriod === 'annual' ? plan.annualPrice : plan.price
            const monthlyPrice = billingPeriod === 'annual' && price ? price / 12 : price

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-3xl shadow-large p-8 flex flex-col border-2 transition-all duration-300 hover:-translate-y-2 ${
                  plan.popular
                    ? 'border-primary-500 lg:scale-105 shadow-glow'
                    : 'border-navy-100 hover:border-primary-200'
                }`}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-5 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-primary-500 to-primary-600 text-white px-6 py-2 rounded-full text-sm font-bold shadow-medium">
                      Più Popolare
                    </span>
                  </div>
                )}

                {/* Plan Header */}
                <div className="mb-6">
                  <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${plan.gradient} text-white mb-4 shadow-soft`}>
                    {plan.icon}
                  </div>
                  <h3 className="text-2xl font-bold text-navy-900 mb-2">{plan.name}</h3>
                  <p className="text-navy-600 text-sm">{plan.description}</p>
                </div>

                {/* Pricing */}
                <div className="mb-8">
                  {price === null ? (
                    <div className="text-4xl font-bold text-navy-900">Personalizzato</div>
                  ) : (
                    <>
                      <div className="flex items-baseline gap-1">
                        <span className="text-5xl font-bold text-navy-900">€{monthlyPrice?.toFixed(0)}</span>
                        <span className="text-navy-600">/mese</span>
                      </div>
                      {billingPeriod === 'annual' && price > 0 && (
                        <div className="text-sm text-emerald-600 font-semibold mt-2">
                          €{price} fatturati annualmente
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Features List */}
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.included.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-navy-700">{feature}</span>
                    </li>
                  ))}
                  {plan.features.notIncluded?.map((feature, idx) => (
                    <li key={`not-${idx}`} className="flex items-start gap-3">
                      <X className="w-5 h-5 text-navy-300 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-navy-400 line-through">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                <button
                  onClick={() => handleSelectPlan(plan.id)}
                  disabled={selectedPlan === plan.id}
                  className={`w-full py-4 rounded-xl font-bold transition-all ${
                    plan.popular
                      ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700 shadow-soft hover:shadow-medium'
                      : 'bg-navy-100 text-navy-900 hover:bg-navy-200'
                  } disabled:opacity-50`}
                >
                  {selectedPlan === plan.id ? 'Caricamento...' : plan.cta}
                </button>

                {/* Trial Notice */}
                {(plan.id === 'professional' || plan.id === 'studio') && (
                  <p className="text-xs text-navy-500 text-center mt-4">
                    Prova gratuita di 14 giorni, nessuna carta di credito richiesta
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="max-w-7xl mx-auto px-4 pb-24">
        <h2 className="text-4xl font-bold text-navy-900 text-center mb-12">Confronto Dettagliato</h2>

        <div className="bg-white rounded-3xl shadow-large overflow-hidden border border-navy-100">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-navy-50 to-navy-100">
              <tr>
                <th className="px-6 py-5 text-left text-sm font-bold text-navy-900">
                  Funzionalità
                </th>
                {PLANS.map(plan => (
                  <th key={plan.id} className="px-6 py-5 text-center text-sm font-bold text-navy-900">
                    {plan.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-100">
              <tr className="hover:bg-navy-50/50 transition-colors">
                <td className="px-6 py-4 text-sm text-navy-700 font-semibold">Documenti/mese</td>
                {PLANS.map(plan => (
                  <td key={plan.id} className="px-6 py-4 text-center text-sm text-navy-900 font-medium">
                    {plan.limits.documents}
                  </td>
                ))}
              </tr>
              <tr className="hover:bg-navy-50/50 transition-colors">
                <td className="px-6 py-4 text-sm text-navy-700 font-semibold">Ricerche/mese</td>
                {PLANS.map(plan => (
                  <td key={plan.id} className="px-6 py-4 text-center text-sm text-navy-900 font-medium">
                    {plan.limits.searches}
                  </td>
                ))}
              </tr>
              <tr className="hover:bg-navy-50/50 transition-colors">
                <td className="px-6 py-4 text-sm text-navy-700 font-semibold">Chat AI</td>
                {PLANS.map(plan => (
                  <td key={plan.id} className="px-6 py-4 text-center text-sm text-navy-900 font-medium">
                    {plan.limits.chat}
                  </td>
                ))}
              </tr>
              <tr className="hover:bg-navy-50/50 transition-colors">
                <td className="px-6 py-4 text-sm text-navy-700 font-semibold">Membri del Team</td>
                {PLANS.map(plan => (
                  <td key={plan.id} className="px-6 py-4 text-center text-sm text-navy-900 font-medium">
                    {plan.limits.users === 999 ? 'Illimitato' : plan.limits.users}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-4 pb-24">
        <h2 className="text-4xl font-bold text-navy-900 text-center mb-12">Domande Frequenti</h2>

        <div className="space-y-4">
          {[
            {
              q: 'Posso cancellare in qualsiasi momento?',
              a: 'Sì, puoi cancellare il tuo abbonamento in qualsiasi momento. Nessuna domanda, nessun contratto. Continuerai ad avere accesso fino alla fine del periodo di fatturazione.'
            },
            {
              q: 'I miei dati sono al sicuro?',
              a: '100% sicuro. Tutta l\'elaborazione dei documenti avviene offline sul tuo computer. Non vediamo mai i tuoi documenti. Vengono raccolte solo statistiche di utilizzo anonime.'
            },
            {
              q: 'Offrite rimborsi?',
              a: 'Sì, offriamo una garanzia di rimborso di 30 giorni. Se non sei soddisfatto, inviaci un\'email e ti rimborseremo, senza domande.'
            },
            {
              q: 'Quali metodi di pagamento accettate?',
              a: 'Accettiamo tutte le principali carte di credito (Visa, Mastercard, Amex) tramite Stripe. I piani annuali possono anche essere pagati tramite bonifico bancario.'
            },
            {
              q: 'Posso cambiare piano in seguito?',
              a: 'Sì, puoi fare l\'upgrade o il downgrade in qualsiasi momento. Quando fai l\'upgrade, ti verrà addebitato un importo proporzionale. Quando fai il downgrade, il credito verrà applicato alla tua prossima fattura.'
            }
          ].map((faq, index) => (
            <details key={index} className="group bg-white rounded-2xl shadow-soft hover:shadow-medium transition-all border border-navy-100 overflow-hidden">
              <summary className="font-bold text-navy-900 cursor-pointer p-6 hover:text-primary-600 transition-colors flex items-center justify-between">
                {faq.q}
                <span className="text-primary-600 group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p className="text-navy-600 px-6 pb-6 leading-relaxed">
                {faq.a}
              </p>
            </details>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gradient-to-br from-navy-900 via-navy-800 to-navy-900 text-white py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-dot-pattern opacity-10" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl" />

        <div className="max-w-4xl mx-auto px-4 text-center relative z-10 space-y-8">
          <h2 className="text-4xl lg:text-5xl font-bold">
            Pronto a risparmiare ore nell'oscuramento dei documenti?
          </h2>
          <p className="text-xl text-navy-200">
            Unisciti a 200+ avvocati italiani che già utilizzano CodiceCivile.ai
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <button
              onClick={() => handleSelectPlan('professional')}
              className="px-10 py-5 bg-white text-primary-600 rounded-2xl font-bold hover:bg-navy-50 text-lg shadow-large hover:shadow-glow-lg hover:scale-105 transition-all"
            >
              Inizia Prova Gratuita
            </button>
            <a
              href="/demo"
              className="px-10 py-5 border-2 border-white/30 bg-white/10 backdrop-blur-sm text-white rounded-2xl font-bold hover:bg-white/20 text-lg transition-all"
            >
              Guarda la Demo
            </a>
          </div>
          <p className="text-sm text-navy-400">
            Nessuna carta di credito richiesta • Prova gratuita di 14 giorni • Cancella in qualsiasi momento
          </p>
        </div>
      </section>
    </div>
  )
}
