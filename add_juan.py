import sqlite3

conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Agregar empleado Juan
cursor.execute('''
    INSERT OR IGNORE INTO employees (employee_id, name, department, schedule, active) 
    VALUES (?, ?, ?, ?, 1)
''', ('2', 'Juan', 'General', 'estandar'))

conn.commit()
conn.close()
print("[OK] Empleado Juan (ID: 2) agregado exitosamente!")