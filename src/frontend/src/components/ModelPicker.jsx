import React, { useEffect, useMemo, useRef, useState } from 'react'
import './ModelPicker.css'

const CATEGORY_ORDER = ['local', 'cloud', 'llm', 'agent']

/**
 * 「选择模型」按钮：为单个功能选择 OCR 供应商，互不影响。
 * value 为空串表示"跟随默认引擎"。
 */
export default function ModelPicker({
  engines = [],
  value = '',
  defaultBackend = '',
  onChange,
  label = '选择模型',
  compact = false
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  const grouped = useMemo(() => {
    const g = {}
    for (const e of engines) {
      ;(g[e.category] = g[e.category] || []).push(e)
    }
    for (const k of Object.keys(g)) {
      g[k].sort((a, b) => (a.available === b.available ? 0 : a.available ? -1 : 1))
    }
    return g
  }, [engines])

  const current = engines.find((e) => e.name === value)
  const fallback = engines.find((e) => e.name === defaultBackend)
  const currentLabel = value
    ? current?.label || value
    : `默认${fallback ? '：' + fallback.label : ''}`

  const pick = (name) => {
    onChange?.(name)
    setOpen(false)
  }

  return (
    <div className={`model-picker ${compact ? 'is-compact' : ''}`} ref={ref}>
      <button className="model-picker__btn" onClick={() => setOpen((o) => !o)} title={label}>
        <span className="model-picker__glyph">模</span>
        <span className="model-picker__text">{currentLabel}</span>
        <span className="model-picker__chevron">{open ? '▴' : '▾'}</span>
      </button>

      {open && (
        <div className="model-picker__menu liquid-glass">
          <button className={`model-picker__item ${!value ? 'active' : ''}`} onClick={() => pick('')}>
            <span className={`model-picker__dot ${fallback?.available ? 'ok' : 'no'}`}>●</span>
            <span className="model-picker__item-label">
              跟随默认{fallback ? `（${fallback.label}）` : ''}
            </span>
          </button>
          {CATEGORY_ORDER.flatMap((cat) =>
            (grouped[cat] || []).length ? (
              <div key={cat} className="model-picker__group">
                <div className="model-picker__group-title">
                  {grouped[cat][0].category_label}
                </div>
                {grouped[cat].map((e) => (
                  <button
                    key={e.name}
                    className={`model-picker__item ${value === e.name ? 'active' : ''}`}
                    onClick={() => pick(e.name)}
                    title={e.available ? e.description : e.unavailable_reason || e.description}
                  >
                    <span className={`model-picker__dot ${e.available ? 'ok' : 'no'}`}>●</span>
                    <span className="model-picker__item-label">{e.label}</span>
                    {e.local === false && <span className="model-picker__tag">云</span>}
                    {!e.available && <span className="model-picker__tag warn">不可用</span>}
                  </button>
                ))}
              </div>
            ) : null
          )}
        </div>
      )}
    </div>
  )
}
