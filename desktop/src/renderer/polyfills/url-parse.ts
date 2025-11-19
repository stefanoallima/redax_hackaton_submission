/**
 * Polyfill for URL.parse() - only available in Node.js 22+
 * This polyfill is needed for react-pdf v10 to work in Electron 28 (Node.js 18)
 */

// @ts-ignore - Adding to global URL object
if (typeof URL !== 'undefined' && !URL.parse) {
  // @ts-ignore
  URL.parse = (url: string, base?: string): URL | null => {
    try {
      return new URL(url, base)
    } catch {
      return null
    }
  }

  console.log('✅ URL.parse() polyfill loaded')
}

export {}
