const {
  app,
  BrowserWindow,
  ipcMain,
  dialog,
  shell,
  Tray,
  Menu,
  globalShortcut,
  clipboard,
  nativeImage,
  desktopCapturer,
  session
} = require('electron')
const path = require('path')
const os = require('os')
const { spawn } = require('child_process')
const fs = require('fs')

const isDev = !app.isPackaged
let backend = null
let mainWindow = null
let tray = null
let pendingOpen = null

// 单实例：第二次点击文件时把路径转交给已有窗口
const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
}

function readSettings() {
  try {
    const dir =
      process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config')
    const file = path.join(dir, 'libu', 'settings.json')
    return JSON.parse(fs.readFileSync(file, 'utf8'))
  } catch (_) {
    return {}
  }
}

function toElectronAccelerator(hotkey) {
  const raw = (hotkey || 'Ctrl+Alt+O').trim()
  return raw
    .replace(/\bCtrl\b/gi, 'Control')
    .replace(/\bCmd\b/gi, 'Command')
    .replace(/\+/g, '+')
}

function registerHotkey() {
  const settings = readSettings()
  const hotkey = toElectronAccelerator(settings.screenshot_hotkey || 'Ctrl+Alt+O')
  try {
    globalShortcut.unregisterAll()
  } catch (_) {}
  const ok = globalShortcut.register(hotkey, () => sendNavigate('screenshot-capture'))
  if (!ok) {
    console.warn(`[libu] 全局快捷键注册失败：${hotkey}`)
  } else {
    console.log(`[libu] 已注册截屏快捷键：${hotkey}`)
  }
}

function setupScreenCapture() {
  // Electron 17+ 必须显式允许 getDisplayMedia，否则应用内框选会直接失败
  try {
    session.defaultSession.setDisplayMediaRequestHandler(
      (request, callback) => {
        desktopCapturer
          .getSources({ types: ['screen'] })
          .then((sources) => {
            if (sources && sources.length) callback({ video: sources[0] })
            else callback({})
          })
          .catch(() => callback({}))
      },
      { useSystemPicker: false }
    )
  } catch (e) {
    console.error('设置屏幕捕获处理器失败', e)
  }
}

function resolveBackend() {
  // 打包后 src 位于 resources/src；开发时位于 仓库根/src
  const candidates = [
    path.join(process.resourcesPath || '', 'src'),
    path.join(__dirname, '..', '..', '..', 'src'),
    path.join(__dirname, '..', '..', '..', '..', 'src')
  ]
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, 'libu', 'api.py'))) return c
  }
  return candidates[1]
}

function startBackend() {
  const srcDir = resolveBackend()
  const env = {
    ...process.env,
    PYTHONPATH: srcDir + (process.env.PYTHONPATH ? ':' + process.env.PYTHONPATH : ''),
    LIBU_OUTPUT_DIR: process.env.LIBU_OUTPUT_DIR || ''
  }
  const webDir = path.join(process.resourcesPath || '', 'web')
  if (fs.existsSync(path.join(webDir, 'index.html'))) env.LIBU_WEB_DIR = webDir
  // 优先使用打包好的后端可执行文件（Windows/macOS 安装包）
  const exeName = process.platform === 'win32' ? 'libu-backend.exe' : 'libu-backend'
  const bundled = path.join(process.resourcesPath || '', 'backend', exeName)
  let cmd, args
  if (fs.existsSync(bundled)) {
    cmd = bundled
    args = ['serve', '--host', '127.0.0.1', '--port', '8000']
  } else if (process.env.LIBU_BUNDLED_PYTHON && fs.existsSync(process.env.LIBU_BUNDLED_PYTHON)) {
    cmd = process.env.LIBU_BUNDLED_PYTHON
    args = ['-m', 'libu', 'serve', '--host', '127.0.0.1', '--port', '8000']
  } else {
    cmd = process.env.LIBU_PYTHON || (process.platform === 'win32' ? 'python' : 'python3')
    args = ['-m', 'libu', 'serve', '--host', '127.0.0.1', '--port', '8000']
  }
  try {
    backend = spawn(cmd, args, {
      env,
      cwd: srcDir,
      stdio: ['ignore', 'pipe', 'pipe']
    })
    backend.stdout.on('data', (d) => process.stdout.write(`[libu] ${d}`))
    backend.stderr.on('data', (d) => process.stderr.write(`[libu] ${d}`))
    backend.on('exit', (code) => console.log(`[libu] backend exited ${code}`))
  } catch (err) {
    console.error('无法启动后端，请手动运行: PYTHONPATH=src python3 -m libu serve', err)
  }
}

function sendNavigate(target) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show()
    mainWindow.focus()
    mainWindow.webContents.send('navigate', target)
  }
}

function openPaths(paths) {
  if (!paths || !paths.length) return
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show()
    mainWindow.webContents.send('open-paths', paths)
  } else {
    pendingOpen = paths
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 940,
    minHeight: 640,
    backgroundColor: '#0b1020',
    title: '吏部 · Libu',
    icon: path.join(__dirname, '..', 'build', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }
  mainWindow.webContents.on('did-finish-load', () => {
    if (pendingOpen) {
      mainWindow.webContents.send('open-paths', pendingOpen)
      pendingOpen = null
    }
  })
  return mainWindow
}

function trayIcon() {
  const candidates = [
    path.join(process.resourcesPath || '', 'data', 'icons', 'libu.png'),
    path.join(__dirname, '..', 'build', 'icon.png')
  ]
  for (const c of candidates) {
    if (fs.existsSync(c)) return nativeImage.createFromPath(c)
  }
  return nativeImage.createEmpty()
}

function createTray() {
  try {
    tray = new Tray(trayIcon())
    tray.setToolTip('吏部 · Libu')
    const menu = Menu.buildFromTemplate([
      { label: '打开吏部', click: () => sendNavigate('main') },
      { label: '截屏 OCR', click: () => sendNavigate('screenshot-capture') },
      { type: 'separator' },
      { label: '退出', click: () => app.quit() }
    ])
    tray.setContextMenu(menu)
    tray.on('click', () => {
      if (mainWindow.isVisible()) mainWindow.hide()
      else {
        mainWindow.show()
        mainWindow.focus()
      }
    })
  } catch (e) {
    console.error('创建托盘失败', e)
  }
}

app.on('second-instance', (_e, argv) => {
  const files = argv.filter((a) => /\.(jpe?g|png|bmp|tiff?|webp|gif|avif|heic|jp2)$/i.test(a))
  if (files.length) openPaths(files)
  else sendNavigate('main')
})

app.whenReady().then(() => {
  setupScreenCapture()
  startBackend()
  createWindow()
  createTray()
  registerHotkey()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
  const files = process.argv.filter((a) =>
    /\.(jpe?g|png|bmp|tiff?|webp|gif|avif|heic|jp2)$/i.test(a)
  )
  if (files.length) openPaths(files)
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

app.on('window-all-closed', () => {
  if (backend) backend.kill()
  if (process.platform !== 'darwin') app.quit()
})

ipcMain.handle('pick-image', async () => {
  const res = await dialog.showOpenDialog({
    title: '选择图片',
    properties: ['openFile', 'multiSelections'],
    filters: [
      {
        name: '图片',
        extensions: [
          'jpg', 'jpeg', 'jpe', 'jfif', 'png', 'bmp', 'tif', 'tiff',
          'webp', 'gif', 'ico', 'tga', 'avif', 'heic', 'heif', 'jp2', 'pnm'
        ]
      },
      { name: '所有文件', extensions: ['*'] }
    ]
  })
  return res.canceled ? [] : res.filePaths
})

ipcMain.handle('set-hotkey', async (_e, hotkey) => {
  const accel = toElectronAccelerator(hotkey || 'Ctrl+Alt+O')
  try {
    globalShortcut.unregisterAll()
    const ok = globalShortcut.register(accel, () => sendNavigate('screenshot-capture'))
    return { ok, hotkey: accel }
  } catch (err) {
    return { ok: false, error: String(err) }
  }
})

ipcMain.handle('open-path', async (_e, target) => shell.openPath(target))

ipcMain.handle('show-item-in-folder', async (_e, target) => {
  shell.showItemInFolder(target)
  return ''
})

ipcMain.handle('copy-text', async (_e, text) => {
  clipboard.writeText(text || '')
  return true
})
