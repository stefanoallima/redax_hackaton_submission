/**
 * Electron Main Process - Unified Gradio Frontend
 * Embeds Gradio web app running on localhost:7860
 *
 * Architecture: Electron window → http://localhost:7860 → Gradio → shared_backend
 */

import { app, BrowserWindow, Menu, shell, dialog } from 'electron'
import { spawn, ChildProcess } from 'child_process'
import path from 'path'
import net from 'net'
import fs from 'fs'

let mainWindow: BrowserWindow | null = null
let gradioProcess: ChildProcess | null = null
let splashWindow: BrowserWindow | null = null

const GRADIO_PORT = 7860
const GRADIO_STARTUP_TIMEOUT = 60000 // 60 seconds
const isDev = !app.isPackaged

// =============================================================================
// PYTHON PATH UTILITIES
// =============================================================================

function getPythonPath(): string {
  if (isDev) {
    // Development: use system Python
    return process.platform === 'win32' ? 'python' : 'python3'
  }

  // Production: check for bundled Python (if you bundle it)
  const bundledPython = path.join(
    process.resourcesPath,
    'python',
    process.platform === 'win32' ? 'python.exe' : 'bin/python3'
  )

  if (fs.existsSync(bundledPython)) {
    return bundledPython
  }

  // Fallback to system Python
  return process.platform === 'win32' ? 'python' : 'python3'
}

function getGradioAppPath(): string {
  if (isDev) {
    // Development: use web/app.py from project root
    return path.join(__dirname, '../../../web/app.py')
  }

  // Production: use bundled app.py in resources
  return path.join(process.resourcesPath, 'web', 'app.py')
}

function getSharedBackendPath(): string {
  if (isDev) {
    return path.join(__dirname, '../../../shared_backend')
  }

  return path.join(process.resourcesPath, 'shared_backend')
}

// =============================================================================
// PORT CHECKING
// =============================================================================

function checkPort(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new net.Socket()
    socket.setTimeout(1000)

    socket.on('connect', () => {
      socket.destroy()
      resolve(true)
    })

    socket.on('error', () => resolve(false))
    socket.on('timeout', () => {
      socket.destroy()
      resolve(false)
    })

    socket.connect(port, '127.0.0.1')
  })
}

async function waitForGradioReady(maxAttempts = 60): Promise<void> {
  for (let i = 0; i < maxAttempts; i++) {
    const isReady = await checkPort(GRADIO_PORT)
    if (isReady) {
      console.log(`✓ Gradio server ready after ${i + 1} attempts`)
      return
    }
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  throw new Error(`Gradio server did not become ready after ${maxAttempts} seconds`)
}

// =============================================================================
// GRADIO SERVER MANAGEMENT
// =============================================================================

function startGradioServer(): Promise<void> {
  return new Promise((resolve, reject) => {
    const pythonPath = getPythonPath()
    const appPath = getGradioAppPath()
    const backendPath = getSharedBackendPath()

    console.log('Starting Gradio server...')
    console.log(`Python: ${pythonPath}`)
    console.log(`App: ${appPath}`)
    console.log(`Backend: ${backendPath}`)

    // Verify files exist
    if (!fs.existsSync(appPath)) {
      reject(new Error(`Gradio app not found: ${appPath}`))
      return
    }

    if (!fs.existsSync(backendPath)) {
      reject(new Error(`Shared backend not found: ${backendPath}`))
      return
    }

    // Set environment variables
    const env = {
      ...process.env,
      ELECTRON: '1',  // Tell Gradio it's running in Electron
      PYTHONUNBUFFERED: '1',  // Real-time output
      // Optionally set GEMINI_API_KEY here if stored in Electron settings
    }

    // Start Gradio process
    gradioProcess = spawn(pythonPath, [appPath], {
      env,
      cwd: path.dirname(appPath)
    })

    let startupOutput = ''

    gradioProcess.stdout?.on('data', (data) => {
      const output = data.toString()
      console.log(`[Gradio] ${output}`)
      startupOutput += output

      // Detect when Gradio is ready
      if (output.includes('Running on') || output.includes('http://127.0.0.1:7860')) {
        console.log('✓ Gradio server started successfully')
        resolve()
      }
    })

    gradioProcess.stderr?.on('data', (data) => {
      const error = data.toString()
      console.error(`[Gradio ERROR] ${error}`)

      // Don't reject on stderr - some libraries print warnings there
      // Only reject on actual process errors
    })

    gradioProcess.on('error', (error) => {
      console.error('Failed to start Gradio process:', error)
      reject(error)
    })

    gradioProcess.on('exit', (code, signal) => {
      console.log(`Gradio process exited with code ${code}, signal ${signal}`)
      gradioProcess = null

      // If app is still running, show error
      if (mainWindow && !mainWindow.isDestroyed()) {
        dialog.showErrorBox(
          'Backend Crashed',
          `Gradio server stopped unexpectedly.\n\nExit code: ${code}\n\nThe application will close.`
        )
        app.quit()
      }
    })

    // Timeout
    setTimeout(() => {
      if (gradioProcess && !gradioProcess.killed) {
        reject(new Error(`Gradio server did not start within ${GRADIO_STARTUP_TIMEOUT / 1000}s\n\nOutput:\n${startupOutput}`))
      }
    }, GRADIO_STARTUP_TIMEOUT)
  })
}

function stopGradioServer() {
  if (gradioProcess && !gradioProcess.killed) {
    console.log('Stopping Gradio server...')
    gradioProcess.kill('SIGTERM')

    // Force kill after 5 seconds if still running
    setTimeout(() => {
      if (gradioProcess && !gradioProcess.killed) {
        console.log('Force killing Gradio server...')
        gradioProcess.kill('SIGKILL')
      }
    }, 5000)
  }
}

// =============================================================================
// SPLASH SCREEN
// =============================================================================

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 500,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    center: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  // Simple HTML splash screen
  const splashHTML = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: white;
          }
          .container {
            text-align: center;
          }
          h1 {
            font-size: 32px;
            margin-bottom: 20px;
          }
          .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          p {
            margin-top: 20px;
            font-size: 14px;
            opacity: 0.9;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>🤖 Redactor AI</h1>
          <div class="spinner"></div>
          <p>Starting application...</p>
        </div>
      </body>
    </html>
  `

  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHTML)}`)
}

function closeSplashWindow() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close()
    splashWindow = null
  }
}

// =============================================================================
// MAIN WINDOW
// =============================================================================

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    title: 'Redactor AI',
    backgroundColor: '#ffffff',
    show: false,  // Don't show until ready
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      // No preload needed - Gradio handles everything
    }
  })

  // Load Gradio interface
  mainWindow.loadURL(`http://127.0.0.1:${GRADIO_PORT}`)

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    closeSplashWindow()
    mainWindow!.show()
    mainWindow!.focus()
  })

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools()
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // Open external links in system browser
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url)
      return { action: 'deny' }
    }
    return { action: 'allow' }
  })
}

// =============================================================================
// APPLICATION MENU
// =============================================================================

function createApplicationMenu() {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow?.reload()
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Alt+F4',
          click: () => app.quit()
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Toggle Developer Tools',
          accelerator: process.platform === 'darwin' ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
          click: () => mainWindow?.webContents.toggleDevTools()
        },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => shell.openExternal('https://github.com/yourusername/redactor-ai')
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox({
              type: 'info',
              title: 'About Redactor AI',
              message: 'Redactor AI',
              detail: 'Intelligent PII Detection & Redaction\n\nVersion: 1.0.0\nPowered by Google Gemini 2.5 Pro'
            })
          }
        }
      ]
    }
  ]

  // Add macOS-specific menu items
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    })
  }

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

// =============================================================================
// APPLICATION LIFECYCLE
// =============================================================================

app.whenReady().then(async () => {
  try {
    console.log('=== Redactor AI Starting ===')
    console.log(`Mode: ${isDev ? 'Development' : 'Production'}`)
    console.log(`Platform: ${process.platform}`)

    // Show splash screen
    createSplashWindow()

    // Start Gradio server
    console.log('Starting Gradio server...')
    await startGradioServer()

    // Wait for server to be ready
    console.log('Waiting for Gradio server to be ready...')
    await waitForGradioReady()

    // Create main window
    console.log('Creating main window...')
    createMainWindow()

    // Create application menu
    createApplicationMenu()

    console.log('=== Redactor AI Started Successfully ===')
  } catch (error) {
    console.error('Failed to start application:', error)

    closeSplashWindow()

    dialog.showErrorBox(
      'Startup Error',
      `Failed to start Redactor AI:\n\n${error instanceof Error ? error.message : String(error)}\n\nPlease ensure Python and required packages are installed.`
    )

    app.quit()
  }
})

// macOS: Re-create window when dock icon is clicked
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow()
  }
})

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Clean up before quitting
app.on('before-quit', () => {
  console.log('Application quitting, stopping Gradio server...')
  stopGradioServer()
})

// Handle unexpected errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error)
  dialog.showErrorBox('Unexpected Error', `An unexpected error occurred:\n\n${error.message}`)
})

process.on('unhandledRejection', (reason) => {
  console.error('Unhandled rejection:', reason)
})
