// 浏览器 / AppImage 模式下前端由同一后端进程提供，使用同源地址；
// Electron（file://）或显式配置时回退到本地 8000 端口。
const _isHttp =
  typeof window !== 'undefined' && window.location.protocol.startsWith('http')
const API_BASE = import.meta.env.VITE_API_BASE || (_isHttp ? window.location.origin : 'http://127.0.0.1:8000')

async function req(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || data.error || detail
    } catch (_) {}
    throw new Error(detail)
  }
  return res.json()
}

async function upload(path, file, fields = {}) {
  const fd = new FormData()
  fd.append('file', file)
  for (const [k, v] of Object.entries(fields)) fd.append(k, v)
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', body: fd })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || data.error || detail
    } catch (_) {}
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  base: API_BASE,
  health: () => req('/health'),
  meta: () => req('/meta'),
  engines: () => req('/engines'),
  getSettings: () => req('/settings'),
  saveSettings: (patch) => req('/settings', { method: 'PUT', body: JSON.stringify(patch) }),
  projects: () => req('/projects'),
  deleteProject: (source) =>
    req('/projects/delete', { method: 'POST', body: JSON.stringify({ source }) }),
  hideProject: (source) =>
    req('/projects/hide', { method: 'POST', body: JSON.stringify({ source }) }),

  async upload(file) {
    return upload('/upload', file)
  },
  importPath: (path) =>
    req('/import-path', { method: 'POST', body: JSON.stringify({ path }) }),
  preprocess: (payload) =>
    req('/preprocess', { method: 'POST', body: JSON.stringify(payload) }),
  ocr: (payload) => req('/ocr', { method: 'POST', body: JSON.stringify(payload) }),
  generate: (payload) => req('/generate', { method: 'POST', body: JSON.stringify(payload) }),

  models: () => req('/models'),
  importModel: (file, name = '') => upload('/models/import', file, { name }),
  deleteModel: (name) => req(`/models/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  // ---- 提供商连通性 / 模型自动检测 ----
  providerModels: (provider, config) =>
    req('/providers/models', { method: 'POST', body: JSON.stringify({ provider, config }) }),
  providerTest: (provider, config) =>
    req('/providers/test', { method: 'POST', body: JSON.stringify({ provider, config }) }),

  // ---- OCR 图片查看器 ----
  viewerImages: () => req('/viewer/images'),
  viewerAdd: (path) => req('/viewer/add', { method: 'POST', body: JSON.stringify({ path }) }),
  viewerRemove: (source) =>
    req('/viewer/remove', { method: 'POST', body: JSON.stringify({ source }) }),
  viewerPaste: (file) => upload('/viewer/paste', file),
  viewerOcr: (source, backend) =>
    req('/viewer/ocr', {
      method: 'POST',
      body: JSON.stringify({ source, backend: backend || undefined })
    }),

  // ---- 截屏 OCR ----
  screenshotState: () => req('/screenshot/state'),
  screenshotUpdate: (text) =>
    req('/screenshot/state', { method: 'PUT', body: JSON.stringify({ text }) }),
  screenshotUpload: (file, backend = '') =>
    upload('/screenshot/upload', file, { backend }),
  screenshotIngest: (path, backend) =>
    req('/screenshot/ingest', {
      method: 'POST',
      body: JSON.stringify({ path, backend: backend || undefined })
    }),
  screenshotCapture: () => req('/screenshot/capture', { method: 'POST' }),
  screenshotClear: () => req('/screenshot/clear', { method: 'POST' }),

  openOutputDir: () => req('/open-output-dir', { method: 'POST' }),
  previewUrl: (path) => `${API_BASE}/preview?path=${encodeURIComponent(path)}`,
  thumbnailUrl: (path) => `${API_BASE}/thumbnail?source=${encodeURIComponent(path)}`,
  downloadUrl: (path) => `${API_BASE}/download?path=${encodeURIComponent(path)}`
}

export async function pickImageFiles() {
  if (window.libu?.pickImage) {
    const paths = await window.libu.pickImage()
    return paths || []
  }
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.multiple = true
    input.onchange = () => resolve(Array.from(input.files || []))
    input.click()
  })
}
