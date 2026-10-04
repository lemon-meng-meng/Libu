import React, { useEffect } from 'react'
import './Toast.css'

export default function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(onClose, 3600)
    return () => clearTimeout(t)
  }, [toast, onClose])

  if (!toast) return null
  return (
    <div className={`toast toast--${toast.type || 'info'}`} key={toast.id}>
      {toast.message}
    </div>
  )
}
