import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# El empleado ID "1" ya existe (admin), solo verificamos
cursor.execute('SELECT employee_id, name FROM employees WHERE active = 1')
employees = cursor.fetchall()

print("Empleados activos en la base de datos:")
for emp in employees:
    print(f"  ID: {emp[0]} - Nombre: {emp[1]}")

conn.close()