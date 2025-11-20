import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Users, 
  Clock, 
  UserCheck,
  UserX,
  Activity,
  BarChart3,
  Eye,
  RefreshCw
} from 'lucide-react'

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    total_records: 0,
    unique_employees: 0,
    employees_inside: [],
    employees_outside: [],
    recent_records: [],
    connected: false,
    monitoring: false
  })
  const [refreshing, setRefreshing] = useState(false)

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/dashboard')
      const data = await response.json()
      console.log('Firebase data:', data)
      setDashboardData(data)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    }
  }

  const handleRefreshActivity = async () => {
    setRefreshing(true)
    await fetchDashboardData()
    setTimeout(() => setRefreshing(false), 500)
  }

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 5000)
    return () => clearInterval(interval)
  }, [])

  const stats = [
    {
      name: 'Total Registros',
      value: dashboardData.total_records,
      icon: Clock,
      color: 'from-blue-500 to-blue-600'
    },
    {
      name: 'Empleados Activos',
      value: dashboardData.unique_employees,
      icon: Users,
      color: 'from-green-500 to-green-600'
    },
    {
      name: 'Empleados Dentro',
      value: dashboardData.employees_inside.length,
      icon: UserCheck,
      color: 'from-emerald-500 to-emerald-600'
    },
    {
      name: 'Empleados Fuera',
      value: dashboardData.employees_outside.length,
      icon: UserX,
      color: 'from-red-500 to-red-600'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg">
              <BarChart3 className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-4">
            Dashboard de Asistencia
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Monitoreo en tiempo real del sistema de control de asistencia
          </p>
          <div className="flex items-center justify-center mt-4 space-x-4">
            <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
              dashboardData.connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                dashboardData.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              }`}></div>
              <span className="text-sm font-medium">
                {dashboardData.connected ? 'Dispositivo Conectado' : 'Dispositivo Desconectado'}
              </span>
            </div>
            <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
              dashboardData.monitoring ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
            }`}>
              <Eye className="w-4 h-4" />
              <span className="text-sm font-medium">
                {dashboardData.monitoring ? 'Monitoreando' : 'En Espera'}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <motion.div
                key={stat.name}
                className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20 hover:shadow-2xl transition-all duration-300"
                whileHover={{ scale: 1.05, y: -5 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color} shadow-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-gray-700">{stat.name}</h3>
              </motion.div>
            )
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Empleados Dentro */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 flex items-center">
                <div className="p-2 bg-green-100 rounded-xl mr-3">
                  <UserCheck className="w-6 h-6 text-green-600" />
                </div>
                Empleados Dentro
              </h3>
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold">
                {dashboardData.employees_inside.length}
              </span>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {dashboardData.employees_inside.length === 0 ? (
                <div className="text-center py-12">
                  <UserCheck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">Nadie dentro</p>
                </div>
              ) : (
                dashboardData.employees_inside.map((emp, index) => (
                  <div
                    key={emp.id}
                    className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold text-sm">
                          {emp.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{emp.name}</p>
                        <p className="text-sm text-gray-600">ID: {emp.id}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-green-700">
                        {emp.time ? new Date(emp.time).toLocaleTimeString() : ''}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Empleados Fuera */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 flex items-center">
                <div className="p-2 bg-red-100 rounded-xl mr-3">
                  <UserX className="w-6 h-6 text-red-600" />
                </div>
                Empleados Fuera
              </h3>
              <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-semibold">
                {dashboardData.employees_outside.length}
              </span>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {dashboardData.employees_outside.length === 0 ? (
                <div className="text-center py-12">
                  <UserX className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">Todos dentro</p>
                </div>
              ) : (
                dashboardData.employees_outside.map((emp, index) => (
                  <div
                    key={emp.id}
                    className="flex items-center justify-between p-4 bg-gradient-to-r from-red-50 to-pink-50 rounded-xl border border-red-100"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold text-sm">
                          {emp.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{emp.name}</p>
                        <p className="text-sm text-gray-600">ID: {emp.id}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-red-700">
                        {emp.time ? new Date(emp.time).toLocaleTimeString() : 'Sin registro'}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Actividad Reciente */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 flex items-center">
                <div className="p-2 bg-blue-100 rounded-xl mr-3">
                  <Activity className="w-6 h-6 text-blue-600" />
                </div>
                Actividad Reciente
              </h3>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleRefreshActivity}
                disabled={refreshing}
                className="p-2 bg-blue-100 hover:bg-blue-200 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 text-blue-600 ${refreshing ? 'animate-spin' : ''}`} />
              </motion.button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              <div className="text-xs text-gray-400 mb-2">
                Debug: {dashboardData.recent_records?.length || 0} registros
              </div>
              {!dashboardData.recent_records || dashboardData.recent_records.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">Sin actividad reciente</p>
                  <p className="text-xs text-gray-400">Array: {JSON.stringify(dashboardData.recent_records)}</p>
                </div>
              ) : (
                dashboardData.recent_records.map((record, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-xl border-l-4 ${
                      record[1] === 'entrada' 
                        ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-400' 
                        : 'bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-400'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                          record[1] === 'entrada' ? 'bg-green-500' : 'bg-orange-500'
                        }`}>
                          {record[0].charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{record[0]}</p>
                          <p className="text-sm text-gray-600">
                            {new Date(record[2]).toLocaleString()}
                          </p>
                          <p className="text-xs text-gray-500">{record[3]}</p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        record[1] === 'entrada' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-orange-100 text-orange-800'
                      }`}>
                        {record[1].toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard