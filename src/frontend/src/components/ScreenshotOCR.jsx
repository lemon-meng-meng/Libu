import React, { useCallback, useEffect, useRef, useState } from 'react'
import ModelPicker from './ModelPicker.jsx'
import { api } from '../api.js'
import './ScreenshotOCR.css'

export default function ScreenshotOCR({
  settings,
  engines,
  onSaveSettings,
  onNotify,
  captureSignal = 0
}) {
  const [state, setState] = useState({ text: '', history: [] })
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [capturing, setCapturing] = useState(false)
  const [captureImage, setCaptureImage] = useState(null)
  const [copied, setCopied] = useState(false)
  const textRef = useRef(null)
  const lastUpdated = useRef(0)

  const backend = settings?.feature_backends?.screenshot || ''
  const defaultBackend = settings?.default_backend || ''
  const hotkey = settings?.screenshot_hotkey || 'Ctrl+Alt+O'

  const applyState = useCallback(
    (s) => {
      setState(s)
      if (s.updated_at !== lastUpdated.current) {
        lastUpdated.current = s.updated_at
        if (document.activeElement !== textRef.current) setText(s.text || '')
      }
    },
    []
  )

  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const s = await api.screenshotState()
        if (alive) applyState(s)
      } catch (_) {
        /* 忽略一次失败 */
      }
    }
    tick()
    const timer = setInterval(tick, 1500)
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [applyState])

  const triggerCapture = async () => {
    try {
      await api.screenshotCapture()
      setBusy(true)
      onNotify?.('已请求区域截屏，请在屏幕上框选（需托盘助手运行）', 'info')
      // 轮询是否有新结果
      let tries = 0
      const poll = setInterval(async () => {
        tries += 1
        try {
          const s = await api.screenshotState()
          if (s.updated_at > lastUpdated.current) {
            applyState(s)
            setBusy(false)
            clearInterval(poll)
          }
        } catch (_) {}
        if (tries > 40) {
          clearInterval(poll)
          setBusy(false)
        }
      }, 1000)
    } catch (e) {
      onNotify?.('请求截屏失败：' + e.message, 'error')
    }
  }

  // 浏览器/Electron 内建的屏幕捕获 + 框选，作为托盘助手的备选方案
  const captureInApp = async () => {
    try {
      if (!navigator.mediaDevices?.getDisplayMedia) throw new Error('当前环境不支持屏幕捕获')
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { cursor: 'never' },
        audio: false
      })
      const video = document.createElement('video')
      video.srcObject = stream
      await video.play()
      await new Promise((r) => setTimeout(r, 200))
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      canvas.getContext('2d').drawImage(video, 0, 0)
      stream.getTracks().forEach((t) => t.stop())
      setCaptureImage(canvas.toDataURL('image/png'))
    } catch (e) {
      onNotify?.('屏幕捕获失败：' + e.message, 'error')
    }
  }

  // 托盘 / 全局快捷键触发：自动进入应用内框选
  useEffect(() => {
    if (captureSignal > 0) captureInApp()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [captureSignal])

  const uploadImage = async (blob) => {
    setBusy(true)
    try {
      const s = await api.screenshotUpload(blob, backend)
      applyState(s)
      setText(s.text || '')
      onNotify?.('识别完成', 'success')
    } catch (e) {
      onNotify?.('识别失败：' + e.message, 'error')
    } finally {
      setBusy(false)
      setCaptureImage(null)
    }
  }

  const pasteImage = async () => {
    try {
      if (!navigator.clipboard?.read) throw new Error('剪贴板不可用')
      const items = await navigator.clipboard.read()
      for (const item of items) {
        const type = item.types.find((t) => t.startsWith('image/'))
        if (type) {
          const blob = await item.getType(type)
          await uploadImage(blob)
          return
        }
      }
      onNotify?.('剪贴板中没有图片', 'info')
    } catch (e) {
      onNotify?.('读取剪贴板失败：' + e.message, 'error')
    }
  }

  const copyText = async () => {
    try {
      await navigator.clipboard.writeText(text)
      if (window.libu?.copyText) await window.libu.copyText(text)
      await api.screenshotUpdate(text)
      setCopied(true)
      onNotify?.('已复制文字', 'success')
      setTimeout(() => setCopied(false), 1500)
    } catch (e) {
      onNotify?.('复制失败：' + e.message, 'error')
    }
  }

  const saveText = async () => {
    try {
      const s = await api.screenshotUpdate(text)
      applyState(s)
      onNotify?.('已保存修改', 'success')
    } catch (e) {
      onNotify?.('保存失败：' + e.message, 'error')
    }
  }

  const clearAll = async () => {
    try {
      const s = await api.screenshotClear()
      applyState(s)
      setText('')
    } catch (e) {
      onNotify?.('清空失败：' + e.message, 'error')
    }
  }

  return (
    <div className="shot-view">
      <header className="shot-view__header">
        <div>
          <h1 className="shot-view__title">截屏 OCR</h1>
          <p className="main-view__subtitle">
            托盘图标点击「截屏 OCR」或按 {hotkey} 在屏幕框选，识别结果直接进入下方剪贴板
          </p>
        </div>
        <div className="shot-view__controls">
          <ModelPicker
            engines={engines}
            value={backend}
            defaultBackend={defaultBackend}
            onChange={(v) => onSaveSettings?.({ feature_backends: { screenshot: v } })}
            label="截屏 OCR 使用的模型"
          />
          <button className="btn-primary" onClick={triggerCapture}>
            截屏
          </button>
          <button className="btn-ghost" onClick={captureInApp}>
            应用内框选
          </button>
          <button className="btn-ghost" onClick={pasteImage}>
            粘贴图片
          </button>
        </div>
      </header>

      <div className="shot-view__body">
        <section className="shot-panel liquid-glass">
          <div className="shot-panel__head">
            <h2>识别结果（可自由修改）</h2>
            <div className="shot-panel__actions">
              <button className="btn-ghost small" onClick={saveText}>
                保存修改
              </button>
              <button className="btn-primary small" onClick={copyText} disabled={!text}>
                {copied ? '已复制' : '复制文字'}
              </button>
              <button className="btn-danger-ghost small" onClick={clearAll}>
                清空
              </button>
            </div>
          </div>
          <textarea
            ref={textRef}
            className="shot-clipboard"
            value={text}
            placeholder="截屏/粘贴图片后，识别出的文字会出现在这里；你也可以直接编辑。"
            onChange={(e) => setText(e.target.value)}
          />
        </section>

        <aside className="shot-history liquid-glass">
          <div className="shot-panel__head">
            <h2>历史记录</h2>
            <span className="count">{(state.history || []).length}</span>
          </div>
          <div className="shot-history__list">
            {(state.history || []).length === 0 && (
              <p className="hint">暂无记录。</p>
            )}
            {(state.history || []).map((h) => (
              <button
                key={h.id}
                className="shot-history__item"
                onClick={() => {
                  setText(h.text || '')
                  onNotify?.('已载入历史记录', 'info')
                }}
                title={h.text}
              >
                <span className="shot-history__time">
                  {new Date(h.created_at * 1000).toLocaleTimeString()}
                </span>
                <span className="shot-history__text">{h.text || '（空）'}</span>
              </button>
            ))}
          </div>
        </aside>
      </div>

      {busy && (
        <div className="shot-busy">
          <div className="spinner" />
          <span>正在识别…</span>
        </div>
      )}

      {captureImage && (
        <RegionCropper
          imageSrc={captureImage}
          onCancel={() => setCaptureImage(null)}
          onCrop={(blob) => uploadImage(blob)}
        />
      )}
    </div>
  )
}

/* 应用内屏幕截图框选 */
function RegionCropper({ imageSrc, onCancel, onCrop }) {
  const [imgSize, setImgSize] = useState(null)
  const [box, setBox] = useState(null)
  const [start, setStart] = useState(null)
  const imgRef = useRef(null)

  const onLoad = () => {
    const img = imgRef.current
    if (img) setImgSize({ w: img.clientWidth, h: img.clientHeight, nw: img.naturalWidth, nh: img.naturalHeight })
  }

  const toImageCoords = (e) => {
    const rect = imgRef.current.getBoundingClientRect()
    return [e.clientX - rect.left, e.clientY - rect.top]
  }

  const onDown = (e) => {
    const p = toImageCoords(e)
    setStart(p)
    setBox([p[0], p[1], p[0], p[1]])
  }
  const onMove = (e) => {
    if (!start) return
    const p = toImageCoords(e)
    setBox([Math.min(start[0], p[0]), Math.min(start[1], p[1]), Math.max(start[0], p[0]), Math.max(start[1], p[1])])
  }
  const onUp = () => {
    if (!box || !imgSize) return
    const scale = imgSize.nw / imgSize.w
    const [x0, y0, x1, y1] = box.map((v) => Math.round(v * scale))
    if (x1 - x0 < 3 || y1 - y0 < 3) return
    const canvas = document.createElement('canvas')
    canvas.width = x1 - x0
    canvas.height = y1 - y0
    const img = new Image()
    img.onload = () => {
      canvas.getContext('2d').drawImage(img, x0, y0, x1 - x0, y1 - y0, 0, 0, x1 - x0, y1 - y0)
      canvas.toBlob((blob) => onCrop(blob), 'image/png')
    }
    img.src = imageSrc
  }

  return (
    <div className="region-cropper" onMouseUp={onUp} onMouseMove={onMove}>
      <div className="region-cropper__bar">
        <span>拖动鼠标框选要识别文字的区域</span>
        <button
          className="btn-primary small"
          onClick={() => {
            const img = imgRef.current
            if (!img) return
            const canvas = document.createElement('canvas')
            canvas.width = img.naturalWidth
            canvas.height = img.naturalHeight
            const im = new Image()
            im.onload = () => {
              canvas.getContext('2d').drawImage(im, 0, 0)
              canvas.toBlob((b) => onCrop(b), 'image/png')
            }
            im.src = imageSrc
          }}
        >
          全屏识别
        </button>
        <button className="btn-ghost small" onClick={onCancel}>
          取消
        </button>
      </div>
      <div className="region-cropper__stage">
        <div className="region-cropper__wrap" style={{ position: 'relative', display: 'inline-block' }}>
          <img
            ref={imgRef}
            src={imageSrc}
            onLoad={onLoad}
            onMouseDown={onDown}
            draggable={false}
            alt="截屏"
          />
          {box && (
            <div
              className="region-cropper__rect"
              style={{ left: box[0], top: box[1], width: box[2] - box[0], height: box[3] - box[1] }}
            />
          )}
        </div>
      </div>
    </div>
  )
}
