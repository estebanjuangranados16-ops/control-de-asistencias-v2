import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Save, User, Clock, Building2, Phone, Mail, Hash } from 'lucide-react'

const EmployeeModal = ({ isOpen, onClose, employee, onSave }) => {
  const [formData, setFormData] = useState({
    employee_id: '',
    name: '',
    department: 'General',
    phone: '',
    email: '',
    schedule: 'Normal'
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (employee) {
      setFormData({
        employee_id: employee.employee_id,
        name: employee.name,
        department: employee.department || 'General',
        phone: employee.phone || '',
        email: employee.email || '',
        schedule: employee.schedule || 'Normal'
      })
    } else {
      setFormData({
        employee_id: '',
        name: '',
        department: 'General',
        phone: '',
        email: '',
        schedule: 'Normal'
      })
    }
  }, [employee])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const url = employee 
        ? `/api/employees/${employee.employee_id}` 
        : '/api/add_employee'
      
      const method = employee ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()
      
      if (data.success) {
        onSave()
        onClose()
      } else {
        alert(data.message)
      }
    } catch (error) {
      alert('Error al guardar empleado')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 50 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 50 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8 border border-gray-100"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {employee ? 'Editar Empleado' : 'Nuevo Empleado'}
                  </h2>
                  <p className="text-sm text-gray-500">
                    {employee ? 'Actualizar información del empleado' : 'Agregar un nuevo empleado al sistema'}
                  </p>
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </motion.button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                    <Hash className="w-4 h-4 mr-2 text-blue-500" />
                    ID del Empleado *
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.02 }}
                    type="text"
                    name="employee_id"
                    value={formData.employee_id}
                    onChange={handleChange}
                    disabled={!!employee}
                    required
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 transition-all duration-200 shadow-sm"
                    placeholder="Ej: 12345"
                  />
                </div>

                <div className="space-y-2">
                  <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                    <User className="w-4 h-4 mr-2 text-green-500" />
                    Nombre Completo *
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.02 }}
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
                    placeholder="Ej: Juan Pérez"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                    <Building2 className="w-4 h-4 mr-2 text-purple-500" />
                    Departamento
                  </label>
                  <motion.select
                    whileFocus={{ scale: 1.02 }}
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
                  >
                    <option value="General">General</option>
                    <option value="Administración">Administración</option>
                    <option value="Ventas">Ventas</option>
                    <option value="Producción">Producción</option>
                    <option value="Reacondicionamiento">Reacondicionamiento</option>
                    <option value="IT">IT</option>
                    <option value="RRHH">RRHH</option>
                  </motion.select>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                    <Clock className="w-4 h-4 mr-2 text-orange-500" />
                    Horario de Trabajo
                  </label>
                  <motion.select
                    whileFocus={{ scale: 1.02 }}
                    name="schedule"
                    value={formData.schedule}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
                  >
                    <option value="Normal">Normal (2 marcaciones)</option>
                    <option value="Reacondicionamiento">Reacondicionamiento (6 marcaciones)</option>
                  </motion.select>
                  {formData.schedule === 'Reacondicionamiento' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-2 p-3 bg-orange-50 border border-orange-200 rounded-lg"
                    >
                      <p className="text-xs text-orange-700 font-medium">Horario Reacondicionamiento:</p>
                      <p className="text-xs text-orange-600 mt-1">
                        7:00 • 9:30 • 9:50 • 12:40 • 13:40 • 17:00/16:00
                      </p>
                    </motion.div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                    <Phone className="w-4 h-4 mr-2 text-emerald-500" />
                    Teléfono
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.02 }}
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
                    placeholder="Ej: +57 300 123 4567"
                  />
                </div>

                <div className="space-y-2">
                  <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                    <Mail className="w-4 h-4 mr-2 text-red-500" />
                    Email
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.02 }}
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
                    placeholder="Ej: juan@empresa.com"
                  />
                </div>
              </div>

              <div className="flex space-x-4 pt-6 border-t border-gray-100">
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50"
                >
                  <Save className="w-5 h-5" />
                  <span>{loading ? 'Guardando...' : 'Guardar Empleado'}</span>
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  type="button"
                  onClick={onClose}
                  className="px-6 py-3 border-2 border-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 hover:border-gray-300 transition-all duration-200"
                >
                  Cancelar
                </motion.button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default EmployeeModal