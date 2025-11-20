from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
import threading
import time
import json
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hikvision_attendance_2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = "attendance.db"
DEVICE_IP = "172.10.0.66"
USERNAME = "admin"
PASSWORD = "PC2024*+"

monitoring = False
connected = False

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            employee_id TEXT UNIQUE,
            name TEXT,
            department TEXT,
            active BOOLEAN DEFAULT 1,
            phone TEXT DEFAULT "",
            email TEXT DEFAULT "",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    # No insertar usuarios ficticios
    
    conn.commit()
    conn.close()

def determine_event_type(employee_id):
    conn = sqlite3.connect(DB_PATH)
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

def record_attendance(employee_id, timestamp, reader_no=1, verify_method="huella"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
    employee = cursor.fetchone()
    
    if not employee:
        conn.close()
        return False
    
    event_type = determine_event_type(employee_id)
    
    cursor.execute('''
        INSERT INTO attendance_records 
        (employee_id, event_type, timestamp, reader_no, verify_method, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (employee_id, event_type, timestamp, reader_no, verify_method, "autorizado"))
    
    conn.commit()
    conn.close()
    
    # Emitir evento WebSocket
    socketio.emit('attendance_record', {
        'employee_id': employee_id,
        'name': employee[0],
        'event_type': event_type,
        'timestamp': timestamp,
        'verify_method': verify_method
    })
    
    print(f"Evento emitido: {employee[0]} - {event_type}")
    return True

def get_dashboard_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute('SELECT COUNT(*) FROM attendance_records WHERE date(timestamp) = ?', (today,))
    total_records = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT employee_id) FROM attendance_records WHERE date(timestamp) = ?', (today,))
    unique_employees = cursor.fetchone()[0]
    
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
        'connected': connected,
        'monitoring': monitoring
    }

def get_employees():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT employee_id, name, department, phone, email, active, created_at FROM employees ORDER BY name')
    employees = cursor.fetchall()
    conn.close()
    
    return [{
        'employee_id': emp[0],
        'name': emp[1],
        'department': emp[2] or 'General',
        'phone': emp[3] or '',
        'email': emp[4] or '',
        'active': emp[5],
        'created_at': emp[6]
    } for emp in employees]

def test_connection():
    """Probar conexión con el dispositivo"""
    global connected
    try:
        session = requests.Session()
        session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
        response = session.get(f"http://{DEVICE_IP}/ISAPI/System/deviceInfo", timeout=10)
        connected = response.status_code == 200
        return connected
    except Exception as e:
        print(f"Error de conexión: {e}")
        connected = False
        return False

def monitor_events():
    """Monitorear eventos del dispositivo Hikvision"""
    global monitoring, connected
    
    url = f"http://{DEVICE_IP}/ISAPI/Event/notification/alertStream"
    
    while monitoring:
        try:
            if not test_connection():
                print("Dispositivo desconectado, reintentando...")
                time.sleep(5)
                continue
            
            session = requests.Session()
            session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
            
            print("Conectando al stream de eventos...")
            response = session.get(url, stream=True, timeout=30)
            
            if response.status_code == 200:
                print("Stream conectado - Esperando eventos de huella...")
                
                current_json = ""
                collecting = False
                brace_count = 0
                
                for line in response.iter_lines(decode_unicode=True):
                    if not monitoring:
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
                                    process_event(event)
                                except json.JSONDecodeError:
                                    pass
                                collecting = False
                                current_json = ""
            else:
                print(f"Error HTTP: {response.status_code}")
                time.sleep(10)
                
        except requests.exceptions.Timeout:
            print("Timeout en el stream, reconectando...")
            time.sleep(5)
        except Exception as e:
            print(f"Error en monitoreo: {e}")
            time.sleep(10)

def process_event(event):
    """Procesar eventos del dispositivo"""
    if 'AccessControllerEvent' in event:
        acs_event = event['AccessControllerEvent']
        sub_type = acs_event.get('subEventType')
        
        if sub_type == 38:  # Acceso autorizado
            employee_id = acs_event.get('employeeNoString')
            timestamp = event.get('dateTime', datetime.now().isoformat())
            reader_no = acs_event.get('cardReaderNo', 1)
            verify_method = decode_verify_method(acs_event.get('currentVerifyMode', 'unknown'))
            
            if employee_id:
                print(f"Evento de huella detectado: Empleado {employee_id}")
                success = record_attendance(employee_id, timestamp, reader_no, verify_method)
                if success:
                    print(f"Evento procesado y enviado via WebSocket")
                else:
                    print(f"Error: Empleado {employee_id} no encontrado en la base de datos")

def decode_verify_method(mode):
    """Decodificar método de verificación"""
    if 'Fp' in mode or 'finger' in mode.lower():
        return 'huella'
    elif 'card' in mode.lower():
        return 'tarjeta'
    elif 'face' in mode.lower():
        return 'facial'
    else:
        return 'desconocido'

def start_monitoring():
    """Iniciar monitoreo en hilo separado"""
    global monitoring
    if not monitoring:
        monitoring = True
        monitor_thread = threading.Thread(target=monitor_events, daemon=True)
        monitor_thread.start()
        print("Monitoreo de eventos iniciado")

def stop_monitoring():
    """Detener monitoreo"""
    global monitoring
    monitoring = False
    print("Monitoreo de eventos detenido")

@socketio.on('connect')
def handle_connect():
    print('Cliente WebSocket conectado')
    emit('status', {'connected': True, 'monitoring': True})

@app.route('/')
def dashboard():
    return '<h1>Sistema de Asistencia Hikvision</h1><p>Frontend: http://localhost:3000</p>'

@app.route('/api/dashboard')
def api_dashboard():
    return jsonify(get_dashboard_data())

@app.route('/api/employees')
def api_employees():
    return jsonify(get_employees())

@app.route('/api/add_employee', methods=['POST'])
def api_add_employee():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO employees (employee_id, name, department, phone, email) 
            VALUES (?, ?, ?, ?, ?)
        ''', (data['employee_id'], data['name'], data.get('department', 'General'),
              data.get('phone', ''), data.get('email', '')))
        conn.commit()
        conn.close()
        
        socketio.emit('employee_added', {
            'employee_id': data['employee_id'],
            'name': data['name'],
            'department': data.get('department', 'General')
        })
        
        return jsonify({'success': True, 'message': 'Empleado agregado correctamente'})
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': f'El empleado con ID {data["employee_id"]} ya existe'})

@app.route('/api/start_monitoring', methods=['POST'])
def api_start_monitoring():
    start_monitoring()
    return jsonify({'success': True, 'message': 'Monitoreo iniciado'})

@app.route('/api/stop_monitoring', methods=['POST'])
def api_stop_monitoring():
    stop_monitoring()
    return jsonify({'success': True, 'message': 'Monitoreo detenido'})

@app.route('/api/test_connection', methods=['POST'])
def api_test_connection():
    connected = test_connection()
    return jsonify({'connected': connected})

if __name__ == '__main__':
    init_database()
    
    # Iniciar monitoreo automáticamente
    start_monitoring()
    
    print("Sistema de Asistencia Hikvision iniciado")
    print(f"Dispositivo: {DEVICE_IP}")
    print("Frontend: http://localhost:3000")
    print("Monitoreo de huellas en tiempo real activo...")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)