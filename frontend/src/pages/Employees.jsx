import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Play, 
  Pause,
  RefreshCw,
  Users,
  Building2,
  Phone,
  Mail,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react'
import EmployeeModal from '../components/EmployeeModal'
import ConfirmDialog from '../components/ConfirmDialog'
import Toast from '../components/Toast'
import { useToast } from '../hooks/useToast'

const Employees = () => {
  const [employees, setEmployees] = useState([])
  const [filteredEmployees, setFilteredEmployees] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState(null)
  const [loading, setLoading] = useState(true)
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, employee: null })
  const { toast, success, error, hideToast } = useToast()

  useEffect(() => {
    fetchEmployees()
  }, [])

  useEffect(() => {
    const filtered = employees.filter(emp =>
      emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.employee_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (emp.department && emp.department.toLowerCase().includes(searchTerm.toLowerCase()))
    )
    setFilteredEmployees(filtered)
  }, [employees, searchTerm])

  const fetchEmployees = async () => {
    try {
      const response = await fetch('/api/employees')
      const data = await response.json()
      setEmployees(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching employees:', error)
      setLoading(false)
    }
  }

  const handleAddEmployee = () => {
    setEditingEmployee(null)
    setShowModal(true)
  }

  const handleEditEmployee = (employee) => {
    setEditingEmployee(employee)
    setShowModal(true)
  }

  const handleDeleteEmployee = (employee) => {
    setConfirmDialog({ isOpen: true, employee })
  }

  const confirmDeleteEmployee = async () => {
    try {
      const response = await fetch(`/api/employees/${confirmDialog.employee.employee_id}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      
      if (data.success) {
        fetchEmployees()
        success(data.message)
      } else {
        error(data.message)
      }
    } catch (err) {
      error('Error al eliminar empleado')
    } finally {
      setConfirmDialog({ isOpen: false, employee: null })
    }
  }

  const handleToggleEmployee = async (employeeId) => {
    try {
      const response = await fetch(`/api/employees/${employeeId}/toggle`, {
        method: 'POST'
      })
      const data = await response.json()
      alert(data.message)
      if (data.success) {
        fetchEmployees()
      }
    } catch (error) {
      alert('Error al cambiar estado del empleado')
    }
  }

  const handleSyncEmployees = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/sync_employees', {
        method: 'POST'
      })
      const data = await response.json()
      alert(data.message)
      if (data.success) {
        fetchEmployees()
      }
    } catch (error) {
      alert('Error al sincronizar empleados')
    } finally {
      setLoading(false)
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
            <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg">
              <Users className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-4">
            Gestión de Empleados
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Administra y supervisa todos los empleados del sistema de asistencia
          </p>
        </motion.div>

        {/* Stats Cards */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Empleados</p>
                <p className="text-3xl font-bold text-gray-900">{employees.length}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-xl">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Empleados Activos</p>
                <p className="text-3xl font-bold text-green-600">{employees.filter(e => e.active).length}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Empleados Inactivos</p>
                <p className="text-3xl font-bold text-red-600">{employees.filter(e => !e.active).length}</p>
              </div>
              <div className="p-3 bg-red-100 rounded-xl">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Action Bar */}
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar empleados por nombre, ID o departamento..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
            />
          </div>
          <div className="flex space-x-3">
            <motion.button
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleAddEmployee}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 shadow-lg hover:shadow-xl transition-all duration-200"
            >
              <Plus className="w-5 h-5" />
              <span>Nuevo Empleado</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSyncEmployees}
              className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50"
              disabled={loading}
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              <span>Sincronizar</span>
            </motion.button>
          </div>
        </motion.div>



        {/* Employees Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence>
            {loading ? (
              <div className="col-span-full flex items-center justify-center py-20">
                <div className="text-center">
                  <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">Cargando empleados...</p>
                </div>
              </div>
            ) : filteredEmployees.length === 0 ? (
              <div className="col-span-full flex items-center justify-center py-20">
                <div className="text-center">
                  <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg">No hay empleados registrados</p>
                  <p className="text-gray-400 text-sm mt-2">Agrega tu primer empleado para comenzar</p>
                </div>
              </div>
            ) : (
              filteredEmployees.map((employee, index) => (
                <motion.div
                  key={employee.employee_id}
                  initial={{ opacity: 0, y: 20, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -20, scale: 0.9 }}
                  transition={{ delay: index * 0.1, type: "spring", damping: 25, stiffness: 300 }}
                  whileHover={{ y: -8, scale: 1.02 }}
                  className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20 hover:shadow-2xl transition-all duration-300"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-3 rounded-xl ${employee.active ? 'bg-green-100' : 'bg-red-100'}`}>
                        <Users className={`w-6 h-6 ${employee.active ? 'text-green-600' : 'text-red-600'}`} />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg text-gray-900">{employee.name}</h3>
                        <p className="text-sm text-gray-500">ID: {employee.employee_id}</p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      employee.active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {employee.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>

                  <div className="space-y-3 mb-6">
                    <div className="flex items-center space-x-2">
                      <Building2 className="w-4 h-4 text-purple-500" />
                      <span className="text-sm text-gray-600">{employee.department || 'Sin departamento'}</span>
                    </div>
                    
                    {employee.schedule && (
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-orange-500" />
                        <span className="text-sm text-gray-600">
                          {employee.schedule === 'Reacondicionamiento' ? 'Horario Especial (6 marcaciones)' : 'Horario Normal (2 marcaciones)'}
                        </span>
                      </div>
                    )}
                    
                    {employee.phone && (
                      <div className="flex items-center space-x-2">
                        <Phone className="w-4 h-4 text-emerald-500" />
                        <span className="text-sm text-gray-600">{employee.phone}</span>
                      </div>
                    )}
                    
                    {employee.email && (
                      <div className="flex items-center space-x-2">
                        <Mail className="w-4 h-4 text-red-500" />
                        <span className="text-sm text-gray-600">{employee.email}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleEditEmployee(employee)}
                      className="flex-1 bg-blue-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors flex items-center justify-center space-x-1"
                    >
                      <Edit className="w-4 h-4" />
                      <span>Editar</span>
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleToggleEmployee(employee.employee_id)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center ${
                        employee.active 
                          ? 'bg-yellow-500 text-white hover:bg-yellow-600' 
                          : 'bg-green-500 text-white hover:bg-green-600'
                      }`}
                    >
                      {employee.active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleDeleteEmployee(employee)}
                      className="px-3 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors flex items-center justify-center"
                    >
                      <Trash2 className="w-4 h-4" />
                    </motion.button>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </motion.div>

        {/* Employee Modal */}
        <EmployeeModal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          employee={editingEmployee}
          onSave={fetchEmployees}
        />

        <ConfirmDialog
          isOpen={confirmDialog.isOpen}
          onClose={() => setConfirmDialog({ isOpen: false, employee: null })}
          onConfirm={confirmDeleteEmployee}
          title="Eliminar Empleado"
          message={`¿Estás seguro de eliminar a ${confirmDialog.employee?.name}? Esta acción no se puede deshacer.`}
          confirmText="Eliminar"
          type="danger"
        />

        <Toast toast={toast} onClose={hideToast} />
      </motion.div>
    </div>
  )
}

export default Employees