import sqlite3
import os

def fix_database():
    """Script para reparar la base de datos existente"""
    db_path = "attendance.db"
    
    if not os.path.exists(db_path):
        print("❌ No se encontró la base de datos")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar estructura actual
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Columnas actuales: {columns}")
        
        # Agregar columnas faltantes
        if 'phone' not in columns:
            cursor.execute('ALTER TABLE employees ADD COLUMN phone TEXT DEFAULT ""')
            print("✅ Agregada columna 'phone'")
        
        if 'email' not in columns:
            cursor.execute('ALTER TABLE employees ADD COLUMN email TEXT DEFAULT ""')
            print("✅ Agregada columna 'email'")
        
        if 'synced_to_device' not in columns:
            cursor.execute('ALTER TABLE employees ADD COLUMN synced_to_device BOOLEAN DEFAULT 0')
            print("✅ Agregada columna 'synced_to_device'")
        
        # Verificar estructura final
        cursor.execute("PRAGMA table_info(employees)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Columnas finales: {final_columns}")
        
        conn.commit()
        print("✅ Base de datos reparada exitosamente")
        
    except Exception as e:
        print(f"❌ Error reparando base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()