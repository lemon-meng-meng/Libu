import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_TARGET = process.env.LIBU_API_TARGET || 'http://127.0.0.1:8000'
const API_PREFIXES = [
  '/health', '/meta', '/engines', '/settings', '/projects', '/upload',
  '/import-path', '/preprocess', '/ocr', '/generate', '/models', '/viewer',
  '/screenshot', '/thumbnail', '/preview', '/download', '/open-output-dir'
]
const proxy = Object.fromEntries(
  API_PREFIXES.map((p) => [p, { target: API_TARGET, changeOrigin: true }])
)

export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    port: 5173,
    strictPort: true,
    host: '127.0.0.1',
    proxy
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
