/**
 * API Adapter - Abstracts communication layer
 *
 * In Electron: Uses IPC (window.api)
 * In Web: Uses HTTP fetch
 */

// Detect if running in Electron or Web
const isElectron = !!(window as any).api;
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Analyze document
 */
export async function analyzeDocument(params: {
  filePath: string;
  depth: string;
  language: string;
  enableGliner: boolean;
  focusAreas?: string[];
  customKeywords?: string[];
}): Promise<any> {
  if (isElectron) {
    // Electron mode: Use IPC
    return (window as any).api.analyzeDocument(params);
  } else {
    // Web mode: Use HTTP API
    const formData = new FormData();
    formData.append('depth', params.depth);
    formData.append('language', params.language);
    formData.append('enableGliner', String(params.enableGliner));

    if (params.focusAreas) {
      formData.append('focusAreas', JSON.stringify(params.focusAreas));
    }

    if (params.customKeywords) {
      formData.append('customKeywords', JSON.stringify(params.customKeywords));
    }

    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

/**
 * Export redacted PDF
 */
export async function exportRedactedPDF(params: {
  inputPath: string;
  entities: any[];
  placeholder: string;
}): Promise<any> {
  if (isElectron) {
    // Electron mode: Use IPC
    return (window as any).api.exportRedactedPDF(params);
  } else {
    // Web mode: Use HTTP API
    const response = await fetch(`${API_BASE_URL}/export-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.blob();
  }
}

/**
 * Get learned entities
 */
export async function getLearnedEntities(): Promise<any> {
  if (isElectron) {
    // Electron mode: Use IPC
    return (window as any).api.getLearnedEntities();
  } else {
    // Web mode: Use HTTP API
    const response = await fetch(`${API_BASE_URL}/learned-entities`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

/**
 * Learn new entities
 */
export async function learnEntities(entities: any[]): Promise<any> {
  if (isElectron) {
    // Electron mode: Use IPC
    return (window as any).api.learnEntities(entities);
  } else {
    // Web mode: Use HTTP API
    const response = await fetch(`${API_BASE_URL}/learn-entities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entities }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

/**
 * Upload file (Web only - returns file path for subsequent calls)
 */
export async function uploadFile(file: File): Promise<{ filePath: string }> {
  if (isElectron) {
    // In Electron, file path is already available locally
    // This is called when user selects file via dialog
    return { filePath: (file as any).path || file.name };
  } else {
    // Web mode: Upload file to server, get temp path back
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }
}

/**
 * Check if running in Electron
 */
export function isElectronMode(): boolean {
  return isElectron;
}

/**
 * Get API base URL
 */
export function getApiBaseUrl(): string {
  return isElectron ? 'electron-ipc' : API_BASE_URL;
}
