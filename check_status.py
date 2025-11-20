#!/usr/bin/env python3
"""
Script simple para verificar el estado del sistema
"""

import sqlite3
import requests
from datetime import datetime

def check_database():
    """Verificar estado de la base de datos"""
    print("Verificando base de datos...")
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Contar empleados
        cursor.execute("SELECT COUNT(*) FROM employees WHERE active = 1")
        active_employees = cursor.fetchone()[0]
        
        # Contar registros recientes
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE datetime(timestamp) >= datetime('now', '-1 day')")
        recent_records = cursor.fetchone()[0]
        
        # Últimos registros
        cursor.execute("""
            SELECT e.name, ar.event_type, ar.timestamp 
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            ORDER BY ar.timestamp DESC LIMIT 5
        """)
        last_records = cursor.fetchall()
        
        conn.close()
        
        print(f"  - Empleados activos: {active_employees}")
        print(f"  - Registros (24h): {recent_records}")
        print("  - Ultimos registros:")
        
        for record in last_records:
            name, event_type, timestamp = record
            dt = datetime.fromisoformat(timestamp)
            print(f"    * {name} - {event_type} - {dt.strftime('%H:%M:%S')}")
            
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def check_web_server():
    """Verificar servidor web"""
    print("\nVerificando servidor web...")
    
    try:
        response = requests.get('http://localhost:5000/api/dashboard', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("  - Servidor web: OK")
            print(f"  - Conectado al dispositivo: {data.get('connected', False)}")
            print(f"  - Monitoreando: {data.get('monitoring', False)}")
            return True
        else:
            print(f"  - Servidor responde con codigo: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  - Servidor web NO esta ejecutandose")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def show_employee_status():
    """Mostrar estado de empleados"""
    print("\nEstado de empleados:")
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.name, e.employee_id, ar.event_type, ar.timestamp
            FROM employees e
            LEFT JOIN (
                SELECT employee_id, event_type, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY timestamp DESC) as rn
                FROM attendance_records
                WHERE datetime(timestamp) >= datetime('now', '-1 day')
            ) ar ON e.employee_id = ar.employee_id AND ar.rn = 1
            WHERE e.active = 1
            ORDER BY e.name
        """)
        
        employees = cursor.fetchall()
        conn.close()
        
        inside = 0
        outside = 0
        
        for emp in employees:
            name, emp_id, last_event, timestamp = emp
            
            if last_event == 'entrada':
                status = "DENTRO"
                inside += 1
            elif last_event == 'salida':
                status = "FUERA"
                outside += 1
            else:
                status = "SIN REGISTRO"
                outside += 1
            
            time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S') if timestamp else 'N/A'
            print(f"  - {status}: {name} (ID: {emp_id}) - {time_str}")
        
        print(f"\nResumen: {inside} dentro, {outside} fuera")
        
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == "__main__":
    print("Sistema de Asistencia Hikvision - Estado")
    print("=" * 45)
    
    db_ok = check_database()
    web_ok = check_web_server()
    
    if db_ok:
        show_employee_status()
    
    print("\n" + "=" * 45)
    if db_ok and web_ok:
        print("Sistema funcionando correctamente")
    elif db_ok:
        print("Base de datos OK - Iniciar servidor web")
    else:
        print("Revisar configuracion del sistema")
    
    print("\nPara iniciar el sistema:")
    print("  python system_optimized.py")
    print("  Abrir: http://localhost:5000")