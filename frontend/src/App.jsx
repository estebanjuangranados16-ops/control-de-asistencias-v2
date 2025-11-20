import { Routes, Route } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import Reports from './pages/Reports'
import Schedules from './pages/Schedules'
import Layout from './components/Layout'

function App() {
  return (
    <Layout>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Dashboard />
            </motion.div>
          } />
          <Route path="/employees" element={
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Employees />
            </motion.div>
          } />
          <Route path="/reports" element={
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
            >
              <Reports />
            </motion.div>
          } />
          <Route path="/schedules" element={
            <motion.div
              initial={{ opacity: 0, rotateY: 10 }}
              animate={{ opacity: 1, rotateY: 0 }}
              exit={{ opacity: 0, rotateY: -10 }}
              transition={{ duration: 0.3 }}
            >
              <Schedules />
            </motion.div>
          } />
        </Routes>
      </AnimatePresence>
    </Layout>
  )
}

export default App