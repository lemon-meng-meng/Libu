import React, { useCallback, useEffect, useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import MainView from './components/MainView.jsx'
import SettingsView from './components/SettingsView.jsx'
import ImageViewer from './components/ImageViewer.jsx'
import ScreenshotOCR from './components/ScreenshotOCR.jsx'
import ProcessWizard from './components/ProcessWizard.jsx'
import Toast from './components/Toast.jsx'
import { api } from './api.js'
import { useTheme } from './theme.jsx'
import './App.css'

export default function App() {
  const { setTheme, setBackground } = useTheme()
  const [view, setView] = useState('main')
  const [settings, setSettings] = useState(null)
  const [engines, setEngines] = useState([])
  const [projects, setProjects] = useState([])
  const [wizardSources, setWizardSources] = useState(null)
  const [incomingViewerPath, setIncomingViewerPath] = useState(null)
  const [captureSignal, setCaptureSignal] = useState(0)
  const [toast, setToast] = useState(null)
  const [backendOnline, setBackendOnline] = useState(true)

  const notify = useCallback((message, type = 'info') => {
    setToast({ message, type, id: Date.now() })
  }, [])

  const refreshProjects = useCallback(async () => {
    try {
      const data = await api.projects()
      setProjects(data.projects || [])
      setBackendOnline(true)
    } catch (e) {
      setBackendOnline(false)
    }
  }, [])

  useEffect(() => {
    ;(async () => {
      try {
        const [s, e] = await Promise.all([api.getSettings(), api.engines()])
        setSettings(s)
        setEngines(e.engines || [])
        setTheme(s.theme || 'system')
        setBackground(s.background || 'aurora-blue')
        await refreshProjects()
      } catch (err) {
        setBackendOnline(false)
        notify('无法连接后端服务，请确认后端已启动', 'error')
      }
    })()
  }, [refreshProjects, setTheme, setBackground, notify])

  const onSaveSettings = useCallback(
    async (patch) => {
      const next = {
        ...(settings || {}),
        ...patch,
        providers: patch.providers
          ? { ...(settings?.providers || {}), ...patch.providers }
          : settings?.providers || {},
        feature_backends: patch.feature_backends
          ? { ...(settings?.feature_backends || {}), ...patch.feature_backends }
          : settings?.feature_backends || {}
      }
      setSettings(next)
      if (patch.theme) setTheme(patch.theme)
      if (patch.background) setBackground(patch.background)
      try {
        const saved = await api.saveSettings(patch)
        setSettings(saved)
        setTheme(saved.theme || 'system')
        setBackground(saved.background || 'aurora-blue')
        notify('设置已保存', 'success')
        return saved
      } catch (e) {
        notify('保存设置失败：' + e.message, 'error')
      }
    },
    [settings, setTheme, setBackground, notify]
  )

  const addFiles = useCallback(
    async (files) => {
      if (!files || files.length === 0) return
      const sources = []
      for (const file of files) {
        try {
          if (typeof file === 'string') {
            const res = await api.importPath(file)
            sources.push(res.path)
          } else {
            const up = await api.upload(file)
            sources.push(up.path)
          }
        } catch (e) {
          notify('导入失败：' + e.message, 'error')
        }
      }
      if (sources.length) setWizardSources(sources)
    },
    [notify]
  )

  // 从文件管理器右键「用吏部打开」或在命令行传入图片：
  // 直接在「图片查看器」中打开（符合系统级图片查看器的使用习惯）。
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const imp = params.get('import')
    if (imp) {
      setIncomingViewerPath(imp)
      setView('viewer')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  // Electron 托盘 / 双击文件：接收主进程的导航与打开文件事件
  useEffect(() => {
    window.libu?.onNavigate?.((target) => {
      if (target === 'screenshot-capture') {
        setView('screenshot')
        setCaptureSignal((s) => s + 1)
      } else if (target) {
        setView(target)
      }
    })
    window.libu?.onOpenPaths?.((paths) => {
      if (paths?.length) {
        setIncomingViewerPath(paths[0])
        setView('viewer')
      }
    })
  }, [])

  return (
    <div className="app-shell">
      <Sidebar view={view} setView={setView} />
      <main className="app-main">
        {view === 'main' && (
          <MainView
            projects={projects}
            settings={settings}
            engines={engines}
            backendOnline={backendOnline}
            onRefresh={refreshProjects}
            onAdd={addFiles}
            onNotify={notify}
            onSaveSettings={onSaveSettings}
          />
        )}
        {view === 'viewer' && (
          <ImageViewer
            settings={settings}
            engines={engines}
            onSaveSettings={onSaveSettings}
            onNotify={notify}
            incomingPath={incomingViewerPath}
            onIncomingHandled={() => setIncomingViewerPath(null)}
          />
        )}
        {view === 'screenshot' && (
          <ScreenshotOCR
            settings={settings}
            engines={engines}
            onSaveSettings={onSaveSettings}
            onNotify={notify}
            captureSignal={captureSignal}
          />
        )}
        {view === 'settings' && (
          <SettingsView
            settings={settings}
            engines={engines}
            onSave={onSaveSettings}
            onNotify={notify}
            onRefreshProjects={refreshProjects}
          />
        )}
      </main>

      {wizardSources && wizardSources.length > 0 && (
        <ProcessWizard
          sources={wizardSources}
          settings={settings}
          engines={engines}
          onClose={() => setWizardSources(null)}
          onDone={() => {
            refreshProjects()
          }}
          onNotify={notify}
        />
      )}

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  )
}
