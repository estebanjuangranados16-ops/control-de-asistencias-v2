import requests
from requests.auth import HTTPDigestAuth
import json
import sqlite3
from datetime import datetime
import threading
import time

class AttendanceSystem:
    def __init__(self, device_ip, username, password, db_path="attendance.db"):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.db_path = db_path
        
        # Configurar conexión
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(username, password)
        self.base_url = f"http://{device_ip}/ISAPI"
        
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
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        print("✅ Base de datos inicializada")
    
    def add_employee(self, employee_id, name, department="General"):
        """Agregar nuevo empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO employees (employee_id, name, department) 
                VALUES (?, ?, ?)
            ''', (employee_id, name, department))
            conn.commit()
            print(f"✅ Empleado agregado: {name} (ID: {employee_id})")
            return True
        except sqlite3.IntegrityError:
            print(f"❌ El empleado con ID {employee_id} ya existe")
            return False
        finally:
            conn.close()
    
    def record_attendance(self, employee_id, event_type, timestamp, reader_no=1, verify_method="huella", status="autorizado"):
        """Registrar evento de asistencia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si el empleado existe
        cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            print(f"⚠️ Empleado {employee_id} no encontrado en la base de datos")
            conn.close()
            return False
        
        # Registrar asistencia
        cursor.execute('''
            INSERT INTO attendance_records 
            (employee_id, event_type, timestamp, reader_no, verify_method, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_id, event_type, timestamp, reader_no, verify_method, status))
        
        conn.commit()
        conn.close()
        
        # Determinar tipo de evento (entrada/salida)
        event_display = self.determine_event_type(employee_id)
        
        print(f"\n📋 REGISTRO DE ASISTENCIA")
        print(f"Empleado: {employee[0]} (ID: {employee_id})")
        print(f"Evento: {event_display}")
        print(f"Hora: {timestamp}")
        print(f"Método: {verify_method}")
        print("=" * 50)
        
        return True
    
    def determine_event_type(self, employee_id):
        """Determina si es entrada o salida basado en el último registro"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener último registro del día
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
    
    def get_daily_report(self, date=None):
        """Generar reporte diario"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.name, e.employee_id, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE date(ar.timestamp) = ?
            ORDER BY ar.timestamp
        ''', (date,))
        
        records = cursor.fetchall()
        conn.close()
        
        print(f"\n📊 REPORTE DIARIO - {date}")
        print("=" * 60)
        
        if not records:
            print("No hay registros para este día")
            return
        
        for record in records:
            name, emp_id, event_type, timestamp, method = record
            time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
            print(f"{time_str} | {name} ({emp_id}) | {event_type.upper()} | {method}")
    
    def start_monitoring(self):
        """Iniciar monitoreo de eventos"""
        url = f"{self.base_url}/Event/notification/alertStream"
        print("🔄 Iniciando monitoreo de asistencia...")
        
        while True:
            try:
                response = self.session.get(url, stream=True, timeout=None)
                if response.status_code == 200:
                    print("✅ Conectado al dispositivo. Monitoreando asistencia...")
                    
                    current_json = ""
                    collecting = False
                    brace_count = 0
                    
                    for line in response.iter_lines(decode_unicode=True):
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
                                        self.process_event(event)
                                    except json.JSONDecodeError:
                                        pass
                                    collecting = False
                                    current_json = ""
                                    
                else:
                    print(f"❌ Error HTTP: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"⚠️ Conexión perdida: {e}")
                print("🔄 Reconectando en 5 segundos...")
                time.sleep(5)
    
    def process_event(self, event):
        """Procesar eventos del dispositivo"""
        if 'AccessControllerEvent' in event:
            acs_event = event['AccessControllerEvent']
            sub_type = acs_event.get('subEventType')
            timestamp = event.get('dateTime', datetime.now().isoformat())
            
            # Solo procesar accesos autorizados
            if sub_type == 38:
                employee_id = acs_event.get('employeeNoString')
                reader_no = acs_event.get('cardReaderNo', 1)
                verify_method = self.decode_verify_method(acs_event.get('currentVerifyMode', 'unknown'))
                
                if employee_id:
                    event_type = self.determine_event_type(employee_id)
                    self.record_attendance(
                        employee_id=employee_id,
                        event_type=event_type,
                        timestamp=timestamp,
                        reader_no=reader_no,
                        verify_method=verify_method,
                        status="autorizado"
                    )
    
    def decode_verify_method(self, mode):
        """Decodificar método de verificación"""
        if 'Fp' in mode or 'finger' in mode.lower():
            return 'huella'
        elif 'card' in mode.lower():
            return 'tarjeta'
        elif 'face' in mode.lower():
            return 'facial'
        else:
            return 'desconocido'

def main():
    # Configuración
    DEVICE_IP = "172.10.0.66"
    USERNAME = "admin"
    PASSWORD = "PC2024*+"
    
    # Crear sistema
    system = AttendanceSystem(DEVICE_IP, USERNAME, PASSWORD)
    
    print("🏢 SISTEMA DE CONTROL DE ASISTENCIA")
    print("=" * 50)
    
    while True:
        print("\n📋 MENÚ PRINCIPAL")
        print("1. Iniciar monitoreo en tiempo real")
        print("2. Agregar empleado")
        print("3. Ver reporte diario")
        print("4. Salir")
        
        choice = input("\nSelecciona una opción: ").strip()
        
        if choice == '1':
            try:
                system.start_monitoring()
            except KeyboardInterrupt:
                print("\n🛑 Monitoreo detenido")
                
        elif choice == '2':
            emp_id = input("ID del empleado: ").strip()
            name = input("Nombre: ").strip()
            dept = input("Departamento (opcional): ").strip() or "General"
            system.add_employee(emp_id, name, dept)
            
        elif choice == '3':
            date_input = input("Fecha (YYYY-MM-DD) o Enter para hoy: ").strip()
            date = date_input if date_input else None
            system.get_daily_report(date)
            
        elif choice == '4':
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()