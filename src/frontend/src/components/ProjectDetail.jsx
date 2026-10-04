import React from 'react'
import LiquidGlass from './LiquidGlass.jsx'
import { api } from '../api.js'
import './ProjectDetail.css'

const LABELS = {
  pdf: '双层 PDF',
  word_hidden: 'Word（原图可复制）',
  word_text: 'Word（纯文本）'
}

export default function ProjectDetail({ project, onClose, onOpenOutput, onReveal, onDelete }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <LiquidGlass className="project-detail" radius={26} onClick={(e) => e.stopPropagation()}>
        <div className="project-detail__head">
          <h2>{project.title}</h2>
          <button className="icon-btn" onClick={onClose} title="关闭">
            ✕
          </button>
        </div>
        <div className="project-detail__body">
          <div className="project-detail__preview">
            {project.thumbnail ? (
              <img src={project.thumbnail} alt={project.title} />
            ) : (
              <div className="project-detail__ph">无预览</div>
            )}
          </div>
          <div className="project-detail__outputs">
            <h3>输出文件</h3>
            {Object.keys(project.outputs || {}).length === 0 && (
              <p className="hint">尚未生成输出。</p>
            )}
            {Object.entries(project.outputs || {}).map(([key, path]) => (
              <div key={key} className="output-row">
                <span className="output-row__label">{LABELS[key] || key}</span>
                <div className="output-row__actions">
                  <button onClick={() => onOpenOutput(path)}>打开</button>
                  <a href={api.downloadUrl(path)} download>
                    下载
                  </a>
                </div>
              </div>
            ))}
            <p className="project-detail__source">源文件：{project.source}</p>
          </div>
        </div>
        <div className="project-detail__foot">
          <button className="btn-danger" onClick={onDelete}>
            删除文件
          </button>
          <button className="btn-ghost" onClick={() => (onReveal || onOpenOutput)(project.source)}>
            打开源文件位置
          </button>
        </div>
      </LiquidGlass>
    </div>
  )
}
