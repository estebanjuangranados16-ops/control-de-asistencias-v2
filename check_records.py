import sqlite3
from datetime import datetime

def check_attendance_records():
    """Verificar registros de asistencia en la base de datos"""
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Verificar empleados
        print("👥 EMPLEADOS REGISTRADOS:")
        cursor.execute("SELECT employee_id, name, department FROM employees")
        employees = cursor.fetchall()
        
        for emp in employees:
            print(f"   ID: {emp[0]} | Nombre: {emp[1]} | Depto: {emp[2]}")
        
        print(f"\n📊 REGISTROS DE ASISTENCIA:")
        
        # Registros de hoy
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT ar.employee_id, e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE date(ar.timestamp) = ?
            ORDER BY ar.timestamp DESC
            LIMIT 20
        ''', (today,))
        
        records = cursor.fetchall()
        
        if records:
            print(f"Registros de hoy ({today}):")
            for record in records:
                emp_id, name, event_type, timestamp, method = record
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                print(f"   {time_str} | {name} ({emp_id}) | {event_type.upper()} | {method}")
        else:
            print("No hay registros de asistencia hoy")
        
        # Total de registros
        cursor.execute("SELECT COUNT(*) FROM attendance_records")
        total = cursor.fetchone()[0]
        print(f"\n📈 Total de registros: {total}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_attendance_records()