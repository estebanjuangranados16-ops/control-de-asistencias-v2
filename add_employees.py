import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Agregar empleados faltantes
employees = [
    ('1069643075', 'Empleado 1069643075', 'General', 'estandar'),
    ('8', 'Empleado 8', 'General', 'estandar')
]

for emp_id, name, dept, schedule in employees:
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO employees (employee_id, name, department, schedule, active) 
            VALUES (?, ?, ?, ?, 1)
        ''', (emp_id, name, dept, schedule))
        print(f"[OK] Agregado: {name} (ID: {emp_id})")
    except Exception as e:
        print(f"[ERROR] Error con {emp_id}: {e}")

conn.commit()
conn.close()
print("\nEmpleados agregados exitosamente!")