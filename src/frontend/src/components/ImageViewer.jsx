import React, { useCallback, useEffect, useRef, useState } from 'react'
import LiquidGlass from './LiquidGlass.jsx'
import ContextMenu from './ContextMenu.jsx'
import ModelPicker from './ModelPicker.jsx'
import { api, pickImageFiles } from '../api.js'
import './ImageViewer.css'

const ACCEPTED =
  '.jpg,.jpeg,.jpe,.jfif,.png,.bmp,.dib,.tif,.tiff,.webp,.gif,.ico,.tga,.avif,.heic,.heif,.jp2,.j2k,.pbm,.pgm,.ppm,.pnm,.pcx,.dcx,.sgi,.ras,.xbm'

export default function ImageViewer({
  settings,
  engines,
  onSaveSettings,
  onNotify,
  incomingPath,
  onIncomingHandled
}) {
  const [images, setImages] = useState([])
  const [menu, setMenu] = useState(null)
  const [active, setActive] = useState(null)
  const [clipboardFile, setClipboardFile] = useState(null)

  const backend = settings?.feature_backends?.viewer || ''
  const defaultBackend = settings?.default_backend || ''

  const load = useCallback(async () => {
    try {
      const data = await api.viewerImages()
      setImages(data.images || [])
    } catch (e) {
      onNotify?.('读取图片列表失败：' + e.message, 'error')
    }
  }, [onNotify])

  useEffect(() => {
    load()
  }, [load])

  // 从文件管理器「用吏部打开」或其它来源传入的路径
  useEffect(() => {
    if (!incomingPath) return
    ;(async () => {
      try {
        const res = await api.viewerAdd(incomingPath)
        await load()
        if (res?.image) setActive(res.image)
      } catch (e) {
        onNotify?.('打开失败：' + e.message, 'error')
      } finally {
        onIncomingHandled?.()
      }
    })()
  }, [incomingPath, load, onNotify, onIncomingHandled])

  const addFiles = async () => {
    const files = await pickImageFiles()
    for (const f of files) {
      try {
        if (typeof f === 'string') await api.viewerAdd(f)
        else await api.viewerPaste(f)
      } catch (e) {
        onNotify?.('导入失败：' + e.message, 'error')
      }
    }
    load()
  }

  const pasteFile = useCallback(
    async (file) => {
      try {
        const res = await api.viewerPaste(file)
        await load()
        onNotify?.('已粘贴图片', 'success')
        if (res?.image) setActive(res.image)
      } catch (e) {
        onNotify?.('粘贴失败：' + e.message, 'error')
      }
    },
    [load, onNotify]
  )

  // Ctrl+V 直接粘贴图片
  useEffect(() => {
    const onPaste = (e) => {
      const items = e.clipboardData?.items || []
      for (const it of items) {
        if (it.type && it.type.startsWith('image/')) {
          const file = it.getAsFile()
          if (file) {
            e.preventDefault()
            pasteFile(file)
            return
          }
        }
      }
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [pasteFile])

  // 检测剪贴板中是否已有图片
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (!navigator.clipboard?.read) return
        const items = await navigator.clipboard.read()
        for (const item of items) {
          const type = item.types.find((t) => t.startsWith('image/'))
          if (type) {
            const blob = await item.getType(type)
            const file = new File([blob], 'clipboard.png', { type })
            if (!cancelled) setClipboardFile(file)
            return
          }
        }
      } catch (_) {
        /* 权限被拒时忽略 */
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const removeFromList = async (img) => {
    try {
      await api.viewerRemove(img.source)
      onNotify?.('已从查看器移除', 'success')
      if (active?.source === img.source) setActive(null)
      load()
    } catch (e) {
      onNotify?.('操作失败：' + e.message, 'error')
    }
  }

  const reveal = async (img) => {
    if (window.libu?.showItem) await window.libu.showItem(img.source)
  }

  return (
    <div className="viewer-view">
      <header className="viewer-view__header">
        <div>
          <h1 className="viewer-view__title">图片查看器</h1>
          <p className="main-view__subtitle">
            像微信一样直接框选复制图中文字 · 记忆打开过的图片（文件未移动/删除即保留）
          </p>
        </div>
        <div className="viewer-view__controls">
          <ModelPicker
            engines={engines}
            value={backend}
            defaultBackend={defaultBackend}
            onChange={(v) => onSaveSettings?.({ feature_backends: { viewer: v } })}
            label="图片查看器使用的 OCR 模型"
          />
          <button className="btn-ghost" onClick={addFiles}>
            导入图片
          </button>
        </div>
      </header>

      {clipboardFile && (
        <div className="viewer-clipboard-bar">
          <span>检测到剪贴板中有图片，是否粘贴查看？</span>
          <button
            className="btn-primary small"
            onClick={() => {
              pasteFile(clipboardFile)
              setClipboardFile(null)
            }}
          >
            粘贴
          </button>
          <button className="btn-ghost small" onClick={() => setClipboardFile(null)}>
            忽略
          </button>
        </div>
      )}

      <div className="viewer-grid">
        <LiquidGlass className="viewer-add" interactive radius={20} onClick={addFiles}>
          <div className="viewer-add__inner">
            <span className="viewer-add__plus">+</span>
            <span className="viewer-add__text">添加图片</span>
          </div>
        </LiquidGlass>

        {images.map((img) => (
          <LiquidGlass
            key={img.id}
            className="viewer-card"
            interactive
            radius={20}
            onClick={() => setActive(img)}
            onContextMenu={(e) => {
              e.preventDefault()
              e.stopPropagation()
              setMenu({ x: e.clientX, y: e.clientY, img })
            }}
          >
            <div className="viewer-card__thumb">
              <img src={api.thumbnailUrl(img.source)} alt={img.title} draggable={false} />
            </div>
            <div className="viewer-card__meta">
              <div className="viewer-card__name" title={img.title}>
                {img.title}
              </div>
            </div>
          </LiquidGlass>
        ))}
      </div>

      {images.length === 0 && (
        <div className="viewer-empty">
          <p>还没有图片，点击「+」或直接 Ctrl+V 粘贴一张图片。</p>
        </div>
      )}

      {menu && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          onClose={() => setMenu(null)}
          items={[
            { label: '在文件管理器中显示', icon: '📂', onClick: () => reveal(menu.img) },
            {
              label: '从查看器移除',
              icon: '🗑',
              danger: true,
              onClick: () => removeFromList(menu.img)
            }
          ]}
        />
      )}

      {active && (
        <ImageViewerOverlay
          image={active}
          engines={engines}
          backend={backend}
          onClose={() => setActive(null)}
          onNotify={onNotify}
        />
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* 全屏查看 + 可复制文字层                                              */
/* ------------------------------------------------------------------ */
function ImageViewerOverlay({ image, backend, onClose, onNotify }) {
  const imgRef = useRef(null)
  const [results, setResults] = useState([])
  const [busy, setBusy] = useState(false)
  const [showText, setShowText] = useState(false)
  const [scale, setScale] = useState(1)
  const [copied, setCopied] = useState(false)

  const recognize = useCallback(async () => {
    setBusy(true)
    try {
      const res = await api.viewerOcr(image.source, backend)
      setResults(res.results || [])
      if ((res.results || []).length === 0) {
        onNotify?.('未识别到文字', 'info')
      }
    } catch (e) {
      onNotify?.('识别失败：' + e.message, 'error')
    } finally {
      setBusy(false)
    }
  }, [image.source, backend, onNotify])

  useEffect(() => {
    recognize()
  }, [recognize])

  const onImgLoad = () => {
    const img = imgRef.current
    if (img && img.naturalWidth) setScale(img.clientWidth / img.naturalWidth)
  }

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    const onResize = () => onImgLoad()
    window.addEventListener('keydown', onKey)
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('resize', onResize)
    }
  })

  const copyAll = async () => {
    const text = results.map((r) => r.text).join('\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      onNotify?.('已复制全部文字', 'success')
      setTimeout(() => setCopied(false), 1500)
    } catch (_) {
      onNotify?.('复制失败', 'error')
    }
  }

  return (
    <div className="viewer-overlay" onClick={onClose}>
      <div className="viewer-overlay__toolbar" onClick={(e) => e.stopPropagation()}>
        <span className="viewer-overlay__title" title={image.title}>
          {image.title}
        </span>
        <button className="btn-ghost small" onClick={recognize} disabled={busy}>
          {busy ? '识别中…' : '重新识别'}
        </button>
        <button
          className={`btn-ghost small ${showText ? 'active' : ''}`}
          onClick={() => setShowText((v) => !v)}
          title="显示/隐藏文字层，便于框选"
        >
          {showText ? '隐藏文字层' : '显示文字层'}
        </button>
        <button className="btn-ghost small" onClick={copyAll} disabled={!results.length}>
          {copied ? '已复制' : '复制全部'}
        </button>
        <button className="icon-btn" onClick={onClose} title="关闭 (Esc)">
          ✕
        </button>
      </div>

      <div className="viewer-overlay__stage" onClick={(e) => e.stopPropagation()}>
        <div className={`viewer-image-wrap ${showText ? 'show-text' : ''}`}>
          <img ref={imgRef} src={api.previewUrl(image.source)} onLoad={onImgLoad} alt={image.title} draggable={false} />
          {results.map((r, i) =>
            r.box ? (
              <span
                key={i}
                className="text-hotspot"
                style={{
                  left: r.box[0] * scale,
                  top: r.box[1] * scale,
                  width: (r.box[2] - r.box[0]) * scale,
                  height: (r.box[3] - r.box[1]) * scale,
                  fontSize: Math.max(9, (r.box[3] - r.box[1]) * scale * 0.82)
                }}
              >
                {r.text}
              </span>
            ) : null
          )}
        </div>
        <p className="viewer-overlay__hint">
          提示：可直接在图片上按住鼠标拖动选中文字，然后 Ctrl+C 复制。
        </p>
      </div>

      {busy && (
        <div className="viewer-overlay__busy">
          <div className="spinner" />
        </div>
      )}
    </div>
  )
}
