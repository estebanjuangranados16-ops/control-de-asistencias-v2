from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)

class AttendanceDashboard:
    def __init__(self, db_path="attendance.db"):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_today_summary(self):
        """Resumen del día actual"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Total de registros hoy
        cursor.execute('''
            SELECT COUNT(*) FROM attendance_records 
            WHERE date(timestamp) = ?
        ''', (today,))
        total_records = cursor.fetchone()[0]
        
        # Empleados únicos hoy
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) FROM attendance_records 
            WHERE date(timestamp) = ?
        ''', (today,))
        unique_employees = cursor.fetchone()[0]
        
        # Últimos 10 registros
        cursor.execute('''
            SELECT e.name, ar.event_type, ar.timestamp, ar.verify_method
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE date(ar.timestamp) = ?
            ORDER BY ar.timestamp DESC
            LIMIT 10
        ''', (today,))
        recent_records = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_records': total_records,
            'unique_employees': unique_employees,
            'recent_records': recent_records
        }
    
    def get_employee_status(self):
        """Estado actual de empleados (dentro/fuera)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT e.name, e.employee_id, ar.event_type, ar.timestamp
            FROM employees e
            LEFT JOIN (
                SELECT employee_id, event_type, timestamp,
                       ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY timestamp DESC) as rn
                FROM attendance_records
                WHERE date(timestamp) = ?
            ) ar ON e.employee_id = ar.employee_id AND ar.rn = 1
            WHERE e.active = 1
        ''', (today,))
        
        employees = cursor.fetchall()
        conn.close()
        
        inside = []
        outside = []
        
        for emp in employees:
            name, emp_id, last_event, timestamp = emp
            if last_event == 'entrada':
                inside.append({'name': name, 'id': emp_id, 'time': timestamp})
            else:
                outside.append({'name': name, 'id': emp_id, 'time': timestamp})
        
        return {'inside': inside, 'outside': outside}

dashboard = AttendanceDashboard()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/summary')
def api_summary():
    return jsonify(dashboard.get_today_summary())

@app.route('/api/employee_status')
def api_employee_status():
    return jsonify(dashboard.get_employee_status())

@app.route('/api/daily_report')
def api_daily_report():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = dashboard.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.name, e.employee_id, ar.event_type, ar.timestamp, ar.verify_method
        FROM attendance_records ar
        JOIN employees e ON ar.employee_id = e.employee_id
        WHERE date(ar.timestamp) = ?
        ORDER BY ar.timestamp
    ''', (date,))
    
    records = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'name': r[0],
        'employee_id': r[1],
        'event_type': r[2],
        'timestamp': r[3],
        'verify_method': r[4]
    } for r in records])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)