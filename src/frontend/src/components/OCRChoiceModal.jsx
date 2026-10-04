import React, { useMemo, useState } from 'react'
import LiquidGlass from './LiquidGlass.jsx'
import './OCRChoiceModal.css'

const CATEGORY_ORDER = ['local', 'cloud', 'llm', 'agent']

export default function OCRChoiceModal({ engines, defaultBackend, onCancel, onConfirm }) {
  const [enableOcr, setEnableOcr] = useState(true)
  const [backend, setBackend] = useState(() => {
    const list = engines || []
    const def = list.find((e) => e.name === defaultBackend)
    if (def && def.available) return def.name
    const firstOk = list.find((e) => e.available)
    return (firstOk || def || list[0] || {}).name || defaultBackend || 'wechat'
  })
  const [lang, setLang] = useState('chi_sim+eng')
  const [outputs, setOutputs] = useState({ pdf: true, word_hidden: true, word_text: true })

  const grouped = useMemo(() => {
    const g = {}
    for (const e of engines || []) {
      ;(g[e.category] = g[e.category] || []).push(e)
    }
    for (const k of Object.keys(g)) {
      g[k].sort((a, b) => (a.available === b.available ? 0 : a.available ? -1 : 1))
    }
    return g
  }, [engines])

  const selected = (engines || []).find((e) => e.name === backend)
  const isRemote = selected && selected.local === false
  const unavailable = selected && selected.available === false

  const toggleOutput = (k) => setOutputs((o) => ({ ...o, [k]: !o[k] }))
  const anyOutput = outputs.pdf || outputs.word_hidden || outputs.word_text

  const confirm = () => {
    const out = Object.entries(outputs)
      .filter(([, v]) => v)
      .map(([k]) => k)
    onConfirm({
      enableOcr,
      backend,
      lang,
      outputs: enableOcr ? out : ['pdf']
    })
  }

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <LiquidGlass className="ocr-choice" radius={24} onClick={(e) => e.stopPropagation()}>
        <h2 className="ocr-choice__title">这一页是否进行 OCR 文字识别？</h2>
        <p className="ocr-choice__sub">
          开启后可生成「可搜索、可复制」的双层 PDF 与 Word；关闭则只做图像增强并输出 PDF。
        </p>

        <div className="ocr-choice__toggle">
          <button className={enableOcr ? 'active' : ''} onClick={() => setEnableOcr(true)}>
            启用 OCR
          </button>
          <button className={!enableOcr ? 'active' : ''} onClick={() => setEnableOcr(false)}>
            不启用，直接输出
          </button>
        </div>

        {enableOcr && (
          <div className="ocr-choice__body">
            <label className="field">
              <span>识别引擎</span>
              <select value={backend} onChange={(e) => setBackend(e.target.value)}>
                {CATEGORY_ORDER.flatMap((cat) =>
                  (grouped[cat] || []).map((e) => (
                    <option key={e.name} value={e.name}>
                      {(e.available ? '' : '⚠ ') + e.label + '（' + e.category_label + '）'}
                    </option>
                  ))
                )}
              </select>
            </label>

            {selected && (
              <p className="ocr-choice__desc">{selected.description}</p>
            )}
            {unavailable && (
              <p className="warn">该引擎当前不可用：{selected.unavailable_reason}</p>
            )}
            {isRemote && (
              <p className="warn">
                ⚠ 该引擎为云端 / 大模型接口，图片会上传到第三方服务器，请注意隐私安全。
              </p>
            )}

            <label className="field">
              <span>识别语言</span>
              <input value={lang} onChange={(e) => setLang(e.target.value)} />
            </label>

            <div className="ocr-choice__outputs">
              <span className="ocr-choice__outputs-label">输出格式</span>
              <label>
                <input type="checkbox" checked={outputs.pdf} onChange={() => toggleOutput('pdf')} />
                双层 PDF（可搜索）
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={outputs.word_hidden}
                  onChange={() => toggleOutput('word_hidden')}
                />
                Word：原图 + 隐形文字（可复制）
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={outputs.word_text}
                  onChange={() => toggleOutput('word_text')}
                />
                Word：保留文字格式，去除多余元素
              </label>
            </div>
            {!anyOutput && <p className="warn">请至少选择一种输出格式。</p>}
          </div>
        )}

        <div className="ocr-choice__foot">
          <button className="btn-ghost" onClick={onCancel}>
            取消
          </button>
          <button className="btn-primary" disabled={enableOcr && (!anyOutput || unavailable)} onClick={confirm}>
            {enableOcr ? '开始识别' : '生成 PDF'}
          </button>
        </div>
      </LiquidGlass>
    </div>
  )
}
