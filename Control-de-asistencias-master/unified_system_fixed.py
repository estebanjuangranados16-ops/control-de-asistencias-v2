from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import requests
from requests.auth import HTTPDigestAuth
import sqlite3
import json
import threading
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'hikvision_attendance_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

class UnifiedAttendanceSystem:
    def __init__(self, device_ip, username, password, db_path="attendance.db"):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.db_path = db_path
        
        # Configurar conexión
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(username, password)
        self.base_url = f"http://{device_ip}/ISAPI"
        
        # Estado del sistema
        self.monitoring = False
        self.connected = False
        
        # Inicializar base de datos
        self.init_database()
        
    def init_database(self):
        """Inicializa la base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                employee_id TEXT UNIQUE,
                name TEXT,
                department TEXT,
                phone TEXT DEFAULT "",
                email TEXT DEFAULT "",
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_to_device BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabla de registros de asistencia
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
        
        # Insertar empleado admin si no existe
        cursor.execute('''
            INSERT OR IGNORE INTO employees (employee_id, name, department) 
            VALUES ('1', 'admin', 'Administración')
        ''')
        
        conn.commit()
        conn.close()
        
    def test_connection(self):
        """Probar conexión con el dispositivo"""
        try:
            response = self.session.get(f"{self.base_url}/System/deviceInfo", timeout=5)
            self.connected = response.status_code == 200
            return self.connected
        except:
            self.connected = False
            return False
    
    def add_employee(self, employee_id, name, department="General", phone="", email=""):
        """Agregar empleado al sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO employees (employee_id, name, department, phone, email) 
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, name, department, phone, email))
            conn.commit()
            conn.close()
            
            # Emitir evento en tiempo real
            socketio.emit('employee_added', {
                'employee_id': employee_id,
                'name': name,
                'department': department
            })
            
            return True, f"Empleado {name} agregado exitosamente"
            
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
            SELECT employee_id, name, department, phone, email, active, synced_to_device, created_at
            FROM employees ORDER BY name
        ''')
        
        employees = cursor.fetchall()
        conn.close()
        
        return [{
            'employee_id': emp[0],
            'name': emp[1],
            'department': emp[2] or 'General',
            'phone': emp[3] or '',
            'email': emp[4] or '',
            'active': emp[5],
            'synced': emp[6],
            'created_at': emp[7]
        } for emp in employees]
    
    def record_attendance(self, employee_id, timestamp, reader_no=1, verify_method="huella"):
        """Registrar asistencia"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar empleado
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                print(f"Empleado {employee_id} no encontrado en la base de datos")
                conn.close()
                return False
            
            # Determinar tipo de evento
            event_type = self.determine_event_type(employee_id)
            
            # Registrar
            cursor.execute('''
                INSERT INTO attendance_records 
                (employee_id, event_type, timestamp, reader_no, verify_method, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, event_type, timestamp, reader_no, verify_method, "autorizado"))
            
            conn.commit()
            conn.close()
            
            print(f"Registro guardado: {employee[0]} - {event_type} - {timestamp}")
            
            # Emitir evento en tiempo real
            socketio.emit('attendance_record', {
                'employee_id': employee_id,
                'name': employee[0],
                'event_type': event_type,
                'timestamp': timestamp,
                'verify_method': verify_method
            })
            
            return True
            
        except Exception as e:
            print(f"Error al registrar asistencia: {e}")
            return False
    
    def determine_event_type(self, employee_id):
        """Determinar si es entrada o salida"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT event_type FROM attendance_records 
            WHERE employee_id = ? AND date(timestamp) = ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (employee_id, today))
        
        last_record = cursor.fetchone()
        conn.close()
        
        if not last_record or last_record[0] == 'salida':
            return 'entrada'
        else:
            return 'salida'
    
    def get_dashboard_data(self):
        """Obtener datos para el dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Registros recientes (24 horas)
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE datetime(timestamp) >= datetime('now', '-1 day')")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM attendance_records WHERE datetime(timestamp) >= datetime('now', '-1 day')")
        unique_employees = cursor.fetchone()[0]
        
        # Empleados dentro/fuera (basado en último registro)
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
        
        # Registros recientes
        cursor.execute('''
            SELECT e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE datetime(ar.timestamp) >= datetime('now', '-1 day')
            ORDER BY ar.timestamp DESC LIMIT 10
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
        """Iniciar monitoreo en hilo separado"""
        if not self.monitoring:
            self.monitoring = True
            monitor_thread = threading.Thread(target=self._monitor_events, daemon=True)
            monitor_thread.start()
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.monitoring = False
    
    def _monitor_events(self):
        """Monitorear eventos del dispositivo con reconexión automática"""
        url = f"http://{self.device_ip}/ISAPI/Event/notification/alertStream"
        consecutive_errors = 0
        last_success = time.time()
        
        while self.monitoring:
            try:
                # Verificar conexión cada 60 segundos o después de errores
                if time.time() - last_success > 60 or consecutive_errors > 0:
                    if not self.test_connection():
                        consecutive_errors += 1
                        wait_time = min(30, consecutive_errors * 5)
                        print(f"⚠️ Reconectando en {wait_time}s... (intento {consecutive_errors})")
                        time.sleep(wait_time)
                        continue
                    else:
                        if consecutive_errors > 0:
                            print("✅ Conexión restaurada")
                            socketio.emit('connection_restored', {'connected': True})
                        consecutive_errors = 0
                        last_success = time.time()
                
                response = self.session.get(url, stream=True, timeout=30)
                
                if response.status_code == 200:
                    self.connected = True
                    consecutive_errors = 0
                    
                    current_json = ""
                    collecting = False
                    brace_count = 0
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if not self.monitoring:
                            break
                            
                        if line:
                            try:
                                line_str = line.strip()
                                
                                if '{' in line_str and not collecting:
                                    collecting = True
                                    current_json = ""
                                    brace_count = 0
                                
                                if collecting:
                                    current_json += line_str
                                    brace_count += line_str.count('{') - line_str.count('}')
                                    
                                    if brace_count == 0 and current_json.strip():
                                        try:
                                            event = json.loads(current_json)
                                            self._process_event(event)
                                            last_success = time.time()
                                        except json.JSONDecodeError:
                                            pass
                                        collecting = False
                                        current_json = ""
                                        
                            except Exception:
                                continue
                                
                else:
                    consecutive_errors += 1
                    self.connected = False
                    if response.status_code not in [401, 404]:
                        print(f"❌ Error HTTP: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                consecutive_errors += 1
                self.connected = False
                if "timeout" in str(e).lower() or "connection" in str(e).lower():
                    print(f"⚠️ Error de conexión, reintentando...")
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
                    print(f"✅ Acceso autorizado: {employee_id}")
                    success = self.record_attendance(employee_id, timestamp, reader_no, verify_method)
                    if success:
                        print(f"Registro guardado exitosamente")
                        # Emitir actualización del dashboard
                        socketio.emit('dashboard_update', self.get_dashboard_data())
                    else:
                        print(f"Error al guardar registro")
                        
            elif sub_type == 39:  # Acceso denegado
                employee_id = acs_event.get('employeeNoString', 'Desconocido')
                timestamp = event.get('dateTime', datetime.now().isoformat())
                verify_method = self._decode_verify_method(acs_event.get('currentVerifyMode', 'unknown'))
                
                print(f"❌ Acceso DENEGADO: {employee_id}")
                
                # Emitir evento de acceso denegado
                socketio.emit('access_denied', {
                    'employee_id': employee_id,
                    'timestamp': timestamp,
                    'verify_method': verify_method,
                    'message': f'Acceso denegado para ID: {employee_id}'
                })
    
    def sync_employees_from_device(self):
        """Sincronizar empleados desde el dispositivo Hikvision"""
        try:
            # Buscar usuarios en el dispositivo
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
                            # Actualizar o insertar empleado
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
    
    def _decode_verify_method(self, mode):
        """Decodificar método de verificación"""
        if 'Fp' in str(mode) or 'finger' in str(mode).lower():
            return 'huella'
        elif 'card' in str(mode).lower():
            return 'tarjeta'
        elif 'face' in str(mode).lower():
            return 'facial'
        else:
            return 'desconocido'

# Instancia global del sistema
system = UnifiedAttendanceSystem("172.10.0.66", "admin", "PC2024*+")

# Eventos de WebSocket
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado al WebSocket')
    emit('status', {'connected': system.connected, 'monitoring': system.monitoring})

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado del WebSocket')

# Rutas web
@app.route('/')
def dashboard():
    return render_template('unified_dashboard.html')

@app.route('/employees')
def employees_page():
    return render_template('employees.html')

@app.route('/api/dashboard')
def api_dashboard():
    return jsonify(system.get_dashboard_data())

@app.route('/api/employees')
def api_employees():
    return jsonify(system.get_employees())

@app.route('/api/add_employee', methods=['POST'])
def api_add_employee():
    data = request.json
    success, message = system.add_employee(
        data['employee_id'],
        data['name'],
        data.get('department', 'General'),
        data.get('phone', ''),
        data.get('email', '')
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/start_monitoring', methods=['POST'])
def api_start_monitoring():
    system.start_monitoring()
    return jsonify({'success': True, 'message': 'Monitoreo iniciado'})

@app.route('/api/stop_monitoring', methods=['POST'])
def api_stop_monitoring():
    system.stop_monitoring()
    return jsonify({'success': True, 'message': 'Monitoreo detenido'})

@app.route('/api/sync_employees', methods=['POST'])
def api_sync_employees():
    success, message = system.sync_employees_from_device()
    return jsonify({'success': success, 'message': message})

@app.route('/api/test_connection', methods=['POST'])
def api_test_connection():
    connected = system.test_connection()
    return jsonify({'connected': connected})

if __name__ == '__main__':
    # Iniciar monitoreo automáticamente
    system.start_monitoring()
    
    # Ejecutar aplicación web
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)