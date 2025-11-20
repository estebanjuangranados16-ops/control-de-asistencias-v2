import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, Clock, User } from 'lucide-react'

const LiveNotification = ({ notification, onClose }) => {
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        onClose()
      }, 5000) // Auto-close after 5 seconds

      return () => clearTimeout(timer)
    }
  }, [notification, onClose])

  if (!notification) return null

  const getIcon = () => {
    switch (notification.event_type) {
      case 'entrada':
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case 'salida':
        return <XCircle className="w-6 h-6 text-orange-500" />
      default:
        return <User className="w-6 h-6 text-blue-500" />
    }
  }

  const getBgColor = () => {
    switch (notification.event_type) {
      case 'entrada':
        return 'from-green-500 to-emerald-600'
      case 'salida':
        return 'from-orange-500 to-red-500'
      default:
        return 'from-blue-500 to-purple-600'
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -100, scale: 0.8 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -100, scale: 0.8 }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="fixed top-4 right-4 z-50 max-w-sm"
      >
        <div className={`bg-gradient-to-r ${getBgColor()} rounded-2xl shadow-2xl border border-white/20 overflow-hidden`}>
          <div className="p-4 text-white">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-xl">
                {getIcon()}
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="font-bold text-lg">¡Nuevo Registro!</h3>
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                </div>
                <p className="text-white/90 font-medium">{notification.name}</p>
                <p className="text-white/70 text-sm capitalize">
                  {notification.event_type} • {notification.verify_method}
                </p>
                <div className="flex items-center space-x-1 text-white/60 text-xs mt-1">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(notification.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Progress bar */}
          <motion.div
            initial={{ width: "100%" }}
            animate={{ width: "0%" }}
            transition={{ duration: 5, ease: "linear" }}
            className="h-1 bg-white/30"
          />
        </div>
      </motion.div>
    </AnimatePresence>
  )
}

export default LiveNotification