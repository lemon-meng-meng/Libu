import React from 'react'
import './LiquidGlass.css'

/**
 * 液态玻璃（Liquid Glass）容器。
 *
 * 采用 liquid-glass-react 的设计语言：半透明背景 + 背景模糊 + 边缘高光 +
 * 轻微折射质感 + 圆角。基于 CSS 实现，无需额外运行时依赖，跨 Electron/浏览器稳定。
 */
export default function LiquidGlass({
  children,
  className = '',
  style = {},
  radius = 22,
  blur = 18,
  tint = 0.10,
  interactive = false,
  as: Tag = 'div',
  ...rest
}) {
  const cssVars = {
    '--lg-radius': `${radius}px`,
    '--lg-blur': `${blur}px`,
    '--lg-tint': tint
  }
  return (
    <Tag
      className={`liquid-glass ${interactive ? 'is-interactive' : ''} ${className}`}
      style={{ ...cssVars, ...style }}
      {...rest}
    >
      <span className="liquid-glass__sheen" aria-hidden="true" />
      <div className="liquid-glass__content">{children}</div>
    </Tag>
  )
}
