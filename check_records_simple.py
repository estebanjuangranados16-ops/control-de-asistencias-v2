import sqlite3
from datetime import datetime

def check_attendance_records():
    """Verificar registros de asistencia en la base de datos"""
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Verificar empleados
        print("EMPLEADOS REGISTRADOS:")
        cursor.execute("SELECT employee_id, name, department FROM employees")
        employees = cursor.fetchall()
        
        for emp in employees:
            print(f"   ID: {emp[0]} | Nombre: {emp[1]} | Depto: {emp[2]}")
        
        print(f"\nREGISTROS DE ASISTENCIA:")
        
        # Registros recientes (últimas 24 horas)
        cursor.execute('''
            SELECT ar.employee_id, e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE datetime(ar.timestamp) >= datetime('now', '-1 day')
            ORDER BY ar.timestamp DESC
            LIMIT 20
        ''')
        
        records = cursor.fetchall()
        
        if records:
            print(f"Registros recientes (últimas 24 horas):")
            for record in records:
                emp_id, name, event_type, timestamp, method = record
                try:
                    # Manejar timestamp con zona horaria
                    dt = datetime.fromisoformat(timestamp.replace('+08:00', ''))
                    time_str = dt.strftime('%H:%M:%S')
                    date_str = dt.strftime('%Y-%m-%d')
                    print(f"   {date_str} {time_str} | {name} ({emp_id}) | {event_type.upper()} | {method}")
                except:
                    print(f"   {timestamp} | {name} ({emp_id}) | {event_type.upper()} | {method}")
        else:
            print("No hay registros recientes")
        
        # Estadísticas
        cursor.execute("SELECT COUNT(*) FROM attendance_records")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE datetime(timestamp) >= datetime('now', '-1 day')")
        recent = cursor.fetchone()[0]
        
        print(f"\nESTADÍSTICAS:")
        print(f"   Total de registros: {total}")
        print(f"   Registros últimas 24h: {recent}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_attendance_records()