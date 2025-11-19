/**
 * Global TypeScript declarations for Electron renderer process
 */

// Electron IPC API exposed via preload script
interface ElectronAPI {
  processDocument(params: {
    action: string
    file_path?: string
    entities?: any[]
    config?: any
    [key: string]: any
  }): Promise<any>

  validateLicense(userId: string, jwt: string): Promise<{
    valid: boolean
    tier: string
    expiresAt?: string
  }>

  getAppVersion(): Promise<string>

  // Python process management
  restartPython(): Promise<void>

  // Python status listeners
  onPythonMessage(callback: (message: any) => void): void
  onPythonStatus(callback: (status: any) => void): void
  removePythonMessageListener(): void
  removePythonStatusListener(): void

  // IPC Renderer for custom channels (Gemini, etc.)
  ipcRenderer: {
    invoke(channel: string, ...args: any[]): Promise<any>
  }
}

// Extend Window interface
declare global {
  interface Window {
    electron: ElectronAPI
  }
}

export {}
