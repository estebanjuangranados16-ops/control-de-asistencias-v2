# Sistema de Control de Asistencia Hikvision

Sistema completo para monitorear y gestionar la asistencia de empleados usando dispositivos Hikvision con lector de huella dactilar.

## 🚀 Características

- **Monitoreo en tiempo real** de eventos de huella dactilar
- **Base de datos SQLite** para almacenar registros
- **Dashboard web** para visualización
- **Detección automática** de entrada/salida
- **Reportes diarios** de asistencia
- **Gestión de empleados**

## 📋 Archivos del Sistema

### Scripts Principales
- `hikvision_isapi.py` - Script básico de conexión y monitoreo
- `attendance_system.py` - Sistema completo con base de datos
- `web_dashboard.py` - Dashboard web con Flask

### Archivos de Configuración
- `requirements_full.txt` - Dependencias necesarias
- `templates/dashboard.html` - Interfaz web

## 🛠️ Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements_full.txt
```

2. **Configurar dispositivo:**
   - Editar IP, usuario y contraseña en los scripts
   - Asegurar que el dispositivo tenga ISAPI habilitado

## 📱 Uso del Sistema

### 1. Sistema Básico de Monitoreo
```bash
python hikvision_isapi.py
```
- Muestra eventos en tiempo real
- Ideal para pruebas y diagnóstico

### 2. Sistema Completo de Asistencia
```bash
python attendance_system.py
```

**Menú principal:**
- **Opción 1:** Monitoreo en tiempo real con base de datos
- **Opción 2:** Agregar nuevos empleados
- **Opción 3:** Ver reportes diarios
- **Opción 4:** Salir

### 3. Dashboard Web
```bash
python web_dashboard.py
```
Luego abrir: http://localhost:5000

**Características del dashboard:**
- Resumen diario en tiempo real
- Lista de empleados dentro/fuera
- Registros recientes
- Auto-actualización cada 30 segundos

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

## 📈 Próximas Mejoras

- [ ] Notificaciones por email
- [ ] Exportar reportes a Excel
- [ ] Integración con sistemas de nómina
- [ ] App móvil
- [ ] Reconocimiento facial
- [ ] Alertas de horarios

## 🤝 Soporte

Para soporte técnico o mejoras, contactar al desarrollador del sistema.

---
**Desarrollado para control de asistencia empresarial** 🏢