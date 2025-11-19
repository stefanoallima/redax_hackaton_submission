/**
 * Settings Page - License Validation & App Configuration
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface LicenseStatus {
  valid: boolean
  tier: string
  expiresAt?: string
  cached?: boolean
  gracePeriod?: boolean
}

export default function SettingsPage() {
  const navigate = useNavigate()
  const [license, setLicense] = useState<LicenseStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [appVersion, setAppVersion] = useState('')

  useEffect(() => {
    loadLicenseStatus()
    loadAppVersion()
  }, [])

  const loadLicenseStatus = async () => {
    try {
      // Check cached license first
      const cached = localStorage.getItem('license_status')
      const cacheTime = localStorage.getItem('license_cache_time')
      
      const now = Date.now()
      const sevenDays = 7 * 24 * 60 * 60 * 1000
      
      // Use cache if less than 7 days old
      if (cached && cacheTime && (now - parseInt(cacheTime)) < sevenDays) {
        setLicense({ ...JSON.parse(cached), cached: true })
        setLoading(false)
        return
      }
      
      // Validate with backend API
      const userId = localStorage.getItem('user_id')
      const jwt = localStorage.getItem('jwt_token')
      
      if (!userId || !jwt) {
        setLicense({ valid: false, tier: 'none' })
        setLoading(false)
        return
      }
      
      const result = await window.electron.validateLicense(userId, jwt)
      
      if (result.valid) {
        // Cache successful validation
        localStorage.setItem('license_status', JSON.stringify(result))
        localStorage.setItem('license_cache_time', now.toString())
        setLicense(result)
      } else {
        // Check if still in grace period
        const gracePeriod = cacheTime && (now - parseInt(cacheTime)) < (sevenDays + 7 * 24 * 60 * 60 * 1000)
        
        if (gracePeriod && cached) {
          setLicense({ ...JSON.parse(cached), gracePeriod: true })
        } else {
          setLicense({ valid: false, tier: 'none' })
        }
      }
      
      setLoading(false)
    } catch (error) {
      console.error('License validation error:', error)
      
      // Use cached license in case of network error
      const cached = localStorage.getItem('license_status')
      if (cached) {
        setLicense({ ...JSON.parse(cached), cached: true })
      } else {
        setLicense({ valid: false, tier: 'none' })
      }
      
      setLoading(false)
    }
  }

  const loadAppVersion = async () => {
    try {
      const version = await window.electron.getAppVersion()
      setAppVersion(version)
    } catch (error) {
      console.error('Error loading app version:', error)
    }
  }

  const handleRefreshLicense = () => {
    // Clear cache and reload
    localStorage.removeItem('license_status')
    localStorage.removeItem('license_cache_time')
    setLoading(true)
    loadLicenseStatus()
  }

  const handleLogin = () => {
    // Open login in system browser
    window.open('https://redaxai.app/login', '_blank')
  }

  const handleUpgrade = () => {
    // Open pricing page
    window.open('https://redaxai.app/pricing', '_blank')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-semibold">Settings</h1>
        </div>
      </header>

      <div className="max-w-4xl mx-auto p-8">
        {/* License Status */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">License Status</h2>

          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="mt-2 text-gray-600">Validating license...</p>
            </div>
          ) : license?.valid ? (
            <div>
              <div className="flex items-start gap-3 mb-4">
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-green-900">
                    {license.gracePeriod ? 'Grace Period - License Validation Failed' : 'Active License'}
                  </p>
                  <p className="text-sm text-gray-600">
                    Plan: <span className="font-medium capitalize">{license.tier}</span>
                  </p>
                  {license.cached && (
                    <p className="text-xs text-gray-500 mt-1">
                      Cached license (validated within the last 7 days)
                    </p>
                  )}
                  {license.gracePeriod && (
                    <p className="text-sm text-amber-600 mt-2">
                      <AlertCircle className="inline w-4 h-4 mr-1" />
                      License validation failed. Grace period active for 7 more days.
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={handleRefreshLicense}
                className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
              >
                Refresh License
              </button>
            </div>
          ) : (
            <div>
              <div className="flex items-start gap-3 mb-4">
                <XCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
                <div>
                  <p className="font-medium text-red-900">No Active License</p>
                  <p className="text-sm text-gray-600">
                    An active subscription is required to use this app
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleLogin}
                  className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
                >
                  Log In
                </button>
                <button
                  onClick={handleUpgrade}
                  className="px-4 py-2 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
                >
                  Subscribe Now
                </button>
              </div>
            </div>
          )}
        </div>

        {/* App Info */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Application Information</h2>

          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Version</span>
              <span className="font-medium">{appVersion || 'Unknown'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Platform</span>
              <span className="font-medium">Windows</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Document Reading</span>
              <span className="font-medium">Advanced Text Recognition</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Data Detection</span>
              <span className="font-medium">Artificial Intelligence</span>
            </div>
          </div>
        </div>

        {/* Subscription Tiers Info */}
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-lg font-semibold mb-4">Subscription Plans</h2>

          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="font-medium">Premium - €19/month</h3>
              <p className="text-sm text-gray-600">50 documents/month, desktop app access</p>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <h3 className="font-medium">Professional - €25/month</h3>
              <p className="text-sm text-gray-600">Unlimited documents, priority support</p>
            </div>

            <div className="border-l-4 border-yellow-500 pl-4">
              <h3 className="font-medium">Enterprise - €99/month</h3>
              <p className="text-sm text-gray-600">Team access, API, customization</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
