import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Download, 
  FileText, 
  Calendar,
  Users,
  Clock,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  PieChart,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Filter
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell } from 'recharts'

const Reports = () => {
  const [reportData, setReportData] = useState({ records: [], stats: {} })
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [viewMode, setViewMode] = useState('calendar') // 'calendar' or 'list'
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(false)
  const [dailyData, setDailyData] = useState([])
  const [chartData, setChartData] = useState([])

  useEffect(() => {
    fetchEmployees()
    generateDailyReport()
  }, [selectedDate])

  const fetchEmployees = async () => {
    try {
      const response = await fetch('/api/employees')
      const data = await response.json()
      setEmployees(data.filter(emp => emp.active))
    } catch (error) {
      console.error('Error fetching employees:', error)
    }
  }

  const generateDailyReport = async () => {
    setLoading(true)
    try {
      const dateStr = selectedDate.toISOString().split('T')[0]
      const response = await fetch(`/api/reports?start_date=${dateStr}&end_date=${dateStr}`)
      const data = await response.json()
      setReportData(data)
      processDailyData(data.records)
      generateChartData(data.records)
    } catch (error) {
      console.error('Error generating report:', error)
    } finally {
      setLoading(false)
    }
  }

  const processDailyData = (records) => {
    const processed = records.map(record => {
      const entryTime = record.entry_time ? new Date(`2000-01-01T${record.entry_time}`) : null
      const exitTime = record.exit_time ? new Date(`2000-01-01T${record.exit_time}`) : null
      const standardStart = new Date('2000-01-01T08:00:00')
      
      return {
        ...record,
        isLate: entryTime && entryTime > standardStart,
        lateMinutes: entryTime && entryTime > standardStart ? 
          Math.floor((entryTime - standardStart) / (1000 * 60)) : 0,
        statusColor: record.status === 'complete' ? 'green' : 
                    record.status === 'late' ? 'red' : 'yellow'
      }
    })
    setDailyData(processed)
  }

  const generateChartData = (records) => {
    const hourlyData = Array.from({length: 24}, (_, i) => ({
      hour: `${i.toString().padStart(2, '0')}:00`,
      entries: 0,
      exits: 0
    }))

    records.forEach(record => {
      if (record.entry_time) {
        const hour = parseInt(record.entry_time.split(':')[0])
        hourlyData[hour].entries++
      }
      if (record.exit_time) {
        const hour = parseInt(record.exit_time.split(':')[0])
        hourlyData[hour].exits++
      }
    })

    setChartData(hourlyData.filter(d => d.entries > 0 || d.exits > 0))
  }

  const navigateDate = (direction) => {
    const newDate = new Date(selectedDate)
    newDate.setDate(newDate.getDate() + direction)
    setSelectedDate(newDate)
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'late': return <AlertTriangle className="w-4 h-4 text-red-500" />
      default: return <XCircle className="w-4 h-4 text-yellow-500" />
    }
  }

  const pieData = [
    { name: 'Completos', value: dailyData.filter(r => r.status === 'complete').length, color: '#10b981' },
    { name: 'Tardíos', value: dailyData.filter(r => r.status === 'late').length, color: '#ef4444' },
    { name: 'Incompletos', value: dailyData.filter(r => r.status === 'incomplete').length, color: '#f59e0b' }
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { duration: 0.5 } }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-8">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-7xl mx-auto space-y-8"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl shadow-lg">
              <BarChart3 className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-gray-900 via-purple-800 to-pink-800 bg-clip-text text-transparent mb-4">
            Reportes de Asistencia
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Análisis detallado de asistencia con estadísticas y visualizaciones
          </p>
        </motion.div>

        {/* Date Navigation */}
        <motion.div variants={itemVariants} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => navigateDate(-1)}
                className="p-2 bg-blue-100 hover:bg-blue-200 rounded-xl transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-blue-600" />
              </motion.button>
              
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedDate.toLocaleDateString('es-ES', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </h2>
                <p className="text-gray-600">Reporte diario de asistencia</p>
              </div>
              
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => navigateDate(1)}
                className="p-2 bg-blue-100 hover:bg-blue-200 rounded-xl transition-colors"
              >
                <ChevronRight className="w-5 h-5 text-blue-600" />
              </motion.button>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="date"
                value={selectedDate.toISOString().split('T')[0]}
                onChange={(e) => setSelectedDate(new Date(e.target.value))}
                className="input-field"
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setViewMode(viewMode === 'calendar' ? 'list' : 'calendar')}
                className="btn btn-primary"
              >
                {viewMode === 'calendar' ? <Filter className="w-4 h-4" /> : <Calendar className="w-4 h-4" />}
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Statistics Cards */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Empleados</p>
                <p className="text-3xl font-bold text-gray-900">{dailyData.length}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-xl">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Asistencias Completas</p>
                <p className="text-3xl font-bold text-green-600">{dailyData.filter(r => r.status === 'complete').length}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Llegadas Tardías</p>
                <p className="text-3xl font-bold text-red-600">{dailyData.filter(r => r.isLate).length}</p>
              </div>
              <div className="p-3 bg-red-100 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Promedio Horas</p>
                <p className="text-3xl font-bold text-purple-600">
                  {dailyData.length > 0 ? 
                    (dailyData.reduce((acc, r) => acc + (r.hours_worked || 0), 0) / dailyData.length).toFixed(1) 
                    : '0.0'}
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-xl">
                <Clock className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Bar Chart */}
          <motion.div variants={itemVariants} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <BarChart3 className="w-6 h-6 text-blue-600 mr-2" />
              Actividad por Hora
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="entries" fill="#3b82f6" name="Entradas" />
                <Bar dataKey="exits" fill="#ef4444" name="Salidas" />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Pie Chart */}
          <motion.div variants={itemVariants} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <PieChart className="w-6 h-6 text-purple-600 mr-2" />
              Estado de Asistencias
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({name, value}) => `${name}: ${value}`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </RechartsPieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Employee Records */}
        <motion.div variants={itemVariants} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-900 flex items-center">
              <Users className="w-6 h-6 text-green-600 mr-2" />
              Registros del Día ({dailyData.length})
            </h3>
            <div className="flex space-x-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.open(`/api/reports/export?start_date=${selectedDate.toISOString().split('T')[0]}&end_date=${selectedDate.toISOString().split('T')[0]}&format=excel`, '_blank')}
                className="btn btn-success flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Excel</span>
              </motion.button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {loading ? (
                <div className="col-span-full text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-500">Cargando registros...</p>
                </div>
              ) : dailyData.length === 0 ? (
                <div className="col-span-full text-center py-12">
                  <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">Sin registros para esta fecha</p>
                </div>
              ) : (
                dailyData.map((record, index) => (
                  <motion.div
                    key={`${record.employee_id}-${index}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className={`p-4 rounded-xl border-l-4 transition-all duration-200 hover:shadow-md ${
                      record.status === 'complete' ? 'bg-green-50 border-green-400' :
                      record.status === 'late' ? 'bg-red-50 border-red-400' :
                      'bg-yellow-50 border-yellow-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold ${
                          record.status === 'complete' ? 'bg-green-500' :
                          record.status === 'late' ? 'bg-red-500' : 'bg-yellow-500'
                        }`}>
                          {record.employee_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{record.employee_name}</p>
                          <p className="text-xs text-gray-500">ID: {record.employee_id}</p>
                        </div>
                      </div>
                      {getStatusIcon(record.status)}
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Entrada:</span>
                        <span className={`font-medium ${record.isLate ? 'text-red-600' : 'text-green-600'}`}>
                          {record.entry_time || '-'}
                          {record.isLate && (
                            <span className="text-xs ml-1">({record.lateMinutes}min tarde)</span>
                          )}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Salida:</span>
                        <span className="font-medium text-gray-900">{record.exit_time || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Horas:</span>
                        <span className="font-medium text-blue-600">{record.hours_worked || '0.0'}h</span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default Reports