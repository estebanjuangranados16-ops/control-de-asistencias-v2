# Sistema de Control de Asistencia Hikvision v2.0

Sistema completo y unificado para monitorear y gestionar la asistencia de empleados usando dispositivos Hikvision con lector de huella dactilar.

## 🚀 Características Principales

- **Monitoreo en tiempo real** con WebSockets
- **Sistema unificado** con interfaz web moderna
- **Base de datos SQLite** optimizada
- **Sincronización bidireccional** con dispositivos
- **Dashboard interactivo** con actualizaciones automáticas
- **Gestión completa de empleados**
- **Reconexión automática** ante fallos de red
- **API REST** para integraciones
- **Frontend React** (opcional)
- **Soporte para múltiples métodos** de verificación

## 📋 Archivos del Sistema

### Scripts Principales
- `unified_system.py` - **Sistema unificado principal** (RECOMENDADO)
- `system_optimized.py` - Sistema optimizado con mejoras de rendimiento
- `cloud_system.py` - Versión con integración Firebase
- `hikvision_isapi.py` - Script básico de conexión y monitoreo
- `attendance_system.py` - Sistema completo con base de datos
- `web_dashboard.py` - Dashboard web con Flask

### Frontend Moderno
- `frontend/` - Aplicación React con Vite
- `templates/` - Plantillas HTML para Flask

### Archivos de Configuración
- `requirements_unified.txt` - Dependencias para sistema unificado
- `requirements_cloud.txt` - Dependencias para versión cloud
- `requirements_full.txt` - Dependencias completas
- `.env.example` - Ejemplo de configuración de entorno

## 🛠️ Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements_full.txt
```

2. **Configurar dispositivo:**
   - Editar IP, usuario y contraseña en los scripts
   - Asegurar que el dispositivo tenga ISAPI habilitado

## 📱 Uso del Sistema

### 🌟 Sistema Unificado (RECOMENDADO)
```bash
python unified_system.py
```
**Características:**
- Dashboard web completo en http://localhost:5000
- Monitoreo en tiempo real con WebSockets
- Gestión de empleados integrada
- Sincronización automática con dispositivo
- Reconexión automática ante fallos
- API REST completa

### 🚀 Frontend React (Opcional)
```bash
cd frontend
npm install
npm run dev
```
Interfaz moderna en http://localhost:5173

### ☁️ Versión Cloud
```bash
python cloud_system.py
```
- Integración con Firebase
- Sincronización en la nube
- Acceso remoto

### 🔧 Herramientas de Diagnóstico
```bash
python test_connection.py    # Probar conexión
python check_status.py       # Ver estado actual
python status_today.py       # Resumen del día
```

## 🗄️ Base de Datos

El sistema crea automáticamente una base de datos SQLite (`attendance.db`) con:

### Tabla `employees`
- `employee_id` - ID único del empleado
- `name` - Nombre del empleado
- `department` - Departamento
- `active` - Estado activo/inactivo

### Tabla `attendance_records`
- `employee_id` - ID del empleado
- `event_type` - entrada/salida
- `timestamp` - Fecha y hora
- `reader_no` - Número del lector
- `verify_method` - Método de verificación
- `status` - Estado del evento

## 🔧 Configuración del Dispositivo

### Credenciales por defecto:
```python
DEVICE_IP = "172.10.0.66"
USERNAME = "admin"
PASSWORD = "PC2024*+"
```

### Eventos detectados:
- **subEventType 38:** Acceso autorizado ✅
- **subEventType 39:** Acceso denegado ❌
- **subEventType 21/22:** Puerta abierta/cerrada 🚪

## 📊 Tipos de Reportes

### Reporte Diario
Muestra todos los registros del día con:
- Hora exacta
- Nombre del empleado
- Tipo de evento (entrada/salida)
- Método de verificación

### Estado en Tiempo Real
- Empleados actualmente dentro del edificio
- Empleados fuera
- Último registro de cada empleado

## 🚨 Solución de Problemas

### Error de conexión:
1. Verificar IP del dispositivo
2. Comprobar credenciales
3. Asegurar que ISAPI esté habilitado
4. Verificar conectividad de red

### No se detectan eventos:
1. Verificar que las huellas estén registradas
2. Comprobar que el dispositivo esté enviando eventos
3. Revisar logs del script para errores

### Dashboard no carga:
1. Verificar que Flask esté instalado
2. Comprobar que el puerto 5000 esté libre
3. Asegurar que la base de datos exista

## 🔄 Flujo de Trabajo

1. **Empleado pone huella** → Dispositivo Hikvision
2. **Evento ISAPI** → Script Python
3. **Procesamiento** → Determina entrada/salida
4. **Almacenamiento** → Base de datos SQLite
5. **Visualización** → Dashboard web

## 📈 Nuevas Características v2.0

- [x] **Sistema unificado** con WebSockets
- [x] **Frontend React** moderno
- [x] **Reconexión automática** ante fallos
- [x] **Sincronización bidireccional** con dispositivos
- [x] **API REST** completa
- [x] **Integración Firebase** para la nube
- [x] **Dashboard interactivo** en tiempo real
- [x] **Gestión avanzada** de empleados

## 🚀 Próximas Mejoras

- [ ] Notificaciones push en tiempo real
- [ ] Exportar reportes a Excel/PDF
- [ ] Integración con sistemas de nómina
- [ ] App móvil nativa
- [ ] Reconocimiento facial avanzado
- [ ] Alertas de horarios personalizadas
- [ ] Múltiples dispositivos
- [ ] Reportes analíticos avanzados

## 🤝 Soporte

Para soporte técnico o mejoras, contactar al desarrollador del sistema.

---
**Desarrollado para control de asistencia empresarial** 🏢