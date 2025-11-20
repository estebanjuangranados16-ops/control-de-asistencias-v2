import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Clock, 
  Users,
  Calendar,
  CheckCircle,
  XCircle,
  Trash2
} from 'lucide-react'
import ScheduleModal from '../components/ScheduleModal'

const Schedules = () => {
  const [schedules, setSchedules] = useState([])
  const [employees, setEmployees] = useState([])
  const [currentStatus, setCurrentStatus] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    fetchSchedules()
    fetchEmployees()
    updateCurrentStatus()
    
    // Actualizar estado cada minuto
    const interval = setInterval(updateCurrentStatus, 60000)
    return () => clearInterval(interval)
  }, [])

  const fetchSchedules = async () => {
    try {
      const response = await fetch('/api/schedules')
      const data = await response.json()
      setSchedules(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching schedules:', error)
      setLoading(false)
    }
  }

  const fetchEmployees = async () => {
    try {
      const response = await fetch('/api/employees')
      const data = await response.json()
      setEmployees(data.filter(emp => emp.active))
    } catch (error) {
      console.error('Error fetching employees:', error)
    }
  }

  const updateCurrentStatus = () => {
    const now = new Date()
    const currentDay = now.getDay()
    const currentTime = now.toTimeString().slice(0, 5)
    
    const todaySchedules = schedules.filter(s => s.day_of_week === currentDay)
    
    const status = todaySchedules.map(schedule => {
      let statusType = 'outside'
      let statusText = 'Fuera de horario'
      
      if (currentTime >= schedule.start_time && currentTime <= schedule.end_time) {
        statusType = 'active'
        statusText = 'En horario'
      } else if (currentTime < schedule.start_time) {
        statusType = 'before'
        statusText = 'Antes del horario'
      } else {
        statusType = 'after'
        statusText = 'Después del horario'
      }

      return {
        ...schedule,
        statusType,
        statusText
      }
    })
    
    setCurrentStatus(status)
  }

  const dayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

  const handleDeleteSchedule = async (scheduleId) => {
    if (window.confirm('¿Estás seguro de eliminar este horario?')) {
      try {
        const response = await fetch(`/api/schedules/${scheduleId}`, {
          method: 'DELETE'
        })
        const data = await response.json()
        alert(data.message)
        if (data.success) {
          fetchSchedules()
        }
      } catch (error) {
        alert('Error al eliminar horario')
      }
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">🕰️ Control de Horarios</h1>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Agregar Horario</span>
        </motion.button>
      </motion.div>

      {/* Current Status */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 text-blue-600 mr-2" />
            Estado Actual
          </h3>
          <div className="space-y-3">
            {currentStatus.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No hay horarios para hoy</p>
            ) : (
              currentStatus.map((status, index) => (
                <motion.div
                  key={status.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-3 rounded-lg ${
                    status.statusType === 'active' ? 'bg-green-50 border-l-4 border-green-400' :
                    status.statusType === 'before' ? 'bg-yellow-50 border-l-4 border-yellow-400' :
                    'bg-red-50 border-l-4 border-red-400'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium text-gray-900">{status.employee_name}</p>
                      <p className="text-sm text-gray-600">
                        {status.start_time} - {status.end_time}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {status.statusType === 'active' ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                      <span className={`text-sm font-medium ${
                        status.statusType === 'active' ? 'text-green-600' :
                        status.statusType === 'before' ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {status.statusText}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 text-purple-600 mr-2" />
            Horarios por Empleado
          </h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {employees.map((employee, index) => {
              const empSchedules = schedules.filter(s => s.employee_id === employee.employee_id)
              return (
                <motion.div
                  key={employee.employee_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-3 bg-gray-50 rounded-lg"
                >
                  <p className="font-medium text-gray-900 mb-2">{employee.name}</p>
                  {empSchedules.length === 0 ? (
                    <p className="text-sm text-gray-500">Sin horarios asignados</p>
                  ) : (
                    <div className="space-y-1">
                      {empSchedules.map(schedule => (
                        <p key={schedule.id} className="text-sm text-gray-600">
                          {dayNames[schedule.day_of_week]}: {schedule.start_time} - {schedule.end_time}
                        </p>
                      ))}
                    </div>
                  )}
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.div>

      {/* Schedules Table */}
      <motion.div variants={itemVariants} className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Calendar className="w-5 h-5 text-green-600 mr-2" />
          Todos los Horarios
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Empleado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Día
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entrada
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Salida
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    Cargando horarios...
                  </td>
                </tr>
              ) : schedules.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No hay horarios configurados
                  </td>
                </tr>
              ) : (
                schedules.map((schedule, index) => (
                  <motion.tr
                    key={schedule.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {schedule.employee_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dayNames[schedule.day_of_week]}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {schedule.start_time}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {schedule.end_time}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="badge badge-success">Activo</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleDeleteSchedule(schedule.id)}
                        className="text-red-600 hover:text-red-900 flex items-center space-x-1"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Eliminar</span>
                      </motion.button>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Schedule Modal */}
      <ScheduleModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSave={fetchSchedules}
        employees={employees}
      />
    </motion.div>
  )
}

export default Schedules