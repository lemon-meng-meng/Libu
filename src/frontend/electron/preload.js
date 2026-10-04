const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('libu', {
  isElectron: true,
  pickImage: () => ipcRenderer.invoke('pick-image'),
  openPath: (p) => ipcRenderer.invoke('open-path', p),
  showItem: (p) => ipcRenderer.invoke('show-item-in-folder', p),
  copyText: (t) => ipcRenderer.invoke('copy-text', t),
  setHotkey: (h) => ipcRenderer.invoke('set-hotkey', h),
  onNavigate: (cb) => ipcRenderer.on('navigate', (_e, target) => cb(target)),
  onOpenPaths: (cb) => ipcRenderer.on('open-paths', (_e, paths) => cb(paths))
})
