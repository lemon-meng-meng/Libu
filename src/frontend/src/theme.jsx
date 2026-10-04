import React, { useEffect, useState } from 'react'

const ThemeContext = React.createContext({
  theme: 'system',
  background: 'aurora-blue',
  setTheme: () => {},
  setBackground: () => {}
})

function resolve(theme) {
  if (theme === 'dark') return 'dark'
  if (theme === 'light') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function ThemeProvider({
  initial = 'system',
  initialBackground = 'aurora-blue',
  children
}) {
  const [theme, setTheme] = useState(initial)
  const [background, setBackground] = useState(initialBackground)

  useEffect(() => {
    const apply = () => {
      document.documentElement.dataset.theme = resolve(theme)
    }
    apply()
    if (theme !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [theme])

  useEffect(() => {
    document.documentElement.dataset.bg = background || 'aurora-blue'
  }, [background])

  return (
    <ThemeContext.Provider value={{ theme, background, setTheme, setBackground }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => React.useContext(ThemeContext)
