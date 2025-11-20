import { useState } from 'react'

export const useToast = () => {
  const [toast, setToast] = useState({
    isVisible: false,
    type: 'info',
    title: '',
    message: '',
    duration: 4000
  })

  const showToast = ({ type = 'info', title, message, duration = 4000 }) => {
    setToast({
      isVisible: true,
      type,
      title,
      message,
      duration
    })
  }

  const hideToast = () => {
    setToast(prev => ({ ...prev, isVisible: false }))
  }

  const success = (message, title = 'Éxito') => {
    showToast({ type: 'success', title, message })
  }

  const error = (message, title = 'Error') => {
    showToast({ type: 'error', title, message })
  }

  const warning = (message, title = 'Advertencia') => {
    showToast({ type: 'warning', title, message })
  }

  const info = (message, title = 'Información') => {
    showToast({ type: 'info', title, message })
  }

  return {
    toast,
    showToast,
    hideToast,
    success,
    error,
    warning,
    info
  }
}