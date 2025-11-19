'use client'

import { Star, Quote, TrendingUp, Clock, Award, CheckCircle2 } from 'lucide-react'

const testimonials = [
  {
    name: 'Marco Bianchi',
    role: 'Independent Lawyer',
    location: 'Milan',
    avatar: 'MB',
    avatarColor: 'from-blue-500 to-blue-600',
    rating: 5,
    quote: 'CodiceCivile.ai saves me 15 hours a week. The desktop app is incredibly accurate and the web search feature is revolutionary. Worth every euro.',
    stats: { documents: 90, timeSaved: '60 hours', weeklySaved: '15h' },
    verified: true,
  },
  {
    name: 'Giulia Ferrara',
    role: 'Managing Partner',
    location: 'Ferrara Law Firm, Rome',
    avatar: 'GF',
    avatarColor: 'from-purple-500 to-pink-600',
    rating: 5,
    quote: 'We process over 200 employment contracts per month. This tool has reduced our redaction time by 96%. The team collaboration features are excellent.',
    stats: { documents: 247, timeSaved: '180 hours', weeklySaved: '45h' },
    verified: true,
  },
  {
    name: 'Alessandro Rossi',
    role: 'Privacy Lawyer',
    location: 'Rome',
    avatar: 'AR',
    avatarColor: 'from-emerald-500 to-teal-600',
    rating: 5,
    quote: 'As a GDPR specialist, I needed a solution that keeps documents on-premise. The offline desktop app is perfect. Detection accuracy is impressive for Italian documents.',
    stats: { documents: 156, timeSaved: '120 hours', weeklySaved: '30h' },
    verified: true,
  },
]

export default function TestimonialsSection() {
  return (
    <section className="py-24 bg-gradient-to-b from-navy-50/50 via-white to-navy-50/50 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-1/4 left-0 w-72 h-72 bg-primary-100/50 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-0 w-72 h-72 bg-purple-100/50 rounded-full blur-3xl" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-6">
          <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 px-5 py-2.5 rounded-full text-sm font-bold shadow-soft">
            <Star className="w-4 h-4 fill-current" />
            4.8/5 from 47 Italian lawyers
          </div>
          <h2 className="text-4xl lg:text-5xl font-bold text-navy-900 leading-tight">
            Trusted by legal
            <span className="block mt-2 bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
              professionals
            </span>
          </h2>
          <p className="text-xl text-navy-600 leading-relaxed">
            Discover how Italian law firms save time and protect client privacy
          </p>
        </div>

        {/* Testimonials grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {testimonials.map((testimonial, index) => (
            <div
              key={testimonial.name}
              className="group relative bg-white rounded-3xl p-8 shadow-soft hover:shadow-large transition-all duration-500 border border-navy-100 hover:border-primary-200 hover:-translate-y-2"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Verified badge */}
              {testimonial.verified && (
                <div className="absolute -top-3 -right-3 bg-gradient-to-br from-emerald-500 to-emerald-600 text-white p-2 rounded-full shadow-medium">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              )}

              {/* Quote icon with gradient */}
              <div className="mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center">
                  <Quote className="w-6 h-6 text-primary-600" />
                </div>
              </div>

              {/* Rating */}
              <div className="flex gap-1 mb-6">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="w-5 h-5 text-amber-400 fill-current"
                  />
                ))}
              </div>

              {/* Quote */}
              <blockquote className="text-navy-700 mb-6 leading-relaxed text-base">
                "{testimonial.quote}"
              </blockquote>

              {/* Stats with modern design */}
              <div className="grid grid-cols-2 gap-4 mb-6 pb-6 border-b border-navy-100">
                <div className="text-center p-3 bg-gradient-to-br from-primary-50 to-blue-50 rounded-xl">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <TrendingUp className="w-4 h-4 text-primary-600" />
                    <div className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                      {testimonial.stats.documents}
                    </div>
                  </div>
                  <div className="text-xs text-navy-600 font-medium">Documents</div>
                </div>
                <div className="text-center p-3 bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Clock className="w-4 h-4 text-emerald-600" />
                    <div className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-emerald-800 bg-clip-text text-transparent">
                      {testimonial.stats.weeklySaved}
                    </div>
                  </div>
                  <div className="text-xs text-navy-600 font-medium">Per week</div>
                </div>
              </div>

              {/* Author with avatar gradient */}
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 bg-gradient-to-br ${testimonial.avatarColor} rounded-2xl flex items-center justify-center text-white font-bold text-lg shadow-medium group-hover:scale-110 transition-transform`}>
                  {testimonial.avatar}
                </div>
                <div className="flex-1">
                  <div className="font-bold text-navy-900 text-base">
                    {testimonial.name}
                  </div>
                  <div className="text-sm text-navy-600 font-medium">
                    {testimonial.role}
                  </div>
                  <div className="text-xs text-navy-500">
                    {testimonial.location}
                  </div>
                </div>
              </div>

              {/* Corner decoration */}
              <div className="absolute bottom-0 right-0 w-24 h-24 bg-gradient-to-tl from-primary-100/30 to-transparent rounded-tr-3xl pointer-events-none" />
            </div>
          ))}
        </div>

        {/* Trust indicators with enhanced design */}
        <div className="bg-gradient-to-br from-navy-900 to-navy-800 rounded-3xl p-12 shadow-large">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white px-5 py-2 rounded-full text-sm font-semibold mb-4">
              <Award className="w-4 h-4 text-amber-400" />
              <span>Join 47 Italian law firms that trust CodiceCivile.ai</span>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div className="group">
              <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium group-hover:scale-110 transition-transform">
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
              <div className="text-4xl font-bold text-white mb-2">156</div>
              <div className="text-navy-300 text-sm font-medium">Documents redacted today</div>
            </div>
            <div className="group">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium group-hover:scale-110 transition-transform">
                <CheckCircle2 className="w-8 h-8 text-white" />
              </div>
              <div className="text-4xl font-bold text-white mb-2">8,942</div>
              <div className="text-navy-300 text-sm font-medium">Total redactions</div>
            </div>
            <div className="group">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-medium group-hover:scale-110 transition-transform">
                <Clock className="w-8 h-8 text-white" />
              </div>
              <div className="text-4xl font-bold text-white mb-2">580+</div>
              <div className="text-navy-300 text-sm font-medium">Hours saved this month</div>
            </div>
          </div>

          {/* Decorative elements */}
          <div className="absolute top-0 left-0 w-32 h-32 bg-primary-500/20 rounded-full blur-2xl" />
          <div className="absolute bottom-0 right-0 w-32 h-32 bg-purple-500/20 rounded-full blur-2xl" />
        </div>
      </div>
    </section>
  )
}
