// MUST be first: Polyfill for URL.parse() (Node.js 22+ API, needed for react-pdf v10 in Electron 28)
import './polyfills/url-parse'

import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Use HashRouter for Electron file:// protocol compatibility
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>,
)
