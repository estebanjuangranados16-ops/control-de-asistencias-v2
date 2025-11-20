import sqlite3

def clean_test_employees():
    """Eliminar empleados de prueba y mantener solo los reales"""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # Mostrar empleados actuales
    print("EMPLEADOS ACTUALES:")
    cursor.execute("SELECT employee_id, name, department FROM employees ORDER BY employee_id")
    employees = cursor.fetchall()
    
    for emp in employees:
        print(f"   ID: {emp[0]} | Nombre: {emp[1]} | Depto: {emp[2]}")
    
    # Empleados de prueba a eliminar (los que creé con nombres genéricos)
    test_employees = ['3']  # Solo eliminar María García si existe
    
    # Verificar cuáles existen
    for emp_id in test_employees:
        cursor.execute("SELECT name FROM employees WHERE employee_id = ?", (emp_id,))
        result = cursor.fetchone()
        if result:
            print(f"\nEliminando empleado de prueba: {result[0]} (ID: {emp_id})")
            
            # Eliminar registros de asistencia del empleado
            cursor.execute("DELETE FROM attendance_records WHERE employee_id = ?", (emp_id,))
            deleted_records = cursor.rowcount
            print(f"   - Eliminados {deleted_records} registros de asistencia")
            
            # Eliminar empleado
            cursor.execute("DELETE FROM employees WHERE employee_id = ?", (emp_id,))
            print(f"   - Empleado eliminado")
    
    # Actualizar nombres de empleados reales si es necesario
    real_employees = {
        '1': 'Admin Usuario',  # Mantener como está
        '2': 'Juan Pérez',     # Ya está correcto
        '4': 'Carlos López',   # Ya está correcto  
        '8': 'granados'        # Ya está correcto
    }
    
    for emp_id, correct_name in real_employees.items():
        cursor.execute("SELECT name FROM employees WHERE employee_id = ?", (emp_id,))
        result = cursor.fetchone()
        if result and result[0] != correct_name:
            cursor.execute("UPDATE employees SET name = ? WHERE employee_id = ?", (correct_name, emp_id))
            print(f"Actualizado nombre: {result[0]} -> {correct_name}")
    
    conn.commit()
    
    # Mostrar empleados finales
    print(f"\nEMPLEADOS FINALES:")
    cursor.execute("SELECT employee_id, name, department FROM employees ORDER BY employee_id")
    employees = cursor.fetchall()
    
    for emp in employees:
        print(f"   ID: {emp[0]} | Nombre: {emp[1]} | Depto: {emp[2]}")
    
    conn.close()
    print(f"\nLimpieza completada!")

if __name__ == "__main__":
    clean_test_employees()