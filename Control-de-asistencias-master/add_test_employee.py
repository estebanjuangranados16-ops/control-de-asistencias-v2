import sqlite3

def add_test_employees():
    """Agregar empleados de prueba"""
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # Empleados de prueba
    employees = [
        ('1', 'Admin Usuario', 'Administración'),
        ('2', 'Juan Pérez', 'Ventas'),
        ('3', 'María García', 'Contabilidad'),
        ('4', 'Carlos López', 'IT')
    ]
    
    for emp_id, name, dept in employees:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO employees (employee_id, name, department) 
                VALUES (?, ?, ?)
            ''', (emp_id, name, dept))
            print(f"Empleado agregado: {name} (ID: {emp_id})")
        except Exception as e:
            print(f"Error agregando {name}: {e}")
    
    conn.commit()
    conn.close()
    print("Empleados de prueba agregados")

if __name__ == "__main__":
    add_test_employees()