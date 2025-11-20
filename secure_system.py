# Sistema con autenticación para acceso público
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Agregar tabla de usuarios
def init_users_table():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'viewer',
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Usuario admin por defecto
    admin_hash = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, role) 
        VALUES ('admin', ?, 'admin')
    ''', (admin_hash,))
    
    conn.commit()
    conn.close()

@app.route('/login')
def login_page():
    return '''
    <form method="POST" action="/login">
        Usuario: <input name="username" required><br>
        Contraseña: <input name="password" type="password" required><br>
        <button type="submit">Ingresar</button>
    </form>
    '''

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash, role FROM users WHERE username = ? AND active = 1', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[0], password):
        session['user'] = username
        session['role'] = user[1]
        return redirect('/')
    
    return 'Credenciales incorrectas'

# Agregar antes de cada ruta
def require_auth():
    if 'user' not in session:
        return redirect('/login')