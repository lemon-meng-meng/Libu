import React, { useEffect, useMemo, useState } from 'react'
import LiquidGlass from './LiquidGlass.jsx'
import ModelPicker from './ModelPicker.jsx'
import { api } from '../api.js'
import './SettingsView.css'

const LLM_PROVIDERS = [
  { key: 'deepseek', label: 'DeepSeek', url: 'https://platform.deepseek.com/' },
  { key: 'glm', label: '智谱 GLM', url: 'https://open.bigmodel.cn/' },
  { key: 'kimi', label: 'Kimi', url: 'https://platform.moonshot.cn/' },
  { key: 'minimax', label: 'MiniMax', url: 'https://www.minimaxi.com/' },
  { key: 'stepfun', label: '阶跃星辰', url: 'https://platform.stepfun.com/' },
  { key: 'qwen', label: '通义千问 Qwen', url: 'https://dashscope.aliyun.com/' },
  { key: 'yi', label: '零一万物 Yi', url: 'https://platform.lingyiwanwu.com/' },
  { key: 'nvidia', label: '英伟达 NIM', url: 'https://build.nvidia.com/' },
  { key: 'hunyuan', label: '腾讯混元', url: 'https://cloud.tencent.com/product/hunyuan' }
]

const AGENT_PROVIDERS = [
  { key: 'opencode', label: 'OpenCode', url: 'https://opencode.ai/' },
  { key: 'deepseek_harness', label: 'DeepSeek Harness', url: 'https://github.com/deepseek-ai' },
  { key: 'claude_code', label: 'Claude Code', url: 'https://docs.anthropic.com/en/docs/claude-code' },
  { key: 'codex', label: 'Codex', url: 'https://openai.com/codex/' },
  { key: 'cherry_studio', label: 'Cherry Studio', url: 'https://cherry-ai.com/' },
  { key: 'ollama', label: 'Ollama', url: 'https://ollama.com/' },
  { key: 'lmstudio', label: 'LM Studio', url: 'https://lmstudio.ai/' }
]

const BACKGROUNDS = [
  { key: 'aurora-blue', label: '极光蓝（默认）' },
  { key: 'midnight-purple', label: '午夜紫' },
  { key: 'sunset-rose', label: '落日玫瑰' },
  { key: 'emerald-night', label: '翡翠夜' },
  { key: 'graphite', label: '石墨灰' },
  { key: 'dawn', label: '黎明' },
  { key: 'ocean', label: '深海' },
  { key: 'forest', label: '森林' }
]

export default function SettingsView({ settings, engines, onSave, onNotify, onRefreshProjects }) {
  const [draft, setDraft] = useState(settings || {})
  const [models, setModels] = useState([])
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    setDraft((d) => {
      if (!settings) return d
      return {
        ...settings,
        providers: { ...(settings.providers || {}), ...(d.providers || {}) },
        feature_backends: {
          ...(settings.feature_backends || {}),
          ...(d.feature_backends || {})
        }
      }
    })
  }, [settings])

  const loadModels = async () => {
    try {
      const data = await api.models()
      setModels(data.models || [])
    } catch (_) {}
  }

  useEffect(() => {
    loadModels()
  }, [])

  const providers = draft.providers || {}
  const featureBackends = draft.feature_backends || {}
  const wechatEngine = useMemo(
    () => (engines || []).find((e) => e.name === 'wechat'),
    [engines]
  )

  const updateProvider = (key, patch) =>
    setDraft((d) => ({
      ...d,
      providers: { ...d.providers, [key]: { ...(d.providers?.[key] || {}), ...patch } }
    }))

  const saveProvider = async (key, extra = {}) => {
    const merged = { ...(providers[key] || {}), ...(extra || {}) }
    const saved = await onSave({ providers: { [key]: merged } })
    if (saved) loadModels()
    return saved
  }

  const onImportModel = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    try {
      await api.importModel(file, file.name.replace(/\.zip$/i, ''))
      onNotify('模型导入成功', 'success')
      await loadModels()
    } catch (err) {
      onNotify('导入失败：' + err.message, 'error')
    } finally {
      setImporting(false)
      e.target.value = ''
    }
  }

  const deleteModel = async (name) => {
    try {
      await api.deleteModel(name)
      onNotify('已删除模型 ' + name, 'success')
      await loadModels()
    } catch (err) {
      onNotify('删除失败：' + err.message, 'error')
    }
  }

  const localEngines = (engines || []).filter((e) => e.category === 'local')

  return (
    <div className="settings-view">
      <header className="settings-view__header">
        <h1>设置</h1>
        <p className="hint">所有配置只保存在本机 ~/.config/libu，不会上传。</p>
      </header>

      <div className="settings-view__scroll">
        {/* 外观 */}
        <Section title="外观与主题" desc="界面主题、渐变底色、文件显示方式与图像增强">
          <div className="field-row">
            <span className="field-label">主题</span>
            <div className="segmented">
              {[
                ['system', '跟随系统'],
                ['light', '亮色'],
                ['dark', '暗色']
              ].map(([v, label]) => (
                <button
                  key={v}
                  className={(draft.theme || 'system') === v ? 'active' : ''}
                  onClick={() => onSave({ theme: v })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="field-col">
            <span className="field-label">渐变底色</span>
            <div className="bg-picker">
              {BACKGROUNDS.map((b) => (
                <button
                  key={b.key}
                  className={`bg-swatch bg-${b.key} ${
                    (draft.background || 'aurora-blue') === b.key ? 'active' : ''
                  }`}
                  title={b.label}
                  onClick={() => onSave({ background: b.key })}
                >
                  <span className="bg-swatch__label">{b.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="field-row">
            <span className="field-label">文件显示</span>
            <div className="segmented">
              {[
                ['grid', '块状'],
                ['list', '条状']
              ].map(([v, label]) => (
                <button
                  key={v}
                  className={(draft.view_mode || 'grid') === v ? 'active' : ''}
                  onClick={() => onSave({ view_mode: v })}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="field-row">
            <span className="field-label">自动图像增强（纠偏 / 去阴影 / 白底）</span>
            <Toggle
              checked={draft.auto_enhance !== false}
              onChange={(v) => onSave({ auto_enhance: v })}
            />
          </div>
        </Section>

        {/* 各功能的模型选择 */}
        <Section
          title="各功能的 OCR 模型"
          desc="文档扫描仪、图片查看器、截屏 OCR 可分别使用不同的供应商，互不影响"
        >
          <div className="feature-model-row">
            <span className="field-label">文档扫描仪（主界面）</span>
            <ModelPicker
              engines={engines}
              value={featureBackends.scanner || ''}
              defaultBackend={draft.default_backend || ''}
              onChange={(v) => onSave({ feature_backends: { scanner: v } })}
            />
          </div>
          <div className="feature-model-row">
            <span className="field-label">图片查看器</span>
            <ModelPicker
              engines={engines}
              value={featureBackends.viewer || ''}
              defaultBackend={draft.default_backend || ''}
              onChange={(v) => onSave({ feature_backends: { viewer: v } })}
            />
          </div>
          <div className="feature-model-row">
            <span className="field-label">截屏 OCR</span>
            <ModelPicker
              engines={engines}
              value={featureBackends.screenshot || ''}
              defaultBackend={draft.default_backend || ''}
              onChange={(v) => onSave({ feature_backends: { screenshot: v } })}
            />
          </div>
          <div className="field-row">
            <span className="field-label">默认 OCR 引擎（未单独指定时使用）</span>
            <select
              className="text-input"
              value={draft.default_backend || 'wechat'}
              onChange={(e) => onSave({ default_backend: e.target.value })}
            >
              {Object.entries(
                (engines || []).reduce((acc, e) => {
                  ;(acc[e.category_label] = acc[e.category_label] || []).push(e)
                  return acc
                }, {})
              ).map(([cat, list]) => (
                <optgroup key={cat} label={cat}>
                  {list.map((e) => (
                    <option key={e.name} value={e.name}>
                      {e.available ? '' : '⚠ '}
                      {e.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        </Section>

        {/* 截屏 OCR */}
        <Section title="截屏 OCR" desc="托盘图标点击「截屏 OCR」即可在屏幕上框选并识别">
          <div className="field-row">
            <span className="field-label">快捷键</span>
            <input
              className="text-input"
              value={draft.screenshot_hotkey || 'Ctrl+Alt+O'}
              onChange={(e) => setDraft((d) => ({ ...d, screenshot_hotkey: e.target.value }))}
              onBlur={async () => {
                const hk = draft.screenshot_hotkey || 'Ctrl+Alt+O'
                await onSave({ screenshot_hotkey: hk })
                const res = await window.libu?.setHotkey?.(hk)
                if (res && res.ok === false) {
                  onNotify?.('快捷键注册失败，可能已被占用：' + hk, 'error')
                }
              }}
            />
          </div>
          <div className="field-row">
            <span className="field-label">随软件启动托盘助手</span>
            <Toggle
              checked={draft.screenshot_autostart !== false}
              onChange={(v) => onSave({ screenshot_autostart: v })}
            />
          </div>
          <p className="hint">
            托盘助手使用系统 GTK，若系统缺少相关组件，也可在「截屏 OCR」页面使用内置的应用内框选。
          </p>
        </Section>

        {/* 本地模型 */}
        <Section
          title="本地 OCR 模型"
          desc="导入常见 OCR 模型压缩包（如 wechat_ocr.zip），离线识别、数据不出本机"
        >
          <div className="engine-status">
            {localEngines.map((e) => (
              <div key={e.name} className={`engine-chip ${e.available ? 'ok' : 'no'}`}>
                <span className="engine-chip__dot">{e.available ? '●' : '○'}</span>
                <span>{e.label}</span>
                {!e.available && <span className="engine-chip__reason">{e.unavailable_reason}</span>}
              </div>
            ))}
          </div>

          <div className="model-actions">
            <label className="btn-ghost file-btn">
              {importing ? '正在导入…' : '导入模型 zip'}
              <input type="file" accept=".zip" hidden onChange={onImportModel} />
            </label>
            <span className="hint">
              可导入 OCR Model/wechat_ocr.zip（微信 OCR）或
              OCR Model/paddleocr_ppocrv5.zip（PaddleOCR，配合「自定义本地模型 (ONNX)」使用）
            </span>
          </div>

          <div className="model-list">
            {models.length === 0 && <p className="hint">尚未导入任何本地模型。</p>}
            {models.map((m) => (
              <div key={m.name} className="model-item">
                <div className="model-item__info">
                  <strong>{m.name}</strong>
                  <span className="hint">
                    {m.kind} · {(m.size / 1024 / 1024).toFixed(1)} MB · {m.file_count} 个文件
                  </span>
                </div>
                <button className="btn-danger-ghost" onClick={() => deleteModel(m.name)}>
                  删除
                </button>
              </div>
            ))}
          </div>

          {wechatEngine && !wechatEngine.available && (
            <p className="warn">
              微信 OCR 暂不可用：{wechatEngine.unavailable_reason}。说明：微信 OCR 的 .xnet 权重跨平台通用，
              但运行需要微信客户端提供的 libmmmojo.so 等库；请在下方配置运行库目录或自定义命令。
            </p>
          )}

          <ProviderFields
            fields={[
              { key: 'lib_dirs', label: '微信运行库目录（逗号分隔）', type: 'list' },
              { key: 'command', label: '自定义命令模板（逗号分隔，可选）', type: 'list' }
            ]}
            values={providers.wechat_ocr || {}}
            onChange={(patch) => updateProvider('wechat_ocr', patch)}
            onSave={() => saveProvider('wechat_ocr')}
          />
        </Section>

        {/* 在线 OCR */}
        <Section title="在线 OCR 引擎" desc="图片会上传到第三方服务器，请注意隐私安全">
          <CloudNotice />
          <ProviderCard
            title="OCR.space"
            url="https://ocr.space/apis"
            fields={[
              { key: 'api_key', label: 'API Key', type: 'password' },
              { key: 'endpoint', label: '接口地址', type: 'text' }
            ]}
            values={providers.ocr_space || {}}
            meta={engines?.find((e) => e.name === 'ocr_space')}
            onChange={(patch) => updateProvider('ocr_space', patch)}
            onSave={() => saveProvider('ocr_space')}
          />
          <ProviderCard
            title="百度云 OCR"
            url="https://cloud.baidu.com/product/ocr"
            fields={[
              { key: 'api_key', label: 'API Key', type: 'password' },
              { key: 'secret_key', label: 'Secret Key', type: 'password' }
            ]}
            values={providers.baidu_ocr || {}}
            meta={engines?.find((e) => e.name === 'baidu_ocr')}
            onChange={(patch) => updateProvider('baidu_ocr', patch)}
            onSave={() => saveProvider('baidu_ocr')}
          />
          <ProviderCard
            title="PaddleOCR 在线（飞桨星河）"
            url="https://aistudio.baidu.com/paddleocr"
            fields={[
              { key: 'api_key', label: '访问令牌（Access Token）', type: 'password' },
              { key: 'endpoint', label: '接口地址', type: 'text' },
              { key: 'base_url', label: '服务主页 / Base', type: 'text' },
              { key: 'model', label: '模型名称', type: 'text' }
            ]}
            values={providers.paddleocr_cloud || {}}
            meta={engines?.find((e) => e.name === 'paddleocr_cloud')}
            onChange={(patch) => updateProvider('paddleocr_cloud', patch)}
            onSave={() => saveProvider('paddleocr_cloud')}
          />
        </Section>

        {/* 大模型 API */}
        <Section title="大模型 API" desc="使用视觉大模型进行 OCR / 版面理解，点击卡片展开填写">
          <CloudNotice />
          {LLM_PROVIDERS.map((p) => (
            <ProviderCard
              key={p.key}
              title={p.label}
              url={p.url}
              providerKey={p.key}
              detectable
              fields={[
                { key: 'api_key', label: 'API Key', type: 'password' },
                { key: 'base_url', label: 'Base URL', type: 'text' },
                { key: 'model', label: '模型名称', type: 'text' }
              ]}
              values={providers[p.key] || {}}
              meta={engines?.find((e) => e.name === p.key)}
              onChange={(patch) => updateProvider(p.key, patch)}
              onSave={() => saveProvider(p.key)}
              onSaveExtra={(extra) => saveProvider(p.key, extra)}
            />
          ))}
        </Section>

        {/* Agent */}
        <Section title="Agent / 本地 AI 助手" desc="连接本机运行的 AI 服务进行识别，点击卡片展开">
          {AGENT_PROVIDERS.map((p) => (
            <ProviderCard
              key={p.key}
              title={p.label}
              url={p.url}
              providerKey={p.key}
              detectable
              fields={[
                { key: 'enabled', label: '启用该引擎', type: 'toggle' },
                { key: 'base_url', label: '服务地址', type: 'text' },
                { key: 'api_key', label: 'API Key（可选）', type: 'password' },
                { key: 'model', label: '模型名称', type: 'text' }
              ]}
              values={providers[p.key] || {}}
              meta={engines?.find((e) => e.name === p.key)}
              onChange={(patch) => updateProvider(p.key, patch)}
              onSave={() => saveProvider(p.key)}
              onSaveExtra={(extra) => saveProvider(p.key, extra)}
            />
          ))}
        </Section>

        <Section title="关于" desc="吏部 · Libu">
          <p className="hint">
            图片转电子文档工具，支持双层 PDF 与 Word 输出。开源许可证 GPL-3.0-or-later。
            本项目与汉王科技、腾讯微信无任何关联。
          </p>
          <p className="hint">输出目录：~/文档/吏部</p>
        </Section>
      </div>
    </div>
  )
}

function Section({ title, desc, children }) {
  return (
    <LiquidGlass className="settings-section" radius={22}>
      <div className="settings-section__head">
        <h2>{title}</h2>
        {desc && <p className="hint">{desc}</p>}
      </div>
      <div className="settings-section__body">{children}</div>
    </LiquidGlass>
  )
}

function ProviderCard({ title, url, fields, values, meta, onChange, onSave, onSaveExtra, providerKey, detectable }) {
  const [open, setOpen] = useState(false)
  const available = meta?.available
  return (
    <div className={`provider-card open-${open}`}>
      <div className="provider-card__head" onClick={() => setOpen((o) => !o)}>
        <div className="provider-card__title">
          <span className={`status-dot ${available ? 'ok' : 'no'}`}>●</span>
          {title}
          {meta && <span className="provider-card__badge">{meta.category_label}</span>}
        </div>
        <span className="provider-card__chevron">{open ? '▾' : '▸'}</span>
      </div>
      {open && (
        <div className="provider-card__body">
          {url && (
            <a className="provider-card__link" href={url} target="_blank" rel="noreferrer">
              获取 API Key ↗
            </a>
          )}
          <ProviderFields fields={fields} values={values} onChange={onChange} onSave={onSave} />
          {detectable && providerKey && (
            <ModelDetector
              providerKey={providerKey}
              values={values}
              onChange={onChange}
              onSave={onSave}
              onSaveExtra={onSaveExtra}
            />
          )}
          {meta && !available && <p className="warn">{meta.unavailable_reason}</p>}
        </div>
      )}
    </div>
  )
}

function ModelDetector({ providerKey, values, onChange, onSave, onSaveExtra }) {
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const [ok, setOk] = useState(null)
  const [detected, setDetected] = useState(values?.models || [])
  const selected = values?.models || []
  const active = values?.model || ''

  const detect = async (save = false) => {
    setBusy(true)
    setMsg('')
    try {
      const data = await api.providerModels(providerKey, values)
      const list = data.models || []
      setDetected(list)
      const patch = { models: list }
      if (list.length && !active) patch.model = list[0]
      onChange(patch)
      setOk(true)
      setMsg(list.length ? `检测到 ${list.length} 个模型` : '连接成功，但未返回模型列表')
      if (save) {
        if (onSaveExtra) await onSaveExtra(patch)
        else await onSave()
      }
    } catch (e) {
      setOk(false)
      setMsg(e.message)
    } finally {
      setBusy(false)
    }
  }

  const test = async () => {
    setBusy(true)
    setMsg('')
    try {
      const data = await api.providerTest(providerKey, values)
      setOk(!!data.ok)
      setMsg(data.message)
    } catch (e) {
      setOk(false)
      setMsg(e.message)
    } finally {
      setBusy(false)
    }
  }

  const toggleModel = (name) => {
    const set = new Set(selected)
    if (set.has(name)) set.delete(name)
    else set.add(name)
    onChange({ models: Array.from(set) })
  }

  return (
    <div className="model-detector">
      <div className="model-detector__actions">
        <button className="btn-ghost small" onClick={() => detect(false)} disabled={busy}>
          {busy ? '检测中…' : '自动检测模型'}
        </button>
        <button className="btn-ghost small" onClick={test} disabled={busy}>
          测试连接
        </button>
        <button className="btn-primary small" onClick={() => detect(true)} disabled={busy}>
          检测并保存
        </button>
      </div>
      {msg && (
        <p className={`model-detector__msg ${ok === false ? 'err' : ok ? 'ok' : ''}`}>{msg}</p>
      )}
      {detected.length > 0 && (
        <div className="model-detector__list">
          <span className="hint">勾选要保存的模型，点击名称设为当前使用：</span>
          <div className="model-detector__chips">
            {detected.map((m) => (
              <span
                key={m}
                className={`model-chip ${active === m ? 'active' : ''}`}
                title="点击设为当前模型"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(m)}
                  onChange={() => toggleModel(m)}
                  onClick={(e) => e.stopPropagation()}
                />
                <button
                  type="button"
                  className="model-chip__name"
                  onClick={() => onChange({ model: m })}
                >
                  {m}
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ProviderFields({ fields, values, onChange, onSave }) {
  return (
    <div className="provider-fields">
      {fields.map((f) => {
        const raw = values?.[f.key]
        if (f.type === 'toggle') {
          return (
            <div key={f.key} className="field-line field-line--toggle">
              <span>{f.label}</span>
              <Toggle checked={raw === true} onChange={(v) => onChange({ [f.key]: v })} />
            </div>
          )
        }
        const value = f.type === 'list' ? (Array.isArray(raw) ? raw.join(', ') : raw ?? '') : raw ?? ''
        return (
          <label key={f.key} className="field-line">
            <span>{f.label}</span>
            <input
              className="text-input"
              type={f.type === 'password' ? 'password' : 'text'}
              value={value}
              placeholder={f.placeholder}
              onChange={(e) =>
                onChange({
                  [f.key]:
                    f.type === 'list'
                      ? e.target.value
                          .split(',')
                          .map((s) => s.trim())
                          .filter(Boolean)
                      : e.target.value
                })
              }
            />
          </label>
        )
      })}
      <div className="provider-fields__foot">
        <button className="btn-primary small" onClick={onSave}>
          保存
        </button>
      </div>
    </div>
  )
}

function Toggle({ checked, onChange }) {
  return (
    <button
      className={`toggle ${checked ? 'on' : ''}`}
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
    >
      <span className="toggle__knob" />
    </button>
  )
}

function CloudNotice() {
  return (
    <p className="warn cloud-notice">
      ⚠ 隐私提示：以下引擎会把图片上传到公网服务器，请勿用于身份证、合同等敏感文档。
    </p>
  )
}
