#!/usr/bin/env python3
"""
Script de prueba para simular eventos de asistencia en tiempo real
Útil para probar el sistema sin necesidad del dispositivo Hikvision
"""

import sqlite3
import time
import random
from datetime import datetime
from unified_system import system, socketio, app
import threading

def simulate_fingerprint_event():
    """Simula un evento de huella dactilar"""
    
    # Obtener empleados de la base de datos
    conn = sqlite3.connect(system.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT employee_id, name FROM employees WHERE active = 1')
    employees = cursor.fetchall()
    conn.close()
    
    if not employees:
        print("❌ No hay empleados activos para simular")
        return
    
    # Seleccionar empleado aleatorio
    employee_id, name = random.choice(employees)
    
    # Simular evento
    timestamp = datetime.now().isoformat()
    verify_method = random.choice(['huella', 'tarjeta', 'facial'])
    
    print(f"🔄 Simulando evento para {name} (ID: {employee_id})")
    
    # Registrar asistencia
    success = system.record_attendance(employee_id, timestamp, 1, verify_method)
    
    if success:
        print(f"✅ Evento registrado exitosamente")
    else:
        print(f"❌ Error al registrar evento")

def run_simulation():
    """Ejecuta la simulación de eventos"""
    print("🚀 Iniciando simulación de eventos de asistencia")
    print("📱 Abre el dashboard en http://localhost:3000 para ver los eventos en tiempo real")
    print("⏹️  Presiona Ctrl+C para detener\n")
    
    try:
        while True:
            # Esperar entre 5 y 15 segundos entre eventos
            wait_time = random.randint(5, 15)
            print(f"⏳ Esperando {wait_time} segundos para el próximo evento...")
            time.sleep(wait_time)
            
            simulate_fingerprint_event()
            print()
            
    except KeyboardInterrupt:
        print("\n🛑 Simulación detenida por el usuario")

if __name__ == "__main__":
    print("🧪 SIMULADOR DE EVENTOS DE ASISTENCIA")
    print("=" * 50)
    
    # Verificar que hay empleados
    conn = sqlite3.connect(system.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM employees WHERE active = 1')
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        print("❌ No hay empleados activos en la base de datos")
        print("💡 Agrega algunos empleados primero usando el dashboard web")
        exit(1)
    
    print(f"👥 Encontrados {count} empleados activos")
    print("🎯 El simulador generará eventos aleatorios para estos empleados")
    
    # Iniciar simulación
    run_simulation()