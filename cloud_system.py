from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from datetime import datetime, time as dt_time
import threading
import time
import requests
from requests.auth import HTTPDigestAuth

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hikvision_attendance_2024')

# Configure CORS
CORS(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')])
socketio = SocketIO(app, cors_allowed_origins="*")

class CloudAttendanceSystem:
    def __init__(self):
        # MongoDB connection
        self.mongo_uri = os.getenv('MONGODB_URI')
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client.attendance_db
        
        # Collections
        self.employees = self.db.employees
        self.attendance_records = self.db.attendance_records
        
        # Device configuration
        self.device_ip = os.getenv('DEVICE_IP', '172.10.0.66')
        self.username = os.getenv('DEVICE_USERNAME', 'admin')
        self.password = os.getenv('DEVICE_PASSWORD', 'PC2024*+')
        
        # Device session
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(self.username, self.password)
        self.session.timeout = 10
        self.base_url = f"http://{self.device_ip}/ISAPI"
        
        # System state
        self.monitoring = False
        self.connected = False
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize MongoDB collections and indexes"""
        try:
            # Create indexes for better performance
            self.employees.create_index("employee_id", unique=True)
            self.attendance_records.create_index([("employee_id", 1), ("timestamp", -1)])
            
            # Create default admin user if not exists
            if not self.employees.find_one({"employee_id": "1"}):
                self.employees.insert_one({
                    "employee_id": "1",
                    "name": "admin",
                    "department": "Administración",
                    "schedule": "Normal",
                    "phone": "",
                    "email": "",
                    "active": True,
                    "created_at": datetime.now()
                })
            
            print("✅ MongoDB initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing MongoDB: {e}")
    
    def test_connection(self):
        """Test device connection"""
        try:
            endpoints = [
                f"{self.base_url}/System/deviceInfo",
                f"http://{self.device_ip}/ISAPI/System/status",
                f"http://{self.device_ip}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=2)
                    if response.status_code in [200, 401]:
                        self.connected = True
                        return True
                except:
                    continue
                    
            self.connected = False
            return False
        except:
            self.connected = False
            return False
    
    def record_attendance(self, employee_id, timestamp, reader_no=1, verify_method="huella"):
        """Record attendance in MongoDB"""
        try:
            # Find employee
            employee = self.employees.find_one({"employee_id": employee_id})
            if not employee:
                print(f"Employee {employee_id} not found")
                return False
            
            # Use local timestamp
            local_timestamp = datetime.now()
            
            # Check for recent duplicate (within 10 seconds)
            recent_record = self.attendance_records.find_one({
                "employee_id": employee_id,
                "timestamp": {"$gte": datetime.now().replace(second=datetime.now().second-10)}
            })
            
            if recent_record:
                print(f"DUPLICATE AVOIDED: {employee['name']}")
                return False
            
            # Determine event type
            event_type = self.determine_event_type(employee_id)
            
            # Insert record
            record = {
                "employee_id": employee_id,
                "event_type": event_type,
                "timestamp": local_timestamp,
                "reader_no": reader_no,
                "verify_method": verify_method,
                "status": "autorizado"
            }
            
            self.attendance_records.insert_one(record)
            
            print(f"✅ RECORD: {employee['name']} - {event_type.upper()} - {local_timestamp}")
            
            # Emit real-time event
            socketio.emit('attendance_record', {
                'employee_id': employee_id,
                'name': employee['name'],
                'event_type': event_type,
                'timestamp': local_timestamp.isoformat(),
                'verify_method': verify_method,
                'department': employee.get('department', 'General'),
                'schedule': employee.get('schedule', 'Normal')
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Error recording attendance: {e}")
            return False
    
    def determine_event_type(self, employee_id):
        """Determine if it's entry or exit"""
        # Get last record for today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        last_record = self.attendance_records.find_one({
            "employee_id": employee_id,
            "timestamp": {"$gte": today_start}
        }, sort=[("timestamp", -1)])
        
        if not last_record:
            return 'entrada'
        
        return 'entrada' if last_record['event_type'] == 'salida' else 'salida'
    
    def get_dashboard_data(self):
        """Get dashboard data from MongoDB"""
        try:
            # Total records today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            total_records = self.attendance_records.count_documents({
                "timestamp": {"$gte": today_start}
            })
            
            # Unique employees today
            unique_employees = len(self.attendance_records.distinct("employee_id", {
                "timestamp": {"$gte": today_start}
            }))
            
            # Employee status
            pipeline = [
                {"$match": {"timestamp": {"$gte": today_start}}},
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": "$employee_id",
                    "last_event": {"$first": "$event_type"},
                    "last_time": {"$first": "$timestamp"}
                }}
            ]
            
            employee_status = list(self.attendance_records.aggregate(pipeline))
            
            employees_inside = []
            employees_outside = []
            
            for status in employee_status:
                employee = self.employees.find_one({"employee_id": status["_id"]})
                if employee and employee.get('active', True):
                    emp_data = {
                        'id': status["_id"],
                        'name': employee['name'],
                        'time': status["last_time"].isoformat() if status["last_time"] else None
                    }
                    
                    if status["last_event"] == 'entrada':
                        employees_inside.append(emp_data)
                    else:
                        employees_outside.append(emp_data)
            
            # Recent records
            recent_records = []
            recent_cursor = self.attendance_records.find({
                "timestamp": {"$gte": today_start}
            }).sort("timestamp", -1).limit(20)
            
            for record in recent_cursor:
                employee = self.employees.find_one({"employee_id": record["employee_id"]})
                if employee:
                    recent_records.append([
                        employee['name'],
                        record['event_type'],
                        record['timestamp'].isoformat(),
                        record['verify_method']
                    ])
            
            return {
                'total_records': total_records,
                'unique_employees': unique_employees,
                'employees_inside': employees_inside,
                'employees_outside': employees_outside,
                'recent_records': recent_records,
                'connected': self.connected,
                'monitoring': self.monitoring
            }
            
        except Exception as e:
            print(f"❌ Error getting dashboard data: {e}")
            return {
                'total_records': 0,
                'unique_employees': 0,
                'employees_inside': [],
                'employees_outside': [],
                'recent_records': [],
                'connected': self.connected,
                'monitoring': self.monitoring
            }
    
    def get_employees(self):
        """Get all employees from MongoDB"""
        try:
            employees = []
            for emp in self.employees.find().sort("name", 1):
                employees.append({
                    'employee_id': emp['employee_id'],
                    'name': emp['name'],
                    'department': emp.get('department', 'General'),
                    'schedule': emp.get('schedule', 'Normal'),
                    'phone': emp.get('phone', ''),
                    'email': emp.get('email', ''),
                    'active': emp.get('active', True),
                    'created_at': emp.get('created_at', datetime.now()).isoformat()
                })
            return employees
        except Exception as e:
            print(f"❌ Error getting employees: {e}")
            return []
    
    def add_employee(self, employee_id, name, department="General", schedule="Normal", phone="", email=""):
        """Add new employee to MongoDB"""
        try:
            employee_doc = {
                "employee_id": employee_id,
                "name": name,
                "department": department,
                "schedule": schedule,
                "phone": phone,
                "email": email,
                "active": True,
                "created_at": datetime.now()
            }
            
            self.employees.insert_one(employee_doc)
            return True, f"Employee {name} added successfully"
            
        except pymongo.errors.DuplicateKeyError:
            return False, f"Employee with ID {employee_id} already exists"
        except Exception as e:
            return False, f"Error: {str(e)}"

# Initialize system
system = CloudAttendanceSystem()

# API Routes
@app.route('/api/dashboard')
def api_dashboard():
    return jsonify(system.get_dashboard_data())

@app.route('/api/employees')
def api_employees():
    return jsonify(system.get_employees())

@app.route('/api/employees', methods=['POST'])
def api_add_employee():
    data = request.json
    success, message = system.add_employee(
        data['employee_id'],
        data['name'],
        data.get('department', 'General'),
        data.get('schedule', 'Normal'),
        data.get('phone', ''),
        data.get('email', '')
    )
    return jsonify({'success': success, 'message': message})

@app.route('/api/test_connection', methods=['POST'])
def api_test_connection():
    connected = system.test_connection()
    message = "✅ Device connected" if connected else "❌ Device not available"
    return jsonify({'connected': connected, 'message': message})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'connected': system.connected, 'monitoring': system.monitoring})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("🚀 Cloud Attendance System Starting...")
    print(f"MongoDB: {'✅ Connected' if system.client.admin.command('ping') else '❌ Failed'}")
    print(f"Device: {'✅ Connected' if system.test_connection() else '❌ Disconnected'}")
    
    # Run with eventlet for better WebSocket support
    socketio.run(app, debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))