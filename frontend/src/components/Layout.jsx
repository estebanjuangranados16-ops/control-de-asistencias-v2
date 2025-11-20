import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Home, 
  Users, 
  BarChart3, 
  Clock, 
  Wifi, 
  WifiOff,
  Play,
  Pause
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const Layout = ({ children }) => {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [systemStatus, setSystemStatus] = useState({
    connected: false,
    monitoring: false
  })
  const location = useLocation()

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    // Fetch system status
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/dashboard')
        const data = await response.json()
        setSystemStatus({
          connected: data.connected,
          monitoring: data.monitoring
        })
      } catch (error) {
        console.error('Error fetching status:', error)
      }
    }

    fetchStatus()
    const statusInterval = setInterval(fetchStatus, 10000)

    return () => {
      clearInterval(timer)
      clearInterval(statusInterval)
    }
  }, [])

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Empleados', href: '/employees', icon: Users },
    { name: 'Reportes', href: '/reports', icon: BarChart3 },
    { name: 'Horarios', href: '/schedules', icon: Clock },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <motion.header 
        className="bg-white/90 backdrop-blur-sm border-b border-white/20 shadow-lg sticky top-0 z-50"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                <Home className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                  Sistema de Asistencia Hikvision
                </h1>
                <p className="text-gray-600 text-sm font-medium">
                  {format(currentTime, "EEEE, d 'de' MMMM 'de' yyyy - HH:mm:ss", { locale: es })}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <motion.div 
                className={`flex items-center space-x-2 px-4 py-2 rounded-full transition-all duration-300 ${
                  systemStatus.connected 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}
                animate={{ scale: systemStatus.connected ? 1 : 0.95 }}
                transition={{ duration: 0.3 }}
              >
                {systemStatus.connected ? (
                  <Wifi className="w-4 h-4" />
                ) : (
                  <WifiOff className="w-4 h-4" />
                )}
                <span className="text-sm font-semibold">
                  {systemStatus.connected ? 'Conectado' : 'Desconectado'}
                </span>
              </motion.div>
              
              <motion.div 
                className={`flex items-center space-x-2 px-4 py-2 rounded-full transition-all duration-300 ${
                  systemStatus.monitoring 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}
                animate={{ scale: systemStatus.monitoring ? 1 : 0.95 }}
                transition={{ duration: 0.3 }}
              >
                {systemStatus.monitoring ? (
                  <Play className="w-4 h-4" />
                ) : (
                  <Pause className="w-4 h-4" />
                )}
                <span className="text-sm font-semibold">
                  {systemStatus.monitoring ? 'Monitoreando' : 'Pausado'}
                </span>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Navigation */}
      <motion.nav 
        className="bg-white/80 backdrop-blur-sm border-b border-white/20 shadow-sm sticky top-[88px] z-40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <motion.div key={item.name} whileHover={{ y: -2 }} whileTap={{ y: 0 }}>
                  <Link
                    to={item.href}
                    className={`flex items-center space-x-3 py-4 px-6 rounded-t-xl transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-white/60'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-semibold">{item.name}</span>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.nav>

      {/* Main Content */}
      <main className="relative">
        {children}
      </main>
    </div>
  )
}

export default Layout