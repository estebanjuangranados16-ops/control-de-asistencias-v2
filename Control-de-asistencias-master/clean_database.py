import sqlite3

def clean_database():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Eliminar datos de prueba
    cursor.execute("DELETE FROM employees WHERE employee_id IN ('123', '456')")
    cursor.execute("DELETE FROM attendance_records WHERE employee_id IN ('123', '456')")
    
    conn.commit()
    conn.close()
    print("Base de datos limpiada")

if __name__ == "__main__":
    clean_database()