import React, { useEffect, useRef } from 'react'
import './ContextMenu.css'

export default function ContextMenu({ x, y, items, onClose }) {
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) onClose()
    }
    const esc = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('pointerdown', handler)
    window.addEventListener('keydown', esc)
    return () => {
      window.removeEventListener('pointerdown', handler)
      window.removeEventListener('keydown', esc)
    }
  }, [onClose])

  return (
    <div
      ref={ref}
      className="context-menu liquid-glass"
      style={{ left: x, top: y }}
      onContextMenu={(e) => e.preventDefault()}
    >
      {items.map((item, i) => (
        <button
          key={i}
          className={`context-menu__item glass-text ${item.danger ? 'danger' : ''}`}
          onClick={() => {
            item.onClick?.()
            onClose()
          }}
        >
          {item.icon && <span className="context-menu__icon">{item.icon}</span>}
          <span className="context-menu__label glass-text">{item.label}</span>
        </button>
      ))}
    </div>
  )
}
