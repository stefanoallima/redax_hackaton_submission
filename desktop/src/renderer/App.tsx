/**
 * Main React App Component
 */
import { useEffect, useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import WelcomePage from './pages/WelcomePage'
import StandardModePage from './pages/StandardModePage'
import ProcessPage from './pages/ProcessPage'
import ReviewPage from './pages/ReviewPage'
import SettingsPage from './pages/SettingsPage'
import { TeachingModePage } from './pages/TeachingModePage'

interface PythonStatus {
  status: 'running' | 'crashed' | 'failed'
  code?: number
  canRestart?: boolean
  message?: string
}

function App() {
  const [pythonStatus, setPythonStatus] = useState<PythonStatus>({ status: 'running' })

  useEffect(() => {
    // Listen for Python status updates
    const handlePythonStatus = (status: PythonStatus) => {
      setPythonStatus(status)

      // Show alert for critical status changes
      if (status.status === 'crashed' && status.canRestart) {
        console.warn('⚠️ Processing engine crashed. Restarting automatically...')
      } else if (status.status === 'failed') {
        console.error('❌ Processing engine failed to start.')
      }
    }

    window.electron.onPythonStatus(handlePythonStatus)

    return () => {
      window.electron.removePythonStatusListener()
    }
  }, [])

  const handleManualRestart = async () => {
    try {
      await window.electron.restartPython()
      setPythonStatus({ status: 'running' })
    } catch (error) {
      console.error('Failed to restart Python:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Python Status Notification Banner */}
      {pythonStatus.status !== 'running' && (
        <div
          className={`
            fixed top-0 left-0 right-0 z-50 p-3 text-white text-center font-medium
            ${pythonStatus.status === 'crashed' ? 'bg-yellow-600' : 'bg-red-600'}
          `}
        >
          <div className="flex items-center justify-center gap-4">
            <span>
              ⚠️ Processing engine is {pythonStatus.status === 'crashed' ? 'restarting' : 'unavailable'}
              {pythonStatus.canRestart && ' - Attempting automatic recovery...'}
            </span>
            {pythonStatus.status === 'failed' && (
              <button
                onClick={handleManualRestart}
                className="px-4 py-1 bg-white text-red-600 rounded hover:bg-gray-100 transition-colors"
              >
                Restart Manually
              </button>
            )}
          </div>
          {pythonStatus.message && (
            <div className="text-sm mt-1 opacity-90">{pythonStatus.message}</div>
          )}
        </div>
      )}

      {/* Main Routes */}
      <div className={pythonStatus.status !== 'running' ? 'mt-16' : ''}>
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          <Route path="/standard" element={<StandardModePage />} />
          <Route path="/teaching" element={<TeachingModePage />} />
          <Route path="/process" element={<ProcessPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
