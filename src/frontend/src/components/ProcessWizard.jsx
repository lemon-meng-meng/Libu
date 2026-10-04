import React, { useCallback, useMemo, useRef, useState } from 'react'
import LiquidGlass from './LiquidGlass.jsx'
import ImageCropper from './ImageCropper.jsx'
import OCRChoiceModal from './OCRChoiceModal.jsx'
import OCRCorrection from './OCRCorrection.jsx'
import { api, pickImageFiles } from '../api.js'
import './ProcessWizard.css'

const LABELS = {
  pdf: '双层 PDF',
  word_hidden: 'Word（原图可复制）',
  word_text: 'Word（纯文本）'
}

let _uid = 0
const nextId = () => `pg_${Date.now().toString(36)}_${(_uid++).toString(36)}`

function baseNameFromSource(source) {
  let name = String(source || '').split(/[\\/]/).pop() || '吏部文档'
  name = name.replace(/\.[^.]+$/, '').replace(/^[0-9a-f]{6,}_/i, '')
  return name || '吏部文档'
}

export default function ProcessWizard({
  sources,
  source,
  settings,
  engines,
  onClose,
  onDone,
  onNotify
}) {
  const initialSources = useMemo(() => {
    if (Array.isArray(sources) && sources.length) return sources.slice()
    return source ? [source] : []
  }, [sources, source])

  const [pages, setPages] = useState(() =>
    initialSources.map((s) => ({ id: nextId(), source: s, box: null, processed: null, results: null }))
  )
  const [current, setCurrent] = useState(0)
  const [step, setStep] = useState('crop')
  const [showChoice, setShowChoice] = useState(false)
  const [outputs, setOutputs] = useState({})
  const [selectedOutputs, setSelectedOutputs] = useState(['pdf', 'word_hidden', 'word_text'])
  const [busy, setBusy] = useState(false)
  const dragFrom = useRef(null)

  const autoEnhance = settings?.auto_enhance !== false
  const firstSource = pages[0]?.source
  const baseName = baseNameFromSource(firstSource)

  const activePage = pages[current]

  const updatePage = useCallback((id, patch) => {
    setPages((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p)))
  }, [])

  const movePage = (index, dir) => {
    setPages((prev) => {
      const next = prev.slice()
      const to = index + dir
      if (to < 0 || to >= next.length) return prev
      ;[next[index], next[to]] = [next[to], next[index]]
      return next
    })
    setCurrent((c) => {
      if (c === index) return Math.max(0, Math.min(pages.length - 1, index + dir))
      return c
    })
  }

  const removePage = (index) => {
    setPages((prev) => {
      if (prev.length <= 1) return prev
      const next = prev.filter((_, i) => i !== index)
      return next
    })
    setCurrent((c) => Math.max(0, Math.min(c, pages.length - 2)))
  }

  const onReorderDrop = (index) => {
    const from = dragFrom.current
    dragFrom.current = null
    if (from === null || from === index) return
    setPages((prev) => {
      const next = prev.slice()
      const [moved] = next.splice(from, 1)
      next.splice(index, 0, moved)
      return next
    })
    setCurrent(index)
  }

  const addMore = async () => {
    const files = await pickImageFiles()
    if (!files || !files.length) return
    const added = []
    for (const f of files) {
      try {
        if (typeof f === 'string') {
          const res = await api.importPath(f)
          added.push(res.path)
        } else {
          const up = await api.upload(f)
          added.push(up.path)
        }
      } catch (e) {
        onNotify?.('导入失败：' + e.message, 'error')
      }
    }
    if (added.length) {
      setPages((prev) => [
        ...prev,
        ...added.map((s) => ({ id: nextId(), source: s, box: null, processed: null, results: null }))
      ])
    }
  }

  const onConfirmChoice = async (choice) => {
    setShowChoice(false)
    setBusy(true)
    try {
      const nextPages = []
      for (const p of pages) {
        const proc = await api.preprocess({ source: p.source, box: p.box, auto_enhance: autoEnhance })
        let results = null
        if (choice.enableOcr) {
          const res = await api.ocr({
            source: proc.path,
            backend: choice.backend,
            lang: choice.lang,
            auto_enhance: false
          })
          results = res.results || []
        }
        nextPages.push({ ...p, processed: proc.path, results })
      }
      setPages(nextPages)

      if (choice.enableOcr) {
        setSelectedOutputs(choice.outputs || ['pdf', 'word_hidden', 'word_text'])
        setStep('correct')
      } else {
        const payloadPages = nextPages.map((p) => ({ source: p.source, box: p.box }))
        const res = await api.generate({
          pages: payloadPages,
          outputs: choice.outputs,
          auto_enhance: autoEnhance,
          enable_ocr: false,
          base_name: baseName
        })
        setSelectedOutputs(choice.outputs || ['pdf'])
        setOutputs(res.outputs || {})
        setStep('done')
        onDone?.()
      }
    } catch (e) {
      onNotify?.('处理失败：' + e.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  const onSaveCorrection = async (corrected) => {
    setBusy(true)
    try {
      const updated = pages.map((p, i) => (i === current ? { ...p, results: corrected } : p))
      setPages(updated)
      const keys = selectedOutputs?.length ? selectedOutputs : ['pdf']
      const payloadPages = updated.map((p) => ({
        source: p.source,
        box: p.box,
        ocr_results: p.results
      }))
      const res = await api.generate({
        pages: payloadPages,
        outputs: keys,
        auto_enhance: autoEnhance,
        enable_ocr: true,
        base_name: baseName
      })
      setOutputs(res.outputs || {})
      setStep('done')
      onDone?.()
    } catch (e) {
      onNotify?.('生成失败：' + e.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop wizard-backdrop">
      <LiquidGlass className="wizard" radius={26}>
        <div className="wizard__head">
          <div className="wizard__title">
            {step === 'crop' && `① 框选纸面范围（共 ${pages.length} 页）`}
            {step === 'correct' && `② 校正 OCR 文字（第 ${current + 1}/${pages.length} 页）`}
            {step === 'done' && '③ 完成'}
          </div>
          <button className="icon-btn" onClick={onClose} title="关闭">
            ✕
          </button>
        </div>

        <div className="wizard__body">
          {step === 'crop' && (
            <div className="wizard__batch">
              <div className="wizard__pages">
                <div className="wizard__pages-head">
                  <span>页面顺序</span>
                  <button className="btn-ghost small" onClick={addMore}>
                    + 添加
                  </button>
                </div>
                <div className="wizard__pages-list">
                  {pages.map((p, i) => (
                    <div
                      key={p.id}
                      className={`page-chip ${i === current ? 'active' : ''}`}
                      draggable
                      onDragStart={() => (dragFrom.current = i)}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => onReorderDrop(i)}
                      onClick={() => setCurrent(i)}
                      title="拖拽可调整顺序"
                    >
                      <span className="page-chip__no">{i + 1}</span>
                      <img
                        className="page-chip__thumb"
                        src={api.thumbnailUrl(p.source)}
                        alt=""
                        draggable={false}
                      />
                      <div className="page-chip__ops">
                        <button onClick={(e) => { e.stopPropagation(); movePage(i, -1) }} title="上移">↑</button>
                        <button onClick={(e) => { e.stopPropagation(); movePage(i, 1) }} title="下移">↓</button>
                        <button
                          className="danger"
                          onClick={(e) => { e.stopPropagation(); removePage(i) }}
                          title="移除"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="wizard__stage">
                {activePage && (
                  <ImageCropper
                    key={activePage.id}
                    imageSrc={api.previewUrl(activePage.source)}
                    onCrop={(box) => updatePage(activePage.id, { box })}
                  />
                )}
              </div>
            </div>
          )}

          {step === 'crop' && (
            <div className="wizard__actions">
              <span className="hint">逐页调整框选范围，可拖拽左侧列表调整页面顺序。</span>
              <div>
                <button className="btn-ghost" onClick={onClose}>
                  取消
                </button>
                <button className="btn-primary" onClick={() => setShowChoice(true)} disabled={!pages.length}>
                  确认范围
                </button>
              </div>
            </div>
          )}

          {step === 'correct' && (
            <>
              <div className="wizard__page-tabs">
                {pages.map((p, i) => (
                  <button
                    key={p.id}
                    className={`wizard__page-tab ${i === current ? 'active' : ''}`}
                    onClick={() => setCurrent(i)}
                  >
                    第 {i + 1} 页
                  </button>
                ))}
              </div>
              {activePage && (
                <OCRCorrection
                  key={activePage.id}
                  imageSrc={api.previewUrl(activePage.processed || activePage.source)}
                  ocrResults={activePage.results || []}
                  onSave={onSaveCorrection}
                  busy={busy}
                />
              )}
            </>
          )}

          {step === 'done' && (
            <div className="wizard__done">
              <div className="wizard__done-icon">✓</div>
              <p>文件已保存到 ~/文档/吏部</p>
              <div className="wizard__outputs">
                {Object.entries(outputs).map(([k, p]) => (
                  <div key={k} className="wizard__output-row">
                    <span>{LABELS[k] || k}</span>
                    <a href={api.downloadUrl(p)} download>
                      下载
                    </a>
                  </div>
                ))}
              </div>
              <div className="wizard__actions">
                <button className="btn-ghost" onClick={() => api.openOutputDir()}>
                  打开输出目录
                </button>
                <button className="btn-primary" onClick={onClose}>
                  完成
                </button>
              </div>
            </div>
          )}
        </div>

        {busy && (
          <div className="wizard__busy">
            <div className="spinner" />
            <span>
              {step === 'correct' ? '正在生成文档…' : '正在识别，请稍候…'}
            </span>
          </div>
        )}
      </LiquidGlass>

      {showChoice && (
        <OCRChoiceModal
          engines={engines}
          defaultBackend={settings?.feature_backends?.scanner || settings?.default_backend}
          onCancel={() => setShowChoice(false)}
          onConfirm={onConfirmChoice}
        />
      )}
    </div>
  )
}
