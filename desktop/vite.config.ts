import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: 'src/renderer',
  base: './',
  publicDir: '../../public', // Point to public directory at root
  build: {
    outDir: '../../dist/renderer',
    emptyOutDir: true,
    copyPublicDir: true // Ensure public files are copied
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src/renderer')
    }
  },
  server: {
    port: 5173,
    strictPort: true,  // Fail if port 5173 is taken (forces cleanup)
    host: 'localhost'
  }
})
