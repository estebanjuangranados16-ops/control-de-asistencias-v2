from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
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
        
        # Verificar si la tabla existe y agregar columnas faltantes
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Crear tabla de empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                employee_id TEXT UNIQUE,
                name TEXT,
                department TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Agregar columnas faltantes si no existen
        if 'phone' not in columns:
            cursor.execute('ALTER TABLE employees ADD COLUMN phone TEXT DEFAULT ""')
        if 'email' not in columns:
            cursor.execute('ALTER TABLE employees ADD COLUMN email TEXT DEFAULT ""')
        if 'synced_to_device' not in columns:
            cursor.execute('ALTER TABLE employees ADD COLUMN synced_to_device BOOLEAN DEFAULT 0')
        
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
            # Reiniciar sesión si es necesario
            if not hasattr(self, 'session') or self.session is None:
                self.session = requests.Session()
                self.session.auth = HTTPDigestAuth(self.username, self.password)
            
            response = self.session.get(f"{self.base_url}/System/deviceInfo", timeout=10)
            self.connected = response.status_code == 200
            
            if not self.connected:
                print(f"Conexión fallida: HTTP {response.status_code}")
                # Intentar reconectar
                self.session = requests.Session()
                self.session.auth = HTTPDigestAuth(self.username, self.password)
                response = self.session.get(f"{self.base_url}/System/deviceInfo", timeout=10)
                self.connected = response.status_code == 200
            
            return self.connected
        except Exception as e:
            print(f"Error de conexión: {e}")
            self.connected = False
            return False
    
    def add_employee_to_device(self, employee_id, name):
        """Agregar empleado al dispositivo Hikvision"""
        try:
            # Datos del empleado para el dispositivo
            employee_data = {
                "UserInfo": {
                    "employeeNo": employee_id,
                    "name": name,
                    "userType": "normal",
                    "Valid": {
                        "enable": True,
                        "beginTime": "2024-01-01T00:00:00",
                        "endTime": "2030-12-31T23:59:59"
                    }
                }
            }
            
            url = f"{self.base_url}/AccessControl/UserInfo/Record"
            response = self.session.post(url, json=employee_data, timeout=10)
            
            if response.status_code in [200, 201]:
                return True, "Usuario agregado al dispositivo"
            else:
                return False, f"Error HTTP: {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def sync_employees_from_device(self):
        """Sincronizar empleados desde el dispositivo"""
        try:
            url = f"{self.base_url}/AccessControl/UserInfo/Search"
            search_data = {
                "UserInfoSearchCond": {
                    "searchID": "1",
                    "maxResults": 100,
                    "searchResultPosition": 0
                }
            }
            
            response = self.session.post(url, json=search_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("UserInfoSearch", {}).get("UserInfo", [])
                
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
                
                return True, f"Sincronizados {synced_count} empleados"
            else:
                return False, f"Error HTTP: {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def add_employee(self, employee_id, name, department="General", phone="", email="", sync_to_device=True):
        """Agregar empleado al sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Agregar a la base de datos local
            cursor.execute('''
                INSERT INTO employees (employee_id, name, department, phone, email, synced_to_device) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, name, department, phone, email, sync_to_device))
            conn.commit()
            
            # Sincronizar con el dispositivo si está habilitado
            device_success = True
            device_message = ""
            
            if sync_to_device and self.connected:
                device_success, device_message = self.add_employee_to_device(employee_id, name)
                
                if device_success:
                    cursor.execute('''
                        UPDATE employees SET synced_to_device = 1 WHERE employee_id = ?
                    ''', (employee_id,))
                    conn.commit()
            
            conn.close()
            
            # Emitir evento en tiempo real
            socketio.emit('employee_added', {
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'synced': device_success
            })
            
            return True, f"Empleado agregado. {device_message if sync_to_device else ''}"
            
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
        
        try:
            cursor.execute('''
                SELECT employee_id, name, department, 
                       COALESCE(phone, '') as phone, 
                       COALESCE(email, '') as email, 
                       active, 
                       COALESCE(synced_to_device, 0) as synced_to_device, 
                       created_at
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
            
        except sqlite3.OperationalError:
            # Fallback para tablas sin las nuevas columnas
            cursor.execute('SELECT employee_id, name, department, active, created_at FROM employees ORDER BY name')
            employees = cursor.fetchall()
            conn.close()
            
            return [{
                'employee_id': emp[0],
                'name': emp[1],
                'department': emp[2] or 'General',
                'phone': '',
                'email': '',
                'active': emp[3],
                'synced': False,
                'created_at': emp[4]
            } for emp in employees]
    
    def record_attendance(self, employee_id, timestamp, reader_no=1, verify_method="huella"):
        """Registrar asistencia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar empleado
        cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
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
        
        # Emitir evento en tiempo real
        socketio.emit('attendance_record', {
            'employee_id': employee_id,
            'name': employee[0],
            'event_type': event_type,
            'timestamp': timestamp,
            'verify_method': verify_method
        })
        
        return True
    
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
        
        # Resumen del día
        cursor.execute('SELECT COUNT(*) FROM attendance_records WHERE date(timestamp) = ?', (today,))
        total_records = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT employee_id) FROM attendance_records WHERE date(timestamp) = ?', (today,))
        unique_employees = cursor.fetchone()[0]
        
        # Empleados dentro/fuera
        cursor.execute('''
            SELECT e.name, e.employee_id, ar.event_type, ar.timestamp
            FROM employees e
            LEFT JOIN (
                SELECT employee_id, event_type, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY timestamp DESC) as rn
                FROM attendance_records
                WHERE date(timestamp) = ?
            ) ar ON e.employee_id = ar.employee_id AND ar.rn = 1
            WHERE e.active = 1
        ''', (today,))
        
        employees_status = cursor.fetchall()
        
        # Registros recientes
        cursor.execute('''
            SELECT e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE date(ar.timestamp) = ?
            ORDER BY ar.timestamp DESC LIMIT 10
        ''', (today,))
        
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
        """Monitorear eventos del dispositivo"""
        url = f"{self.base_url}/Event/notification/alertStream"
        reconnect_attempts = 0
        max_attempts = 5
        
        while self.monitoring:
            try:
                # Verificar conexión
                if not self.test_connection():
                    reconnect_attempts += 1
                    if reconnect_attempts >= max_attempts:
                        print(f"Máximo de intentos de reconexión alcanzado ({max_attempts})")
                        socketio.emit('connection_lost', {'message': 'Conexión perdida con el dispositivo'})
                        time.sleep(30)  # Esperar más tiempo antes de reintentar
                        reconnect_attempts = 0
                    else:
                        print(f"Intento de reconexión {reconnect_attempts}/{max_attempts}")
                        time.sleep(5)
                    continue
                
                # Resetear contador si la conexión es exitosa
                reconnect_attempts = 0
                
                print("Conectando al stream de eventos...")
                response = self.session.get(url, stream=True, timeout=30)
                
                if response.status_code == 200:
                    print("✅ Stream conectado")
                    socketio.emit('connection_restored', {'message': 'Conexión restaurada'})
                    
                    current_json = ""
                    collecting = False
                    brace_count = 0
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if not self.monitoring:
                            break
                            
                        if line:
                            line = line.strip()
                            
                            if '{' in line and not collecting:
                                collecting = True
                                current_json = ""
                                brace_count = 0
                            
                            if collecting:
                                current_json += line
                                brace_count += line.count('{') - line.count('}')
                                
                                if brace_count == 0:
                                    try:
                                        event = json.loads(current_json)
                                        self._process_event(event)
                                    except json.JSONDecodeError:
                                        pass
                                    collecting = False
                                    current_json = ""
                else:
                    print(f"❌ Error HTTP: {response.status_code}")
                    time.sleep(10)
                    
            except requests.exceptions.Timeout:
                print("⏰ Timeout en el stream, reconectando...")
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ Error en monitoreo: {e}")
                time.sleep(10)
    
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
    
    def _decode_verify_method(self, mode):
        """Decodificar método de verificación"""
        if 'Fp' in mode or 'finger' in mode.lower():
            return 'huella'
        elif 'card' in mode.lower():
            return 'tarjeta'
        elif 'face' in mode.lower():
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
        data.get('email', ''),
        data.get('sync_to_device', True)
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/sync_employees', methods=['POST'])
def api_sync_employees():
    success, message = system.sync_employees_from_device()
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
    return jsonify({'connected': connected})

if __name__ == '__main__':
    # Iniciar monitoreo automáticamente
    system.start_monitoring()
    
    # Ejecutar aplicación web
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)