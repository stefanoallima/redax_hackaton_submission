/**
 * Electron Main Process
 * Handles window management, IPC, and Python subprocess
 */
import { app, BrowserWindow, ipcMain, net } from 'electron'
import path from 'path'
import fs from 'fs'
import { spawn, ChildProcess } from 'child_process'
import type { IPCCommand, ProcessDocumentCommand, ExportRedactedCommand } from '../types/ipc'

let mainWindow: BrowserWindow | null = null
let pythonProcess: ChildProcess | null = null
let pythonRestartAttempts = 0
const MAX_RESTART_ATTEMPTS = 3

// Enhanced error logging
const pythonLog = {
  stdout: [] as string[],
  stderr: [] as string[],
  crashes: [] as { time: Date, code: number | null, stderr: string[] }[],
  maxLogSize: 1000
}

function logPythonCrash(code: number | null) {
  const crashInfo = {
    time: new Date(),
    code,
    stderr: pythonLog.stderr.slice(-50) // Last 50 stderr lines
  }
  pythonLog.crashes.push(crashInfo)
  console.error('=== Python Process Crash ===')
  console.error(`Time: ${crashInfo.time.toISOString()}`)
  console.error(`Exit code: ${code}`)
  console.error('Recent stderr:')
  crashInfo.stderr.forEach(line => console.error(`  ${line}`))
  console.error('===========================')

  // Also save to file in app data directory
  const logPath = path.join(app.getPath('userData'), 'python-crashes.log')
  const logEntry = `\n=== Crash at ${crashInfo.time.toISOString()} ===\nExit code: ${code}\nStderr:\n${crashInfo.stderr.join('\n')}\n`
  fs.appendFileSync(logPath, logEntry, 'utf-8')
  console.log(`Crash log saved to: ${logPath}`)
}

// Check if running in development mode
// In test mode, always use built files (not dev server)
const isDev = !app.isPackaged && process.env.NODE_ENV !== 'test'

// In development, allow insecure origins for localhost
if (isDev) {
  app.commandLine.appendSwitch('unsafely-treat-insecure-origin-as-secure', 'http://localhost:5173')
}

// File validation constants
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt']

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true, // Keep web security enabled
    },
    title: 'OscuraTesti AI',
    backgroundColor: '#ffffff',
  })

  // Grant permissions for media devices (microphone for speech recognition)
  mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
    const allowedPermissions = ['media', 'microphone', 'audioCapture']
    if (allowedPermissions.includes(permission)) {
      console.log(`✓ Granting permission: ${permission}`)
      callback(true)
    } else {
      console.warn(`✗ Denying permission: ${permission}`)
      callback(false)
    }
  })

  // Also handle permission checks (pre-grant before request)
  mainWindow.webContents.session.setPermissionCheckHandler((webContents, permission) => {
    const allowedPermissions = ['media', 'microphone', 'audioCapture']
    const isAllowed = allowedPermissions.includes(permission)
    console.log(`🔐 Permission check for ${permission}: ${isAllowed ? 'ALLOWED' : 'DENIED'}`)
    return isAllowed
  })

  // Load renderer
  if (isDev) {
    // Try multiple ports in case default is taken
    const tryLoadDevServer = async () => {
      const ports = [5173, 5174, 5175, 5176, 5177, 5178, 5179, 5180]
      for (const port of ports) {
        try {
          // Use Electron's net module to check if port is serving content
          const url = `http://localhost:${port}`
          const request = net.request(url)

          await new Promise<void>((resolve, reject) => {
            request.on('response', (response) => {
              if (response.statusCode === 200) {
                resolve()
              } else {
                reject(new Error(`Status ${response.statusCode}`))
              }
            })
            request.on('error', reject)
            request.end()
          })

          // If we get here, the port is valid
          await mainWindow!.loadURL(url)
          console.log(`✓ Loaded dev server from port ${port}`)
          mainWindow!.webContents.openDevTools()
          return
        } catch (err) {
          console.log(`✗ Port ${port} not available`)
        }
      }
      console.error('❌ Could not connect to dev server on any port')
    }
    tryLoadDevServer()
  } else {
    // In built mode, __dirname is dist/electron/electron
    // We need to go up 2 levels to dist/, then access renderer/
    const rendererPath = path.join(__dirname, '..', '..', 'renderer', 'index.html')
    console.log(`Loading renderer from: ${rendererPath}`)
    console.log(`Renderer exists: ${fs.existsSync(rendererPath)}`)
    mainWindow.loadFile(rendererPath)
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// Safe write to Python stdin with EPIPE error handling
function writeToPython(data: string): boolean {
  if (!pythonProcess || !pythonProcess.stdin || pythonProcess.stdin.destroyed) {
    console.warn('Cannot write to Python: process not running or stdin closed')
    return false
  }

  try {
    return pythonProcess.stdin.write(data, (error) => {
      if (error) {
        // EPIPE means the pipe was closed - this is expected during shutdown
        if ((error as any).code === 'EPIPE') {
          console.log('Python stdin pipe closed (expected during shutdown)')
        } else {
          console.error('Error writing to Python stdin:', error)
        }
      }
    })
  } catch (error: any) {
    if (error.code === 'EPIPE') {
      console.log('Caught EPIPE while writing to Python (expected during shutdown)')
    } else {
      console.error('Exception writing to Python stdin:', error)
    }
    return false
  }
}

// Start Python backend process with crash recovery
function startPythonProcess() {
  // Determine Python paths based on app state
  let pythonScriptPath: string
  let pythonExecutable: string

  if (app.isPackaged) {
    // Production: Python files are unpacked from asar (asarUnpack in package.json)
    pythonScriptPath = path.join(process.resourcesPath, 'app.asar.unpacked', 'src', 'python', 'main.py')
    pythonExecutable = path.join(process.resourcesPath, 'app.asar.unpacked', 'src', 'python', 'venv', 'Scripts', 'python.exe')
  } else {
    // Development or built (E2E tests)
    const appPath = app.getAppPath()
    let basePath: string

    // If running from dist folder, navigate back to project root
    if (appPath.includes(path.join('dist', 'electron'))) {
      // app.getAppPath() returns .../desktop/dist/electron/electron
      // We need to go up 3 levels to get to desktop/
      basePath = path.join(appPath, '..', '..', '..')
    } else {
      // Running directly from source
      basePath = appPath
    }

    pythonScriptPath = path.join(basePath, 'src', 'python', 'main.py')
    pythonExecutable = path.join(basePath, 'src', 'python', 'venv', 'Scripts', 'python.exe')
  }

  console.log(`Starting Python process (attempt ${pythonRestartAttempts + 1}/${MAX_RESTART_ATTEMPTS + 1})`)
  console.log(`  Python script: ${pythonScriptPath}`)
  console.log(`  Python executable: ${pythonExecutable}`)
  console.log(`  Script exists: ${fs.existsSync(pythonScriptPath)}`)
  console.log(`  Executable exists: ${fs.existsSync(pythonExecutable)}`)

  // Enable new integrated PII detector (faster, more accurate)
  const pythonEnv = {
    ...process.env,
    USE_NEW_PII_DETECTOR: 'true'
  }

  // Set working directory to Python source directory so imports work correctly
  const pythonWorkingDir = path.dirname(pythonScriptPath)

  pythonProcess = spawn(pythonExecutable, [pythonScriptPath], {
    env: pythonEnv,
    cwd: pythonWorkingDir  // Fix: Set working directory for Python imports
  })

  // Handle stdin errors (especially EPIPE during shutdown)
  if (pythonProcess.stdin) {
    pythonProcess.stdin.on('error', (error: any) => {
      if (error.code === 'EPIPE') {
        console.log('Python stdin pipe closed (expected during shutdown)')
      } else {
        console.error('Python stdin error:', error)
      }
    })
  }

  // Note: We don't attach a global stdout listener here because it would
  // interfere with IPC handlers that use .once('data', ...) to wait for responses.
  // Each IPC handler sets up its own listener when needed.

  // Capture stdout for diagnostics (non-blocking)
  pythonProcess.stdout?.on('data', (data) => {
    const lines = data.toString().split('\n').filter((l: string) => l.trim())
    pythonLog.stdout.push(...lines)
    if (pythonLog.stdout.length > pythonLog.maxLogSize) {
      pythonLog.stdout = pythonLog.stdout.slice(-pythonLog.maxLogSize)
    }
  })

  pythonProcess.stderr?.on('data', (data) => {
    const stderrText = data.toString()
    console.error(`Python stderr: ${stderrText}`)

    // Capture for crash analysis
    const lines = stderrText.split('\n').filter((l: string) => l.trim())
    pythonLog.stderr.push(...lines)
    if (pythonLog.stderr.length > pythonLog.maxLogSize) {
      pythonLog.stderr = pythonLog.stderr.slice(-pythonLog.maxLogSize)
    }

    // Check for critical errors
    if (stderrText.toLowerCase().includes('error') ||
        stderrText.toLowerCase().includes('exception') ||
        stderrText.toLowerCase().includes('traceback')) {
      console.error('!!! Critical error detected in Python process !!!')
      console.error(stderrText)
    }
  })

  pythonProcess.on('close', (code) => {
    console.error(`Python process exited with code ${code}`)

    // Log crash with detailed diagnostics
    logPythonCrash(code)

    pythonProcess = null

    // Notify renderer about crash
    if (mainWindow) {
      mainWindow.webContents.send('python-status', {
        status: 'crashed',
        code,
        canRestart: pythonRestartAttempts < MAX_RESTART_ATTEMPTS
      })
    }

    // Auto-restart with exponential backoff
    if (pythonRestartAttempts < MAX_RESTART_ATTEMPTS) {
      pythonRestartAttempts++
      const delay = Math.pow(2, pythonRestartAttempts) * 1000 // 2s, 4s, 8s

      console.log(`Restarting Python in ${delay}ms...`)
      setTimeout(() => {
        startPythonProcess()
      }, delay)
    } else {
      console.error('Max restart attempts reached. Python backend unavailable.')
      if (mainWindow) {
        mainWindow.webContents.send('python-status', {
          status: 'failed',
          message: 'Python backend failed to start after multiple attempts. Please restart the application.'
        })
      }
    }
  })

  // Reset restart counter on successful spawn
  pythonProcess.on('spawn', () => {
    pythonRestartAttempts = 0
    console.log('Python process started successfully')
  })
}

// Helper function to validate file path
function validateFilePath(filePath: string): void {
  // Check if file exists
  if (!fs.existsSync(filePath)) {
    throw new Error('File not found')
  }

  // Check file size
  const stats = fs.statSync(filePath)
  if (stats.size > MAX_FILE_SIZE) {
    throw new Error(`File too large (max ${MAX_FILE_SIZE / 1024 / 1024}MB)`)
  }

  // Check file extension
  const ext = path.extname(filePath).toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    throw new Error(`Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`)
  }

  // Prevent directory traversal
  const normalizedPath = path.normalize(filePath)
  if (normalizedPath.includes('..')) {
    throw new Error('Invalid file path')
  }
}

// IPC Handlers
ipcMain.handle('process-document', async (event, command: IPCCommand) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  // Validate file path for security
  if ('file_path' in command) {
    validateFilePath(command.file_path)
  }

  // Send entire command to Python (includes file_path and config)
  const commandStr = JSON.stringify(command)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  // Wait for response - handle potentially large multi-chunk responses
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Python process timeout (180 seconds). The document may be too large or complex. Please try a smaller file or contact support.'))
    }, 180000) // 180 second timeout (3 minutes)

    let buffer = ''

    const dataHandler = (data: Buffer) => {
      buffer += data.toString()

      // Try to parse accumulated buffer as JSON
      // Python sends complete JSON on a single line ending with \n
      const lines = buffer.split('\n')

      // Process complete lines (all but the last, which may be incomplete)
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)

          // Skip the "ready" signal - we're waiting for the actual result
          if (result.status === 'ready') {
            continue
          }

          // We got a complete response!
          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          // Debug logging to track data flow
          console.log('IPC Handler - Received from Python:')
          console.log(`  Status: ${result.status}`)
          console.log(`  Entities count: ${result.entities?.length || 0}`)
          if (result.entities && result.entities.length > 0) {
            console.log(`  First entity: ${JSON.stringify(result.entities[0])}`)
          }
          console.log(`  Summary: ${JSON.stringify(result.summary)}`)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Line is not complete JSON yet, continue accumulating
          console.error(`IPC Handler - Failed to parse line: ${line.substring(0, 100)}...`)
        }
      }

      // Keep the last incomplete line in the buffer
      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// Manual Python restart handler
ipcMain.handle('restart-python', async () => {
  console.log('Manual Python restart requested')
  if (pythonProcess) {
    pythonProcess.kill()
  }
  pythonRestartAttempts = 0
  startPythonProcess()
})

ipcMain.handle('validate-license', async (event, userId: string, jwt: string) => {
  // Call backend API to validate license
  // TODO: Implement license validation (Task 1.8)
  return { valid: true, tier: 'professional' }
})

ipcMain.handle('get-app-version', async () => {
  return app.getVersion()
})

// Diagnostic handler to get Python crash logs
ipcMain.handle('get-python-diagnostics', async () => {
  return {
    crashes: pythonLog.crashes,
    recentStdout: pythonLog.stdout.slice(-100),
    recentStderr: pythonLog.stderr.slice(-100),
    restartAttempts: pythonRestartAttempts,
    processRunning: pythonProcess !== null,
    logPath: path.join(app.getPath('userData'), 'python-crashes.log')
  }
})

// Gemini AI Integration Handlers
ipcMain.handle('gemini-scan', async (event, payload: { file_path: string; prompt?: string }) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  // Validate file path for security
  validateFilePath(payload.file_path)

  const command = {
    action: 'gemini_scan',
    file_path: payload.file_path,
    prompt: payload.prompt
  }

  const commandStr = JSON.stringify(command)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  // Wait for response with 200 second timeout (Gemini API can be slow)
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Gemini scan timeout (200 seconds). The API may be overloaded. Please try again.'))
    }, 200000)

    let buffer = ''

    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)

          // Skip the "ready" signal
          if (result.status === 'ready') {
            continue
          }

          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          console.log('Gemini Scan - Received from Python:')
          console.log(`  Status: ${result.status}`)
          console.log(`  Entities count: ${result.entities?.length || 0}`)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Line is not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// Teach Template - Get bounding boxes for blank templates
ipcMain.handle('teach-template', async (event, payload: { file_path: string; voice_command: string; description?: string }) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  // Validate file path for security
  validateFilePath(payload.file_path)

  const command = {
    action: 'teach_template',
    file_path: payload.file_path,
    voice_command: payload.voice_command,
    description: payload.description || null
  }

  const commandStr = JSON.stringify(command)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  // Wait for response with 200 second timeout (Gemini API can be slow)
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Template teaching timeout (200 seconds). The API may be overloaded. Please try again.'))
    }, 200000)

    let buffer = ''

    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)

          // Skip the "ready" signal
          if (result.status === 'ready') {
            continue
          }

          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          console.log('Teach Template - Received from Python:')
          console.log(`  Status: ${result.status}`)
          console.log(`  Regions count: ${result.regions?.length || 0}`)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Line is not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})
ipcMain.handle('learn-from-gemini', async (event, payload: { confirmed_entities: any[]; denied_entities: any[] }) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  const command = {
    action: 'learn_from_gemini',
    confirmed_entities: payload.confirmed_entities || [],
    denied_entities: payload.denied_entities || []
  }

  const commandStr = JSON.stringify(command)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Learning timeout (10 seconds)'))
    }, 10000)

    let buffer = ''

    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)

          if (result.status === 'ready') {
            continue
          }

          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          console.log('Learn from Gemini - Received from Python:')
          console.log(`  Status: ${result.status}`)
          console.log(`  Learned count: ${result.learned_count || 0}`)
          console.log(`  Total learned: ${result.total_learned || 0}`)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Line is not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

ipcMain.handle('get-learned-stats', async () => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  const command = {
    action: 'get_learned_stats'
  }

  const commandStr = JSON.stringify(command)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Get stats timeout (5 seconds)'))
    }, 5000)

    let buffer = ''

    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)

          if (result.status === 'ready') {
            continue
          }

          // Only process responses for THIS action
          if (result.action && result.action !== 'get_learned_stats') {
            console.log('Get learned stats - Skipping response for different action:', result.action)
            continue
          }

          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Line is not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// Save template handler
console.log('✅ Registering save-template IPC handler')
ipcMain.handle('save-template', async (event, payload: {
  template_id: string
  cache_name: string
  description: string
  regions: any[]
  created_at: string
  expires_at: string
  voice_command: string
}) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  console.log('Save template - Received payload:', payload)

  const command = {
    action: 'save_template',
    template_id: payload.template_id,
    cache_name: payload.cache_name,
    description: payload.description,
    regions: payload.regions,
    created_at: payload.created_at,
    expires_at: payload.expires_at,
    voice_command: payload.voice_command
  }

  const commandStr = JSON.stringify(command)
  console.log('Save template - Sending to Python:', commandStr)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Save template timeout (60 seconds). The template may be too large.'))
    }, 60000)

    let buffer = ''

    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)

          if (result.status === 'ready') {
            continue
          }

          console.log('Save template - Received from Python:', result)
          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Line is not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// List templates handler
console.log('✅ Registering list-templates IPC handler')
ipcMain.handle('list-templates', async () => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  const command = { action: 'list_templates' }
  const commandStr = JSON.stringify(command)
  console.log('List templates - Sending to Python')
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('List templates timeout'))
    }, 5000)

    let buffer = ''
    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)
          if (result.status === 'ready') continue

          // Only process responses for THIS action
          if (result.action && result.action !== 'list_templates') {
            console.log('List templates - Skipping response for different action:', result.action)
            continue
          }

          console.log('List templates - Received:', result)
          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// Load template handler
console.log('✅ Registering load-template IPC handler')
ipcMain.handle('load-template', async (event, template_id: string) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  const command = { action: 'load_template', template_id }
  const commandStr = JSON.stringify(command)
  console.log(`Load template - Sending to Python: ${template_id}`)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Load template timeout'))
    }, 5000)

    let buffer = ''
    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)
          if (result.status === 'ready') continue

          // Only process responses for THIS action
          if (result.action && result.action !== 'load_template') {
            console.log('Load template - Skipping response for different action:', result.action)
            continue
          }

          console.log('Load template - Received:', result)
          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// Apply template handler
console.log('✅ Registering apply-template IPC handler')
ipcMain.handle('apply-template', async (event, file_path: string, template_id: string) => {
  if (!pythonProcess) {
    throw new Error('Python process not running')
  }

  const command = { action: 'apply_template', file_path, template_id }
  const commandStr = JSON.stringify(command)
  console.log(`Apply template - Sending to Python: ${template_id} for ${file_path}`)
  if (!writeToPython(commandStr + '\n')) {
    throw new Error('Failed to send command to Python process')
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pythonProcess!.stdout?.removeAllListeners('data')
      reject(new Error('Apply template timeout'))
    }, 10000)  // 10 second timeout for PDF extraction

    let buffer = ''
    const dataHandler = (data: Buffer) => {
      buffer += data.toString()
      const lines = buffer.split('\n')

      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim()
        if (!line) continue

        try {
          const result = JSON.parse(line)
          if (result.status === 'ready') continue

          // Only process responses for THIS action
          if (result.action && result.action !== 'apply_template') {
            console.log('Apply template - Skipping response for different action:', result.action)
            continue
          }

          console.log('Apply template - Received:', result)
          clearTimeout(timeout)
          pythonProcess!.stdout?.removeListener('data', dataHandler)

          if (result.status === 'error') {
            reject(new Error(result.error))
          } else {
            resolve(result)
          }
          return
        } catch (e) {
          // Not complete JSON yet
        }
      }

      buffer = lines[lines.length - 1]
    }

    pythonProcess!.stdout?.on('data', dataHandler)
  })
})

// App lifecycle
app.whenReady().then(() => {
  createWindow()
  startPythonProcess()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// Clean shutdown of Python process
function cleanupPythonProcess() {
  if (pythonProcess) {
    console.log('Cleaning up Python process...')

    // Close stdin first to prevent EPIPE errors
    if (pythonProcess.stdin && !pythonProcess.stdin.destroyed) {
      try {
        pythonProcess.stdin.end()
        console.log('Python stdin closed')
      } catch (error) {
        console.log('Error closing stdin:', error)
      }
    }

    // Give Python a moment to finish current operation
    setTimeout(() => {
      if (pythonProcess) {
        console.log('Killing Python process')
        pythonProcess.kill()
      }
    }, 100)
  }
}

app.on('window-all-closed', () => {
  cleanupPythonProcess()

  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  cleanupPythonProcess()
})
