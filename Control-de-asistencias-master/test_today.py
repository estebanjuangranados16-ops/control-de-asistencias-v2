#!/usr/bin/env python3
"""
Script para verificar el sistema con la fecha actual
7 de noviembre de 2025, 8:35 AM
"""

import sqlite3
from datetime import datetime

def check_today_status():
    """Verificar estado del día actual"""
    print("Sistema de Asistencia - Estado del Día")
    print("=" * 45)
    print("Fecha: Jueves, 7 de noviembre de 2025")
    print("Hora actual: 8:35 AM")
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
        
        # Estado actual de empleados (último evento)
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
        
        employees_status = cursor.fetchall()
        
        print(f"📊 Resumen del día:")
        print(f"   - Empleados activos: {active_employees}")
        print(f"   - Registros de hoy: {today_records}")
        print()
        
        print("👥 Estado actual de empleados:")
        
        arrived = 0
        not_arrived = 0
        
        for emp in employees_status:
            name, emp_id, last_event, timestamp = emp
            
            if last_event == 'entrada':
                status = "🟢 YA LLEGÓ"
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                arrived += 1
                print(f"   {status} - {name} (ID: {emp_id}) - {time_str}")
            else:
                status = "⚪ AÚN NO LLEGA"
                not_arrived += 1
                print(f"   {status} - {name} (ID: {emp_id})")
        
        print()
        print(f"📈 Resumen de llegadas:")
        print(f"   - Ya llegaron: {arrived}")
        print(f"   - Aún no llegan: {not_arrived}")
        
        # Horario normal: 9:00 AM
        print()
        print("⏰ Información de horarios:")
        print("   - Horario normal de entrada: 9:00 AM")
        print("   - Hora actual: 8:35 AM")
        print("   - Tiempo restante para horario: 25 minutos")
        
        if arrived > 0:
            print(f"   - Empleados que llegaron temprano: {arrived}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_recent_activity():
    """Mostrar actividad reciente"""
    print("\n📋 Actividad reciente (últimos 10 registros):")
    print("-" * 45)
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            ORDER BY ar.timestamp DESC LIMIT 10
        """)
        
        records = cursor.fetchall()
        
        for record in records:
            name, event_type, timestamp, verify_method = record
            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime('%d/%m/%Y %H:%M:%S')
            event_icon = "🟢" if event_type == "entrada" else "🔴"
            print(f"   {event_icon} {name} - {event_type.upper()} - {date_str} ({verify_method})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_today_status()
    show_recent_activity()
    
    print("\n" + "=" * 45)
    print("💡 Para monitorear en tiempo real:")
    print("   1. Ejecutar: python system_optimized.py")
    print("   2. Abrir: http://localhost:5000")
    print("   3. Ver reportes: http://localhost:5000/reports")
    print("   4. Gestionar horarios: http://localhost:5000/schedules")