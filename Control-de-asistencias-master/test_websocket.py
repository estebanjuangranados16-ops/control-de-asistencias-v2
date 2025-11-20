#!/usr/bin/env python3
"""
Script simple para probar WebSockets
"""

import sqlite3
from datetime import datetime
from unified_system import system, socketio

def test_websocket_event():
    """Prueba directa de WebSocket"""
    
    # Obtener primer empleado
    conn = sqlite3.connect(system.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT employee_id, name FROM employees WHERE active = 1 LIMIT 1')
    employee = cursor.fetchone()
    conn.close()
    
    if not employee:
        print("❌ No hay empleados activos")
        return
    
    employee_id, name = employee
    timestamp = datetime.now().isoformat()
    
    print(f"🧪 Probando WebSocket para {name} (ID: {employee_id})")
    
    # Registrar asistencia directamente
    success = system.record_attendance(employee_id, timestamp, 1, "huella")
    
    if success:
        print("✅ Evento registrado y WebSocket emitido")
    else:
        print("❌ Error al registrar evento")

if __name__ == "__main__":
    print("🧪 PRUEBA DE WEBSOCKET")
    print("=" * 30)
    print("📱 Abre el dashboard en http://localhost:3000")
    print("⏳ Presiona Enter para enviar evento de prueba...")
    
    input()
    test_websocket_event()
    
    print("\n✅ Evento enviado. ¿Apareció en el dashboard?")