import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

export const useSocket = () => {
  const [socket, setSocket] = useState(null)

  useEffect(() => {
    const newSocket = io('http://localhost:5000', {
      transports: ['websocket', 'polling']
    })

    newSocket.on('connect', () => {
      console.log('Connected to server')
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server')
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  return socket
}