/**
 * Electron Preload Script
 * Exposes safe IPC methods to renderer process
 */
import { contextBridge, ipcRenderer } from 'electron'
import type { IPCCommand, ProcessDocumentResponse, ExportRedactedResponse } from '../types/ipc'

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('electron', {
  // Document processing - Type-safe with proper interfaces
  processDocument: (command: IPCCommand) =>
    ipcRenderer.invoke('process-document', command),

  // License validation
  validateLicense: (userId: string, jwt: string) =>
    ipcRenderer.invoke('validate-license', userId, jwt),

  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  // Python process management
  restartPython: () => ipcRenderer.invoke('restart-python'),

  // Listen to Python messages
  onPythonMessage: (callback: (message: any) => void) => {
    ipcRenderer.on('python-message', (_event, message) => callback(message))
  },

  // Listen to Python status updates
  onPythonStatus: (callback: (status: any) => void) => {
    ipcRenderer.on('python-status', (_event, status) => callback(status))
  },

  // Remove listeners
  removePythonMessageListener: () => {
    ipcRenderer.removeAllListeners('python-message')
  },

  removePythonStatusListener: () => {
    ipcRenderer.removeAllListeners('python-status')
  },

  // Gemini AI Integration
  ipcRenderer: {
    invoke: (channel: string, ...args: any[]) => {
      // Whitelist allowed channels for security
      const validChannels = [
        'gemini-scan',
        'learn-from-gemini',
        'get-learned-stats',
        'save-template',
        'list-templates',
        'load-template',
        'apply-template',
        'teach-template',
        'text-to-speech'
      ]
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args)
      }
      throw new Error(`Invalid IPC channel: ${channel}`)
    }
  },
})

// Type definitions for window.electron
export interface IElectronAPI {
  processDocument: (command: IPCCommand) => Promise<ProcessDocumentResponse | ExportRedactedResponse>
  validateLicense: (userId: string, jwt: string) => Promise<{ valid: boolean; tier: string }>
  getAppVersion: () => Promise<string>
  restartPython: () => Promise<void>
  onPythonMessage: (callback: (message: any) => void) => void
  onPythonStatus: (callback: (status: any) => void) => void
  removePythonMessageListener: () => void
  removePythonStatusListener: () => void
  ipcRenderer: {
    invoke: (channel: string, ...args: any[]) => Promise<any>
  }
}

declare global {
  interface Window {
    electron: IElectronAPI
  }
}
