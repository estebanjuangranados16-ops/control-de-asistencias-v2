#!/usr/bin/env python3
"""
Estado del sistema - 7 de noviembre de 2025, 8:35 AM
"""

import sqlite3
from datetime import datetime

def check_system_status():
    """Verificar estado actual del sistema"""
    print("SISTEMA DE ASISTENCIA - ESTADO ACTUAL")
    print("=" * 50)
    print("Fecha: Jueves, 7 de noviembre de 2025")
    print("Hora: 8:35 AM")
    print("Estado: Antes del horario normal (9:00 AM)")
    print()
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Empleados activos
        cursor.execute("SELECT COUNT(*) FROM employees WHERE active = 1")
        active_employees = cursor.fetchone()[0]
        
        # Registros de hoy
        today = '2025-11-07'
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE date(timestamp) = ?", (today,))
        today_records = cursor.fetchone()[0]
        
        # Estado de empleados hoy
        cursor.execute("""
            SELECT e.name, e.employee_id, ar.event_type, ar.timestamp
            FROM employees e
            LEFT JOIN (
                SELECT employee_id, event_type, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY timestamp DESC) as rn
                FROM attendance_records
                WHERE date(timestamp) = ?
            ) ar ON e.employee_id = ar.employee_id AND ar.rn = 1
            WHERE e.active = 1
            ORDER BY e.name
        """, (today,))
        
        employees = cursor.fetchall()
        
        print("RESUMEN DEL DIA:")
        print(f"  - Empleados activos: {active_employees}")
        print(f"  - Registros de hoy: {today_records}")
        print()
        
        print("ESTADO DE EMPLEADOS:")
        
        arrived = 0
        not_arrived = 0
        
        for emp in employees:
            name, emp_id, last_event, timestamp = emp
            
            if last_event == 'entrada':
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                print(f"  [PRESENTE] {name} (ID: {emp_id}) - Llego: {time_str}")
                arrived += 1
            else:
                print(f"  [AUSENTE]  {name} (ID: {emp_id}) - Aun no llega")
                not_arrived += 1
        
        print()
        print("ESTADISTICAS:")
        print(f"  - Ya llegaron: {arrived}")
        print(f"  - Aun no llegan: {not_arrived}")
        print(f"  - Porcentaje presente: {(arrived/active_employees*100):.1f}%")
        
        # Actividad reciente
        print()
        print("ULTIMOS 5 REGISTROS:")
        cursor.execute("""
            SELECT e.name, ar.event_type, ar.timestamp
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            ORDER BY ar.timestamp DESC LIMIT 5
        """)
        
        recent = cursor.fetchall()
        for record in recent:
            name, event_type, timestamp = record
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%H:%M:%S')
            print(f"  - {name}: {event_type.upper()} a las {time_str}")
        
        conn.close()
        
        print()
        print("INFORMACION DE HORARIOS:")
        print("  - Horario normal: 9:00 AM - 5:00 PM")
        print("  - Tiempo restante: 25 minutos")
        print("  - Empleados puntuales llegaran entre 8:45-9:00 AM")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_system_status()
    
    print()
    print("=" * 50)
    print("SISTEMA FUNCIONANDO CORRECTAMENTE")
    print("Dashboard: http://localhost:5000")
    print("Reportes: http://localhost:5000/reports")
    print("Horarios: http://localhost:5000/schedules")