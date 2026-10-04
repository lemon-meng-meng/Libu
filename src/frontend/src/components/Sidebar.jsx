import React from 'react'
import './Sidebar.css'

const NAV = [
  { key: 'main', glyph: '主', label: '主页', title: '主界面' },
  { key: 'viewer', glyph: '图', label: '图片查看器', title: '图片查看器' },
  { key: 'screenshot', glyph: '截', label: '截屏OCR', title: '截屏 OCR' },
  { key: 'settings', glyph: <GearIcon />, label: '设置', title: '设置' }
]

export default function Sidebar({ view, setView }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__logo" title="吏部 · Libu">
        吏
      </div>
      <nav className="sidebar__nav">
        {NAV.map((item) => (
          <button
            key={item.key}
            className={`sidebar__btn ${view === item.key ? 'active' : ''}`}
            onClick={() => setView(item.key)}
            title={item.title}
          >
            <span className="sidebar__glyph">{item.glyph}</span>
            <span className="sidebar__label">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar__spacer" />
      <div className="sidebar__version">v0.4.0</div>
    </aside>
  )
}

function GearIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="3.2" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  )
}
