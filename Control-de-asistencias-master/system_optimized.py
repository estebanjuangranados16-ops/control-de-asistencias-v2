from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
from requests.auth import HTTPDigestAuth
import sqlite3
import json
import threading
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'hikvision_attendance_2024'
CORS(app, origins=["http://localhost:3001", "http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="*")

class OptimizedAttendanceSystem:
    def __init__(self, device_ip, username, password, db_path="attendance.db"):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.db_path = db_path
        
        # Configurar conexión con timeouts más cortos
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(username, password)
        self.session.timeout = 10
        self.base_url = f"http://{device_ip}/ISAPI"
        
        # Estado del sistema
        self.monitoring = False
        self.connected = False
        self.last_event_time = time.time()
        
        # Inicializar base de datos
        self.init_database()
        
    def init_database(self):
        """Inicializa la base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                employee_id TEXT UNIQUE,
                name TEXT,
                department TEXT,
                schedule TEXT DEFAULT "estandar",
                phone TEXT DEFAULT "",
                email TEXT DEFAULT "",
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_to_device BOOLEAN DEFAULT 0
            )
        ''')
        
        # Agregar columna schedule si no existe
        try:
            cursor.execute('ALTER TABLE employees ADD COLUMN schedule TEXT DEFAULT "estandar"')
        except:
            pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                event_type TEXT,
                timestamp TIMESTAMP,
                reader_no INTEGER,
                verify_method TEXT,
                status TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO employees (employee_id, name, department) 
            VALUES ('1', 'admin', 'Administración')
        ''')
        
        conn.commit()
        conn.close()
        
    def test_connection(self):
        """Probar conexión rápida"""
        try:
            # Probar múltiples endpoints
            endpoints = [
                f"{self.base_url}/System/deviceInfo",
                f"http://{self.device_ip}/ISAPI/System/status",
                f"http://{self.device_ip}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=2)
                    if response.status_code in [200, 401]:  # 401 también indica que el dispositivo responde
                        self.connected = True
                        return True
                except:
                    continue
                    
            self.connected = False
            return False
        except:
            self.connected = False
            return False
    
    def record_attendance(self, employee_id, timestamp, reader_no=1, verify_method="huella"):
        """Registrar asistencia con hora local corregida y prevención de duplicados"""
        try:
            from datetime import datetime, timedelta
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name, department, schedule FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                print(f"Empleado {employee_id} no encontrado")
                conn.close()
                return False
            
            # Usar hora local del sistema
            local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Verificar si hay un registro muy reciente (menos de 10 segundos)
            cursor.execute('''
                SELECT timestamp FROM attendance_records 
                WHERE employee_id = ? AND datetime(timestamp) > datetime('now', '-10 seconds')
                ORDER BY timestamp DESC LIMIT 1
            ''', (employee_id,))
            
            recent_record = cursor.fetchone()
            if recent_record:
                print(f"DUPLICADO EVITADO: {employee[0]} - Registro muy reciente ({recent_record[0]})")
                conn.close()
                return False
            
            event_type = self.determine_event_type(employee_id)
            
            cursor.execute('''
                INSERT INTO attendance_records 
                (employee_id, event_type, timestamp, reader_no, verify_method, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, event_type, local_timestamp, reader_no, verify_method, "autorizado"))
            
            conn.commit()
            conn.close()
            
            # Mensaje detallado
            dept = employee[1] or 'General'
            schedule = employee[2] or 'estandar'
            
            if dept == 'Reacondicionamiento' or schedule == 'reacondicionamiento':
                print(f"✅ REACONDICIONAMIENTO: {employee[0]} - {event_type.upper()} - {local_timestamp}")
            else:
                print(f"✅ REGISTRO: {employee[0]} - {event_type.upper()} - {local_timestamp}")
            
            # Emitir evento inmediatamente con más detalles
            socketio.emit('attendance_record', {
                'employee_id': employee_id,
                'name': employee[0],
                'event_type': event_type,
                'timestamp': local_timestamp,
                'verify_method': verify_method,
                'department': dept,
                'schedule': schedule,
                'real_time': True
            })
            
            # Emitir actualización completa del dashboard después de un breve delay
            import threading
            def delayed_update():
                time.sleep(0.5)
                socketio.emit('dashboard_update', self.get_dashboard_data())
            
            threading.Thread(target=delayed_update, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error al registrar: {e}")
            return False
    
    def determine_event_type(self, employee_id):
        """Determinar entrada o salida basado en horario del empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener horario del empleado
        cursor.execute('SELECT schedule, department FROM employees WHERE employee_id = ?', (employee_id,))
        employee_info = cursor.fetchone()
        schedule = employee_info[0] if employee_info else 'estandar'
        department = employee_info[1] if employee_info else 'General'
        
        # Obtener último registro del día
        cursor.execute('''
            SELECT event_type, time(timestamp) FROM attendance_records 
            WHERE employee_id = ? AND date(timestamp) = date('now')
            ORDER BY timestamp DESC LIMIT 1
        ''', (employee_id,))
        
        last_record = cursor.fetchone()
        
        # Debug: mostrar información del empleado
        print(f"DEBUG - Empleado {employee_id}: Depto={department}, Horario={schedule}")
        if last_record:
            print(f"DEBUG - Último evento: {last_record[0]} a las {last_record[1]}")
        else:
            print(f"DEBUG - Sin registros previos hoy")
        
        conn.close()
        
        # Si no hay registros, es entrada
        if not last_record:
            print(f"DEBUG - Resultado: ENTRADA (primer registro del día)")
            return 'entrada'
        
        # Lógica especial para Reacondicionamiento
        if schedule == 'reacondicionamiento' or department == 'Reacondicionamiento':
            result = self._determine_reacondicionamiento_event(last_record)
            print(f"DEBUG - Resultado Reacondicionamiento: {result.upper()}")
            return result
        
        # Lógica estándar: alternar entrada/salida
        result = 'entrada' if last_record[0] == 'salida' else 'salida'
        print(f"DEBUG - Resultado estándar: {result.upper()} (alternando desde {last_record[0]})")
        return result
    
    def _determine_reacondicionamiento_event(self, last_record):
        """Lógica específica para horario de Reacondicionamiento"""
        from datetime import datetime, time
        
        current_time = datetime.now().time()
        last_event, last_time_str = last_record
        
        print(f"DEBUG Reacondicionamiento - Hora actual: {current_time}, Último evento: {last_event}")
        
        # Horarios de Reacondicionamiento:
        # 1. 07:00 - Entrada principal
        # 2. 09:30 - Salida (descanso)
        # 3. 09:50 - Entrada (regreso descanso)
        # 4. 12:40 - Salida (almuerzo)
        # 5. 13:40 - Entrada (regreso almuerzo)
        # 6. 17:00 - Salida final (16:00 Viernes)
        
        # Obtener día de la semana (0=lunes, 4=viernes)
        current_day = datetime.now().weekday()
        
        # Simplificar la lógica: siempre alternar pero con validaciones de horario
        next_event = 'entrada' if last_event == 'salida' else 'salida'
        
        # Validaciones especiales por horario
        if time(6, 30) <= current_time <= time(8, 0):
            # Horario de entrada matutina - debe ser entrada
            if last_event != 'entrada':
                next_event = 'entrada'
                
        elif time(9, 15) <= current_time <= time(10, 15):
            # Horario de descanso - alternar normalmente
            pass
            
        elif time(12, 20) <= current_time <= time(14, 0):
            # Horario de almuerzo - alternar normalmente
            pass
            
        elif time(15, 45) <= current_time <= time(18, 0):
            # Horario de salida final
            if current_day == 4 and current_time >= time(15, 45):  # Viernes
                if last_event != 'salida':
                    next_event = 'salida'
            elif current_day < 4 and current_time >= time(16, 45):  # Lunes-Jueves
                if last_event != 'salida':
                    next_event = 'salida'
        
        print(f"DEBUG Reacondicionamiento - Evento determinado: {next_event}")
        return next_event
    
    def get_dashboard_data(self):
        """Obtener datos del dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Registros de las últimas 24 horas
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE datetime(timestamp) >= datetime('now', '-1 day')")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM attendance_records WHERE datetime(timestamp) >= datetime('now', '-1 day')")
        unique_employees = cursor.fetchone()[0]
        
        # Estado de empleados
        cursor.execute('''
            SELECT e.name, e.employee_id, ar.event_type, ar.timestamp
            FROM employees e
            LEFT JOIN (
                SELECT employee_id, event_type, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY timestamp DESC) as rn
                FROM attendance_records
                WHERE datetime(timestamp) >= datetime('now', '-1 day')
            ) ar ON e.employee_id = ar.employee_id AND ar.rn = 1
            WHERE e.active = 1
        ''')
        
        employees_status = cursor.fetchall()
        
        # Registros recientes - últimos 50 registros sin filtro de tiempo
        cursor.execute('''
            SELECT e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            ORDER BY ar.timestamp DESC LIMIT 50
        ''')
        
        recent_records = cursor.fetchall()
        conn.close()
        
        inside = []
        outside = []
        
        for emp in employees_status:
            name, emp_id, last_event, timestamp = emp
            if last_event == 'entrada':
                inside.append({'name': name, 'id': emp_id, 'time': timestamp})
            else:
                outside.append({'name': name, 'id': emp_id, 'time': timestamp})
        
        return {
            'total_records': total_records,
            'unique_employees': unique_employees,
            'employees_inside': inside,
            'employees_outside': outside,
            'recent_records': recent_records,
            'connected': self.connected,
            'monitoring': self.monitoring
        }
    
    def start_monitoring(self):
        """Iniciar monitoreo"""
        if not self.monitoring:
            self.monitoring = True
            monitor_thread = threading.Thread(target=self._monitor_events, daemon=True)
            monitor_thread.start()
            print("Monitoreo iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring = False
        print("Monitoreo detenido")
    
    def _monitor_events(self):
        """Monitoreo optimizado con mejor manejo de errores"""
        url = f"http://{self.device_ip}/ISAPI/Event/notification/alertStream"
        retry_count = 0
        max_retries = 5
        
        while self.monitoring:
            try:
                # Verificar conexión cada 30 segundos
                if time.time() - self.last_event_time > 30:
                    if not self.test_connection():
                        retry_count += 1
                        if retry_count <= max_retries:
                            wait_time = min(30, retry_count * 5)  # Reducir tiempo de espera
                            print(f"Reintentando conexion en {wait_time}s (intento {retry_count}/{max_retries})")
                            socketio.emit('connection_status', {'connected': False, 'retrying': True, 'attempt': retry_count})
                            time.sleep(wait_time)
                            continue
                        else:
                            print("Maximo de reintentos alcanzado. Pausando monitoreo...")
                            socketio.emit('connection_status', {'connected': False, 'retrying': False})
                            time.sleep(60)  # Pausa más corta
                            retry_count = 0
                            continue
                    else:
                        if retry_count > 0:
                            print("Conexion restaurada")
                            socketio.emit('connection_restored', {'connected': True})
                        retry_count = 0
                        self.last_event_time = time.time()
                
                # Intentar conectar al stream
                response = self.session.get(url, stream=True, timeout=60)
                
                if response.status_code == 200:
                    self.connected = True
                    retry_count = 0
                    print("Stream de eventos activo")
                    
                    buffer = ""
                    for chunk in response.iter_content(chunk_size=1024):
                        if not self.monitoring:
                            break
                            
                        if chunk:
                            try:
                                chunk_str = chunk.decode('utf-8', errors='ignore')
                                buffer += chunk_str
                            except:
                                continue
                            
                            # Procesar eventos JSON completos
                            while '{' in buffer and '}' in buffer:
                                start = buffer.find('{')
                                if start == -1:
                                    break
                                    
                                brace_count = 0
                                end = start
                                
                                for i in range(start, len(buffer)):
                                    if buffer[i] == '{':
                                        brace_count += 1
                                    elif buffer[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            end = i
                                            break
                                
                                if brace_count == 0:
                                    json_str = buffer[start:end+1]
                                    buffer = buffer[end+1:]
                                    
                                    try:
                                        event = json.loads(json_str)
                                        self._process_event(event)
                                        self.last_event_time = time.time()
                                    except json.JSONDecodeError:
                                        pass
                                else:
                                    break
                else:
                    self.connected = False
                    retry_count += 1
                    print(f"Error HTTP {response.status_code}")
                    time.sleep(10)
                    
            except Exception as e:
                self.connected = False
                retry_count += 1
                if "timeout" in str(e).lower():
                    print("Timeout de conexion")
                else:
                    print(f"Error: {str(e)[:50]}...")
                time.sleep(5)
    
    def _process_event(self, event):
        """Procesar eventos del dispositivo"""
        if 'AccessControllerEvent' in event:
            acs_event = event['AccessControllerEvent']
            sub_type = acs_event.get('subEventType')
            
            if sub_type == 38:  # Acceso autorizado
                employee_id = acs_event.get('employeeNoString')
                timestamp = event.get('dateTime', datetime.now().isoformat())
                reader_no = acs_event.get('cardReaderNo', 1)
                verify_method = self._decode_verify_method(acs_event.get('currentVerifyMode', 'unknown'))
                
                if employee_id:
                    self.record_attendance(employee_id, timestamp, reader_no, verify_method)
                        
            elif sub_type == 39:  # Acceso denegado
                employee_id = acs_event.get('employeeNoString', 'Desconocido')
                timestamp = event.get('dateTime', datetime.now().isoformat())
                verify_method = self._decode_verify_method(acs_event.get('currentVerifyMode', 'unknown'))
                
                print(f"ACCESO DENEGADO: {employee_id}")
                
                socketio.emit('access_denied', {
                    'employee_id': employee_id,
                    'timestamp': timestamp,
                    'verify_method': verify_method,
                    'message': f'Acceso denegado para ID: {employee_id}'
                })
    
    def add_employee(self, employee_id, name, department="General", schedule="estandar", phone="", email=""):
        """Agregar empleado al sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO employees (employee_id, name, department, schedule, phone, email) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, name, department, schedule, phone, email))
            conn.commit()
            conn.close()
            
            socketio.emit('employee_added', {
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'schedule': schedule
            })
            
            return True, f"Empleado {name} agregado exitosamente al área de {department}"
            
        except sqlite3.IntegrityError:
            conn.close()
            return False, f"El empleado con ID {employee_id} ya existe"
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    
    def get_employees(self):
        """Obtener lista de empleados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT employee_id, name, department, schedule, phone, email, active, synced_to_device, created_at
            FROM employees ORDER BY name
        ''')
        
        employees = cursor.fetchall()
        conn.close()
        
        # Mapear schedule del backend al frontend
        schedule_mapping = {
            'estandar': 'Normal',
            'reacondicionamiento': 'Reacondicionamiento'
        }
        
        return [{
            'employee_id': emp[0],
            'name': emp[1],
            'department': emp[2] or 'General',
            'schedule': schedule_mapping.get(emp[3] or 'estandar', 'Normal'),
            'phone': emp[4] or '',
            'email': emp[5] or '',
            'active': emp[6],
            'synced': emp[7],
            'created_at': emp[8]
        } for emp in employees]
    
    def update_employee(self, employee_id, name, department, schedule="estandar", phone="", email="", active=True):
        """Actualizar empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE employees 
                SET name=?, department=?, schedule=?, phone=?, email=?, active=?
                WHERE employee_id=?
            ''', (name, department, schedule, phone, email, active, employee_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True, f"Empleado {name} actualizado exitosamente"
            else:
                conn.close()
                return False, "Empleado no encontrado"
                
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    
    def delete_employee(self, employee_id):
        """Eliminar empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obtener nombre antes de eliminar
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                conn.close()
                return False, "Empleado no encontrado"
            
            # Eliminar empleado
            cursor.execute('DELETE FROM employees WHERE employee_id = ?', (employee_id,))
            conn.commit()
            conn.close()
            
            return True, f"Empleado {employee[0]} eliminado exitosamente"
            
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    
    def toggle_employee_status(self, employee_id):
        """Cambiar estado activo/inactivo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT name, active FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                conn.close()
                return False, "Empleado no encontrado"
            
            new_status = not employee[1]
            cursor.execute('UPDATE employees SET active = ? WHERE employee_id = ?', (new_status, employee_id))
            conn.commit()
            conn.close()
            
            status_text = "activado" if new_status else "desactivado"
            return True, f"Empleado {employee[0]} {status_text}"
            
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    
    def sync_employees_from_device(self):
        """Sincronizar empleados desde el dispositivo Hikvision"""
        try:
            search_url = f"{self.base_url}/AccessControl/UserInfo/Search"
            search_data = {
                "UserInfoSearchCond": {
                    "searchID": "1",
                    "maxResults": 100,
                    "searchResultPosition": 0
                }
            }
            
            response = self.session.post(search_url, json=search_data, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    users = data.get("UserInfoSearch", {}).get("UserInfo", [])
                    
                    if not users:
                        return False, "No se encontraron usuarios en el dispositivo"
                    
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    synced_count = 0
                    for user in users:
                        emp_id = user.get("employeeNo")
                        name = user.get("name", f"Usuario_{emp_id}")
                        
                        if emp_id:
                            cursor.execute('''
                                INSERT OR REPLACE INTO employees 
                                (employee_id, name, department, synced_to_device) 
                                VALUES (?, ?, ?, 1)
                            ''', (emp_id, name, "Sincronizado"))
                            synced_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    return True, f"Sincronizados {synced_count} empleados desde el dispositivo"
                    
                except json.JSONDecodeError:
                    return False, "Error al procesar respuesta del dispositivo"
            else:
                return False, f"Error HTTP: {response.status_code}"
                
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"
    
    def generate_report(self, start_date, end_date, employee_id=None, report_type='daily'):
        """Generar reporte de asistencia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query base
        base_query = '''
            SELECT 
                e.name as employee_name,
                e.employee_id,
                DATE(ar.timestamp) as date,
                MIN(CASE WHEN ar.event_type = 'entrada' THEN TIME(ar.timestamp) END) as entry_time,
                MAX(CASE WHEN ar.event_type = 'salida' THEN TIME(ar.timestamp) END) as exit_time,
                ar.timestamp
            FROM employees e
            LEFT JOIN attendance_records ar ON e.employee_id = ar.employee_id
            WHERE e.active = 1
        '''
        
        params = []
        
        if start_date and end_date:
            base_query += ' AND DATE(ar.timestamp) BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        if employee_id:
            base_query += ' AND e.employee_id = ?'
            params.append(employee_id)
        
        base_query += ' GROUP BY e.employee_id, DATE(ar.timestamp) ORDER BY ar.timestamp DESC'
        
        cursor.execute(base_query, params)
        raw_data = cursor.fetchall()
        
        # Procesar datos
        records = []
        for row in raw_data:
            if row[5]:  # Si hay timestamp (hay registros)
                entry_time = row[3]
                exit_time = row[4]
                hours_worked = 0
                status = 'incomplete'
                
                if entry_time and exit_time:
                    # Calcular horas trabajadas
                    from datetime import datetime, time
                    entry_dt = datetime.strptime(entry_time, '%H:%M:%S')
                    exit_dt = datetime.strptime(exit_time, '%H:%M:%S')
                    
                    if exit_dt > entry_dt:
                        hours_worked = (exit_dt - entry_dt).seconds / 3600
                        status = 'complete'
                    
                    # Verificar si llegó tarde (después de las 9:00)
                    if entry_dt.time() > time(9, 0):
                        status = 'late'
                
                records.append({
                    'employee_name': row[0],
                    'employee_id': row[1],
                    'date': row[2],
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'hours_worked': round(hours_worked, 2),
                    'status': status
                })
        
        # Estadísticas
        stats = {
            'total_records': len(records),
            'total_employees': len(set(r['employee_id'] for r in records)),
            'avg_hours': sum(r['hours_worked'] for r in records) / len(records) if records else 0,
            'late_arrivals': len([r for r in records if r['status'] == 'late'])
        }
        
        conn.close()
        
        return {
            'records': records,
            'stats': stats,
            'period': f"{start_date} - {end_date}"
        }
    
    def export_report(self, start_date, end_date, employee_id=None, format_type='excel'):
        """Exportar reporte"""
        from flask import Response
        import io
        
        data = self.generate_report(start_date, end_date, employee_id)
        
        if format_type == 'excel':
            # Crear CSV simple (Excel puede abrirlo)
            output = io.StringIO()
            output.write('Empleado,Fecha,Entrada,Salida,Horas,Estado\n')
            
            for record in data['records']:
                output.write(f"{record['employee_name']},{record['date']},{record['entry_time'] or ''},{record['exit_time'] or ''},{record['hours_worked']},{record['status']}\n")
            
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=reporte_asistencia_{start_date}_{end_date}.csv'}
            )
            return response
        
        return {'error': 'Formato no soportado'}
    
    def get_schedules(self):
        """Obtener horarios de trabajo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tabla de horarios si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_schedules (
                id INTEGER PRIMARY KEY,
                employee_id TEXT,
                day_of_week INTEGER,
                start_time TEXT,
                end_time TEXT,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        cursor.execute('''
            SELECT ws.*, e.name 
            FROM work_schedules ws
            JOIN employees e ON ws.employee_id = e.employee_id
            WHERE ws.active = 1
            ORDER BY e.name, ws.day_of_week
        ''')
        
        schedules = cursor.fetchall()
        conn.close()
        
        return [{
            'id': s[0],
            'employee_id': s[1],
            'employee_name': s[6],
            'day_of_week': s[2],
            'start_time': s[3],
            'end_time': s[4],
            'active': s[5]
        } for s in schedules]
    
    def add_schedule(self, data):
        """Agregar horario de trabajo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO work_schedules (employee_id, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?)
            ''', (data['employee_id'], data['day_of_week'], data['start_time'], data['end_time']))
            
            conn.commit()
            conn.close()
            return True, "Horario agregado exitosamente"
            
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    
    def delete_schedule(self, schedule_id):
        """Eliminar horario de trabajo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM work_schedules WHERE id = ?', (schedule_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True, "Horario eliminado exitosamente"
            else:
                conn.close()
                return False, "Horario no encontrado"
                
        except Exception as e:
            conn.close()
            return False, f"Error: {str(e)}"
    

    def _decode_verify_method(self, mode):
        """Decodificar método de verificación"""
        mode_str = str(mode).lower()
        if 'fp' in mode_str or 'finger' in mode_str:
            return 'huella'
        elif 'card' in mode_str:
            return 'tarjeta'
        elif 'face' in mode_str:
            return 'facial'
        else:
            return 'desconocido'

# Instancia global
system = OptimizedAttendanceSystem("172.10.0.66", "admin", "PC2024*+")

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    emit('status', {'connected': system.connected, 'monitoring': system.monitoring})

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

# Rutas web
@app.route('/')
def dashboard():
    return render_template('unified_dashboard.html')

@app.route('/api/dashboard')
def api_dashboard():
    return jsonify(system.get_dashboard_data())

@app.route('/api/employees')
def api_employees():
    return jsonify(system.get_employees())

@app.route('/employees')
def employees_page():
    return render_template('employees.html')

@app.route('/api/employees', methods=['POST'])
def api_add_employee():
    data = request.json
    
    # Mapear el schedule del frontend al backend
    schedule_mapping = {
        'Normal': 'estandar',
        'Reacondicionamiento': 'reacondicionamiento'
    }
    
    schedule = schedule_mapping.get(data.get('schedule', 'Normal'), 'estandar')
    
    success, message = system.add_employee(
        data['employee_id'],
        data['name'],
        data.get('department', 'General'),
        schedule,
        data.get('phone', ''),
        data.get('email', '')
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/sync_employees', methods=['POST'])
def api_sync_employees():
    success, message = system.sync_employees_from_device()
    return jsonify({'success': success, 'message': message})

@app.route('/api/employees/<employee_id>', methods=['PUT'])
def api_update_employee(employee_id):
    data = request.json
    
    # Mapear el schedule del frontend al backend
    schedule_mapping = {
        'Normal': 'estandar',
        'Reacondicionamiento': 'reacondicionamiento'
    }
    
    schedule = schedule_mapping.get(data.get('schedule', 'Normal'), 'estandar')
    
    success, message = system.update_employee(
        employee_id,
        data.get('name'),
        data.get('department'),
        schedule,
        data.get('phone', ''),
        data.get('email', ''),
        data.get('active', True)
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/employees/<employee_id>', methods=['DELETE'])
def api_delete_employee(employee_id):
    success, message = system.delete_employee(employee_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/employees/<employee_id>/toggle', methods=['POST'])
def api_toggle_employee(employee_id):
    success, message = system.toggle_employee_status(employee_id)
    return jsonify({'success': success, 'message': message})

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/schedules')
def schedules_page():
    return render_template('schedules.html')

@app.route('/api/reports')
def api_reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    report_type = request.args.get('report_type', 'daily')
    
    data = system.generate_report(start_date, end_date, employee_id, report_type)
    return jsonify(data)

@app.route('/api/reports/export')
def api_export_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    format_type = request.args.get('format', 'excel')
    
    return system.export_report(start_date, end_date, employee_id, format_type)

@app.route('/api/schedules')
def api_schedules():
    return jsonify(system.get_schedules())

@app.route('/api/schedules', methods=['POST'])
def api_add_schedule():
    data = request.json
    success, message = system.add_schedule(data)
    return jsonify({'success': success, 'message': message})

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def api_delete_schedule(schedule_id):
    success, message = system.delete_schedule(schedule_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/start_monitoring', methods=['POST'])
def api_start_monitoring():
    system.start_monitoring()
    return jsonify({'success': True, 'message': 'Monitoreo iniciado'})

@app.route('/api/stop_monitoring', methods=['POST'])
def api_stop_monitoring():
    system.stop_monitoring()
    return jsonify({'success': True, 'message': 'Monitoreo detenido'})

@app.route('/api/test_connection', methods=['POST'])
def api_test_connection():
    connected = system.test_connection()
    message = "✅ Dispositivo conectado" if connected else "❌ Dispositivo no disponible"
    return jsonify({'connected': connected, 'message': message})

@app.route('/api/schedule_info/<employee_id>')
def api_schedule_info(employee_id):
    """Obtener información detallada del horario de un empleado"""
    from datetime import datetime, time
    
    conn = sqlite3.connect(system.db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, department, schedule FROM employees WHERE employee_id = ?', (employee_id,))
    employee = cursor.fetchone()
    
    if not employee:
        conn.close()
        return jsonify({'error': 'Empleado no encontrado'})
    
    # Obtener últimos registros del día
    cursor.execute('''
        SELECT event_type, time(timestamp) as time_only, timestamp 
        FROM attendance_records 
        WHERE employee_id = ? AND date(timestamp) = date('now')
        ORDER BY timestamp ASC
    ''', (employee_id,))
    
    today_records = cursor.fetchall()
    conn.close()
    
    current_time = datetime.now().time()
    current_day = datetime.now().weekday()  # 0=lunes, 4=viernes
    
    schedule_info = {
        'employee_name': employee[0],
        'department': employee[1],
        'schedule_type': employee[2],
        'current_time': current_time.strftime('%H:%M:%S'),
        'current_day': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][current_day],
        'today_records': [{
            'event_type': r[0],
            'time': r[1],
            'timestamp': r[2]
        } for r in today_records]
    }
    
    # Información específica para Reacondicionamiento
    if employee[1] == 'Reacondicionamiento' or employee[2] == 'reacondicionamiento':
        schedule_info['expected_schedule'] = {
            'entrada_1': '07:00 - Entrada principal',
            'salida_1': '09:30 - Salida a descanso (15-20 min)',
            'entrada_2': '09:50 - Regreso de descanso',
            'salida_2': '12:40 - Salida a almuerzo',
            'entrada_3': '13:40 - Regreso de almuerzo',
            'salida_3': '17:00 - Salida final (16:00 Viernes)'
        }
        
        # Determinar próximo evento esperado
        records_count = len(today_records)
        if records_count == 0:
            schedule_info['next_expected'] = 'Entrada principal (07:00)'
        elif records_count == 1:
            schedule_info['next_expected'] = 'Salida a descanso (09:30)'
        elif records_count == 2:
            schedule_info['next_expected'] = 'Regreso de descanso (09:50)'
        elif records_count == 3:
            schedule_info['next_expected'] = 'Salida a almuerzo (12:40)'
        elif records_count == 4:
            schedule_info['next_expected'] = 'Regreso de almuerzo (13:40)'
        elif records_count == 5:
            final_time = '16:00' if current_day == 4 else '17:00'
            schedule_info['next_expected'] = f'Salida final ({final_time})'
        else:
            schedule_info['next_expected'] = 'Horario completado'
    
    return jsonify(schedule_info)

if __name__ == '__main__':
    print("Sistema de Asistencia Optimizado")
    print("=" * 40)
    print(f"Dispositivo: {system.device_ip}")
    print(f"Dashboard: http://localhost:5000")
    print(f"Empleados: http://localhost:5000/employees")
    print("=" * 40)
    
    # Mostrar empleados de Reacondicionamiento
    conn = sqlite3.connect(system.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT employee_id, name FROM employees WHERE department = "Reacondicionamiento" AND active = 1')
    reacon_employees = cursor.fetchall()
    conn.close()
    
    if reacon_employees:
        print("Empleados de Reacondicionamiento activos:")
        for emp in reacon_employees:
            print(f"  - {emp[1]} (ID: {emp[0]})")
        print("Horario: 07:00, 09:30, 09:50, 12:40, 13:40, 17:00 (16:00 Viernes)")
        print("=" * 40)
    
    # Probar conexión inicial
    if system.test_connection():
        print("Dispositivo conectado - Monitoreo activo")
        system.start_monitoring()
    else:
        print("Dispositivo no disponible - iniciando sin monitoreo")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)