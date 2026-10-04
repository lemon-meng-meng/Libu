import React, { useCallback, useEffect, useRef, useState } from 'react'
import './ImageCropper.css'

const HANDLE = 10
const MIN_SIZE = 24

/**
 * 图片范围框选：支持拖拽新建、移动、八方向缩放，坐标自动换算回原图像素。
 * onCrop(box) 在交互结束时回调，box = [x0, y0, x1, y1]（原图像素坐标）。
 */
export default function ImageCropper({ imageSrc, onCrop, onBoxChange }) {
  const imgRef = useRef(null)
  const stateRef = useRef({ mode: null, start: null, box: null, handle: null })
  const [box, setBox] = useState(null)
  const [natural, setNatural] = useState({ w: 0, h: 0 })

  const displayRect = () => imgRef.current?.getBoundingClientRect()

  const toOriginal = useCallback(
    (rect) => {
      const r = displayRect()
      if (!r || !rect) return null
      const sx = natural.w / r.width
      const sy = natural.h / r.height
      return [
        Math.round(rect.x * sx),
        Math.round(rect.y * sy),
        Math.round((rect.x + rect.w) * sx),
        Math.round((rect.y + rect.h) * sy)
      ]
    },
    [natural]
  )

  const emit = useCallback(
    (rect) => {
      const orig = toOriginal(rect)
      if (orig) {
        onCrop?.(orig)
        onBoxChange?.(orig)
      }
    },
    [onCrop, onBoxChange, toOriginal]
  )

  const clamp = (v, min, max) => Math.max(min, Math.min(max, v))

  const onLoad = () => {
    const img = imgRef.current
    if (!img) return
    const w = img.naturalWidth
    const h = img.naturalHeight
    setNatural({ w, h })
    const r = displayRect()
    if (!r) return
    // 默认框选 90%
    const init = { x: r.width * 0.05, y: r.height * 0.05, w: r.width * 0.9, h: r.height * 0.9 }
    setBox(init)
    stateRef.current.box = init
    // 直接用原图尺寸换算，避免使用尚未更新的 natural 状态
    const sx = w / r.width
    const sy = h / r.height
    const orig = [
      Math.round(init.x * sx),
      Math.round(init.y * sy),
      Math.round((init.x + init.w) * sx),
      Math.round((init.y + init.h) * sy)
    ]
    onCrop?.(orig)
    onBoxChange?.(orig)
  }

  const hitHandle = (x, y, b) => {
    const near = (a, c) => Math.abs(a - c) <= HANDLE
    if (near(x, b.x) && near(y, b.y)) return 'nw'
    if (near(x, b.x + b.w) && near(y, b.y)) return 'ne'
    if (near(x, b.x) && near(y, b.y + b.h)) return 'sw'
    if (near(x, b.x + b.w) && near(y, b.y + b.h)) return 'se'
    if (near(y, b.y) && x > b.x && x < b.x + b.w) return 'n'
    if (near(y, b.y + b.h) && x > b.x && x < b.x + b.w) return 's'
    if (near(x, b.x) && y > b.y && y < b.y + b.h) return 'w'
    if (near(x, b.x + b.w) && y > b.y && y < b.y + b.h) return 'e'
    return null
  }

  useEffect(() => {
    const onDown = (e) => {
      const r = displayRect()
      if (!r) return
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return
      const x = e.clientX - r.left
      const y = e.clientY - r.top
      const b = stateRef.current.box || { x: 0, y: 0, w: 0, h: 0 }
      const handle = hitHandle(x, y, b)
      if (handle) {
        stateRef.current = { mode: 'resize', start: { x, y }, box: b, handle }
      } else if (x > b.x && x < b.x + b.w && y > b.y && y < b.y + b.h) {
        stateRef.current = { mode: 'move', start: { x, y }, box: b, handle: null }
      } else {
        stateRef.current = { mode: 'create', start: { x, y }, box: { x, y, w: 0, h: 0 }, handle: null }
        setBox(stateRef.current.box)
      }
      e.preventDefault()
    }

    const onMove = (e) => {
      const st = stateRef.current
      if (!st.mode) return
      const r = displayRect()
      const x = e.clientX - r.left
      const y = e.clientY - r.top
      const { start, box: b0, handle } = st
      let b
      if (st.mode === 'create') {
        const nx = Math.min(start.x, x)
        const ny = Math.min(start.y, y)
        b = { x: nx, y: ny, w: Math.abs(x - start.x), h: Math.abs(y - start.y) }
      } else if (st.mode === 'move') {
        b = {
          x: clamp(b0.x + (x - start.x), 0, r.width - b0.w),
          y: clamp(b0.y + (y - start.y), 0, r.height - b0.h),
          w: b0.w,
          h: b0.h
        }
      } else {
        let { x: bx, y: by, w, h } = b0
        const dx = x - start.x
        const dy = y - start.y
        if (handle.includes('e')) w = clamp(w + dx, MIN_SIZE, r.width - bx)
        if (handle.includes('s')) h = clamp(h + dy, MIN_SIZE, r.height - by)
        if (handle.includes('w')) {
          const nx = clamp(bx + dx, 0, bx + w - MIN_SIZE)
          w = w + (bx - nx)
          bx = nx
        }
        if (handle.includes('n')) {
          const ny = clamp(by + dy, 0, by + h - MIN_SIZE)
          h = h + (by - ny)
          by = ny
        }
        b = { x: bx, y: by, w, h }
      }
      stateRef.current.box = b
      setBox(b)
      onBoxChange?.(toOriginal(b))
    }

    const onUp = () => {
      const st = stateRef.current
      if (!st.mode) return
      st.mode = null
      emit(st.box)
    }

    window.addEventListener('pointerdown', onDown)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [emit, onBoxChange, toOriginal])

  const reset = () => {
    const r = displayRect()
    if (!r) return
    const init = { x: r.width * 0.05, y: r.height * 0.05, w: r.width * 0.9, h: r.height * 0.9 }
    setBox(init)
    stateRef.current.box = init
    emit(init)
  }

  return (
    <div className="cropper-wrap">
      <div className="cropper">
        <img ref={imgRef} src={imageSrc} onLoad={onLoad} alt="待处理" draggable={false} />
        {box && (
          <div
            className="crop-box"
            style={{ left: box.x, top: box.y, width: box.w, height: box.h }}
          >
            {['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'].map((h) => (
              <span key={h} className={`handle ${h}`} />
            ))}
          </div>
        )}
      </div>
      <div className="cropper-toolbar">
        <button onClick={reset}>全选 / 重置</button>
        <span className="cropper-toolbar__hint">拖动边角确定纸面范围</span>
      </div>
    </div>
  )
}
