import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

export const useSocket = () => {
  const [socket, setSocket] = useState(null)

  useEffect(() => {
    // Conectar al WebSocket del backend
    const newSocket = io('http://localhost:5000', {
      transports: ['polling', 'websocket'],
      upgrade: true,
      rememberUpgrade: true
    })

    newSocket.on('connect', () => {
      console.log('🔗 Conectado al servidor WebSocket')
    })

    newSocket.on('disconnect', (reason) => {
      console.log('❌ Desconectado del servidor WebSocket:', reason)
    })

    newSocket.on('connect_error', (error) => {
      console.error('⚠️ Error de conexión WebSocket:', error)
    })

    newSocket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconectado al servidor (intento ${attemptNumber})`)
    })

    newSocket.on('reconnect_error', (error) => {
      console.error('❌ Error de reconexión:', error)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  return socket
}