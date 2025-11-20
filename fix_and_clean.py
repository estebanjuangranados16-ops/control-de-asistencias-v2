import sqlite3
from datetime import datetime

def fix_and_clean_database():
    """Limpiar empleados de prueba y mostrar registros recientes"""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    print("=== LIMPIEZA DE BASE DE DATOS ===")
    
    # 1. Eliminar empleado de prueba María García (ID: 3)
    cursor.execute("SELECT name FROM employees WHERE employee_id = '3'")
    if cursor.fetchone():
        cursor.execute("DELETE FROM attendance_records WHERE employee_id = '3'")
        deleted_records = cursor.rowcount
        cursor.execute("DELETE FROM employees WHERE employee_id = '3'")
        print(f"Eliminado: María García (ID: 3) y {deleted_records} registros")
    
    # 2. Mostrar empleados finales
    print(f"\nEMPLEADOS ACTIVOS:")
    cursor.execute("SELECT employee_id, name, department FROM employees ORDER BY employee_id")
    employees = cursor.fetchall()
    
    for emp in employees:
        print(f"   ID: {emp[0]} | Nombre: {emp[1]} | Depto: {emp[2]}")
    
    # 3. Mostrar registros recientes (últimas 24 horas)
    print(f"\nREGISTROS RECIENTES (últimas 24 horas):")
    cursor.execute('''
        SELECT ar.employee_id, e.name, ar.event_type, ar.timestamp, ar.verify_method
        FROM attendance_records ar
        JOIN employees e ON ar.employee_id = e.employee_id
        WHERE datetime(ar.timestamp) >= datetime('now', '-1 day')
        ORDER BY ar.timestamp DESC
        LIMIT 20
    ''')
    
    recent_records = cursor.fetchall()
    
    if recent_records:
        for record in recent_records:
            emp_id, name, event_type, timestamp, method = record
            # Convertir timestamp para mostrar
            try:
                dt = datetime.fromisoformat(timestamp.replace('+08:00', ''))
                time_str = dt.strftime('%H:%M:%S')
                date_str = dt.strftime('%Y-%m-%d')
                print(f"   {date_str} {time_str} | {name} ({emp_id}) | {event_type.upper()} | {method}")
            except:
                print(f"   {timestamp} | {name} ({emp_id}) | {event_type.upper()} | {method}")
    else:
        print("   No hay registros recientes")
    
    # 4. Estadísticas
    cursor.execute("SELECT COUNT(*) FROM attendance_records")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE date(timestamp) = date('now')")
    today = cursor.fetchone()[0]
    
    print(f"\nESTADÍSTICAS:")
    print(f"   Total de registros: {total}")
    print(f"   Registros de hoy: {today}")
    
    conn.commit()
    conn.close()
    print(f"\nLimpieza completada!")

if __name__ == "__main__":
    fix_and_clean_database()