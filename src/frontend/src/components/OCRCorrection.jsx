import React, { useRef, useState } from 'react'
import './OCRCorrection.css'

/**
 * OCR 结果编辑校正：左侧逐行编辑，右侧原图叠加框选高亮，便于对照修改。
 */
export default function OCRCorrection({ imageSrc, ocrResults, onSave, busy }) {
  const [items, setItems] = useState(
    (ocrResults || []).map((r, i) => ({ id: i, text: r.text || '', box: r.box || null }))
  )
  const [active, setActive] = useState(null)
  const [fit, setFit] = useState(null)
  const [natural, setNatural] = useState(null)
  const imgRef = useRef(null)
  const listRef = useRef(null)

  const updateText = (id, text) =>
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, text } : it)))

  const removeItem = (id) => setItems((prev) => prev.filter((it) => it.id !== id))

  const onImgLoad = () => {
    const img = imgRef.current
    if (img) {
      setFit({ w: img.clientWidth, h: img.clientHeight })
      setNatural({ w: img.naturalWidth, h: img.naturalHeight })
    }
  }

  const handleSave = () => {
    const corrected = items.map(({ text, box }) => ({ text, box }))
    onSave?.(corrected)
  }

  const scale = fit && natural?.w ? fit.w / natural.w : 1

  return (
    <div className="ocr-correction">
      <div className="ocr-correction__list" ref={listRef}>
        <div className="ocr-correction__list-head">
          <h3>OCR 文字校正</h3>
          <span className="count">{items.length} 行</span>
        </div>
        <div className="ocr-correction__scroll">
          {items.map((item, idx) => (
            <div
              key={item.id}
              className={`ocr-line ${active === item.id ? 'active' : ''}`}
              onMouseEnter={() => setActive(item.id)}
              onMouseLeave={() => setActive(null)}
            >
              <span className="ocr-line__no">{idx + 1}</span>
              <input
                value={item.text}
                onChange={(e) => updateText(item.id, e.target.value)}
                placeholder="识别文本"
              />
              <button className="ocr-line__del" onClick={() => removeItem(item.id)} title="删除该行">
                ✕
              </button>
            </div>
          ))}
          {items.length === 0 && <p className="hint">没有识别到文字，可直接生成 PDF。</p>}
        </div>
      </div>

      <div className="ocr-correction__preview">
        <div className="ocr-correction__img-wrap">
          <img ref={imgRef} src={imageSrc} onLoad={onImgLoad} alt="校正预览" draggable={false} />
          {fit &&
            items.map((it) =>
              it.box ? (
                <span
                  key={it.id}
                  className={`ocr-overlay ${active === it.id ? 'active' : ''}`}
                  style={{
                    left: it.box[0] * scale,
                    top: it.box[1] * scale,
                    width: (it.box[2] - it.box[0]) * scale,
                    height: (it.box[3] - it.box[1]) * scale
                  }}
                />
              ) : null
            )}
        </div>
      </div>

      <div className="ocr-correction__foot">
        <span className="hint">修改后点击保存，生成 PDF / Word</span>
        <button className="btn-primary" onClick={handleSave} disabled={busy}>
          {busy ? '正在生成…' : '保存并输出'}
        </button>
      </div>
    </div>
  )
}
