#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema mejorado
"""

import sqlite3
import requests
from datetime import datetime

def check_system_status():
    """Verificar estado del sistema"""
    print("🔍 Verificando estado del sistema...")
    
    # Verificar base de datos
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Contar empleados
        cursor.execute("SELECT COUNT(*) FROM employees WHERE active = 1")
        active_employees = cursor.fetchone()[0]
        
        # Contar registros de hoy
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE date(timestamp) = date('now')")
        today_records = cursor.fetchone()[0]
        
        # Últimos 5 registros
        cursor.execute("""
            SELECT e.name, ar.event_type, ar.timestamp, ar.status 
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            ORDER BY ar.timestamp DESC LIMIT 5
        """)
        recent_records = cursor.fetchall()
        
        conn.close()
        
        print(f"✅ Base de datos OK")
        print(f"   - Empleados activos: {active_employees}")
        print(f"   - Registros de hoy: {today_records}")
        print(f"   - Últimos registros:")
        
        for record in recent_records:
            name, event_type, timestamp, status = record
            print(f"     • {name} - {event_type} - {timestamp}")
            
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
    
    # Verificar API web
    try:
        response = requests.get('http://localhost:5000/api/dashboard', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Web OK")
            print(f"   - Conectado al dispositivo: {data.get('connected', False)}")
            print(f"   - Monitoreando: {data.get('monitoring', False)}")
        else:
            print(f"⚠️ API Web responde con código: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor web no está ejecutándose")
    except Exception as e:
        print(f"❌ Error en API: {e}")

def show_employee_status():
    """Mostrar estado actual de empleados"""
    print("\n👥 Estado actual de empleados:")
    
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Obtener último evento de cada empleado
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
        
        inside_count = 0
        outside_count = 0
        
        for emp in employees:
            name, emp_id, last_event, timestamp = emp
            
            if last_event == 'entrada':
                status = "🟢 DENTRO"
                inside_count += 1
            elif last_event == 'salida':
                status = "🔴 FUERA"
                outside_count += 1
            else:
                status = "⚪ SIN REGISTRO"
                outside_count += 1
            
            time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S') if timestamp else 'N/A'
            print(f"   {status} - {name} (ID: {emp_id}) - Último: {time_str}")
        
        print(f"\n📊 Resumen: {inside_count} dentro, {outside_count} fuera")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🏢 Sistema de Asistencia Hikvision - Verificación")
    print("=" * 50)
    
    check_system_status()
    show_employee_status()
    
    print("\n💡 Para usar el sistema:")
    print("   1. Ejecutar: python unified_system_fixed.py")
    print("   2. Abrir: http://localhost:5000")
    print("   3. Probar huella dactilar en el dispositivo")