import React, { useState } from 'react'
import LiquidGlass from './LiquidGlass.jsx'
import ContextMenu from './ContextMenu.jsx'
import ProjectDetail from './ProjectDetail.jsx'
import ModelPicker from './ModelPicker.jsx'
import { api, pickImageFiles } from '../api.js'
import './MainView.css'

export default function MainView({
  projects,
  settings,
  engines,
  backendOnline,
  onAdd,
  onRefresh,
  onNotify,
  onSaveSettings
}) {
  const [menu, setMenu] = useState(null)
  const [detail, setDetail] = useState(null)
  const viewMode = settings?.view_mode || 'grid'
  const scannerBackend = settings?.feature_backends?.scanner || ''

  const handleAdd = async () => {
    const files = await pickImageFiles()
    await onAdd(files)
  }

  const handleContext = (e, project) => {
    e.preventDefault()
    e.stopPropagation()
    setMenu({ x: e.clientX, y: e.clientY, project })
  }

  const deleteProject = async (project) => {
    try {
      await api.deleteProject(project.source)
      onNotify('已删除文件', 'success')
      onRefresh()
    } catch (err) {
      onNotify('删除失败：' + err.message, 'error')
    }
  }

  const hideProject = async (project) => {
    try {
      await api.hideProject(project.source)
      onNotify('已不在软件内显示', 'success')
      onRefresh()
    } catch (err) {
      onNotify('操作失败：' + err.message, 'error')
    }
  }

  const openOutput = async (path) => {
    if (window.libu?.openPath) {
      await window.libu.openPath(path)
    } else {
      window.open(api.previewUrl(path), '_blank')
    }
  }

  const revealOutput = async (path) => {
    if (window.libu?.showItem) {
      await window.libu.showItem(path)
    } else {
      await openOutput(path)
    }
  }

  return (
    <div className="main-view">
      <header className="main-view__header">
        <div className="main-view__title-wrap">
          <h1 className="main-view__title">吏部</h1>
          <p className="main-view__subtitle">图片 · 扫描件 → 可搜索 PDF / Word 电子文档</p>
        </div>
        <div className="main-view__controls">
          {!backendOnline && (
            <span className="main-view__offline">● 后端离线</span>
          )}
          <ModelPicker
            engines={engines}
            value={scannerBackend}
            defaultBackend={settings?.default_backend || ''}
            onChange={(v) => onSaveSettings?.({ feature_backends: { scanner: v } })}
            label="文档扫描仪使用的 OCR 模型"
          />
          <div className="view-toggle liquid-glass">
            <button
              className={viewMode === 'grid' ? 'active' : ''}
              onClick={() => onSaveSettings?.({ view_mode: 'grid' })}
              title="块状显示"
            >
              <GridIcon />
            </button>
            <button
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => onSaveSettings?.({ view_mode: 'list' })}
              title="条状显示"
            >
              <ListIcon />
            </button>
          </div>
          <button className="main-view__open-dir" onClick={() => api.openOutputDir()}>
            打开输出目录
          </button>
        </div>
      </header>

      <div className={`project-area ${viewMode === 'list' ? 'is-list' : 'is-grid'}`}>
        <LiquidGlass
          className="add-tile"
          interactive
          onClick={handleAdd}
          radius={20}
        >
          <div className="add-tile__inner">
            <span className="add-tile__plus">+</span>
            {viewMode === 'grid' && <span className="add-tile__text">添加图片</span>}
          </div>
        </LiquidGlass>

        {projects.map((p) => (
          <LiquidGlass
            key={p.id}
            className="project-card"
            interactive
            radius={20}
            onClick={() => setDetail(p)}
            onContextMenu={(e) => handleContext(e, p)}
          >
            <div className="project-card__thumb">
              {p.thumbnail ? (
                <img src={p.thumbnail} alt={p.title} draggable={false} />
              ) : (
                <div className="project-card__ph">无预览</div>
              )}
            </div>
            <div className="project-card__meta">
              <div className="project-card__name" title={p.title}>
                {p.title}
              </div>
              <div className="project-card__sub">
                {Object.keys(p.outputs || {}).length > 0
                  ? `输出 ${Object.keys(p.outputs).length} 个文件`
                  : '未处理'}
                <span className="dot">·</span>
                {formatTime(p.updated_at)}
              </div>
            </div>
          </LiquidGlass>
        ))}
      </div>

      {projects.length === 0 && (
        <div className="main-view__empty">
          <p>还没有项目，点击「+」导入一张图片开始吧。</p>
          <p className="hint">处理结果会保存到 ~/文档/吏部</p>
        </div>
      )}

      {menu && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          onClose={() => setMenu(null)}
          items={[
            {
              label: '打开所在位置',
              icon: '📂',
              onClick: () => revealOutput(menu.project.source)
            },
            {
              label: '不在软件内显示该文件',
              icon: '🙈',
              onClick: () => hideProject(menu.project)
            },
            {
              label: '删除文件',
              icon: '🗑',
              danger: true,
              onClick: () => deleteProject(menu.project)
            }
          ]}
        />
      )}

      {detail && (
        <ProjectDetail
          project={detail}
          onClose={() => setDetail(null)}
          onOpenOutput={openOutput}
          onReveal={revealOutput}
          onDelete={async () => {
            await deleteProject(detail)
            setDetail(null)
          }}
        />
      )}
    </div>
  )
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  const now = Date.now()
  const diff = (now - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return d.toLocaleDateString()
}

function GridIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <rect x="3" y="3" width="8" height="8" rx="2" />
      <rect x="13" y="3" width="8" height="8" rx="2" />
      <rect x="3" y="13" width="8" height="8" rx="2" />
      <rect x="13" y="13" width="8" height="8" rx="2" />
    </svg>
  )
}

function ListIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <rect x="3" y="4" width="18" height="3.5" rx="1.5" />
      <rect x="3" y="10.2" width="18" height="3.5" rx="1.5" />
      <rect x="3" y="16.4" width="18" height="3.5" rx="1.5" />
    </svg>
  )
}
