import requests
from requests.auth import HTTPDigestAuth
import json
import time
import xml.etree.ElementTree as ET  # Para fallback XML
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HikvisionISAPI:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}/ISAPI"
        self.session = requests.Session()
        # Empieza con DigestAuth
        self.session.auth = HTTPDigestAuth(username, password)
        # Headers para JSON preferido
        self.session.headers.update({'Accept': 'application/json'})
        
        # Retries automáticos
        retry_strategy = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def login_session(self):
        """Fallback: Login con sesión para streams"""
        print("🔄 Haciendo login de sesión...")
        login_url = f"{self.base_url}/Security/sessionLogin"
        login_data = {
            "userName": self.username,
            "password": self.password,
            "clientType": "DeviceManager"
        }
        try:
            response = self.session.post(login_url, json=login_data, timeout=5, verify=False)
            if response.status_code == 200:
                session_info = response.json()
                self.session_id = session_info.get("SessionID")
                # Remueve Digest y usa SessionID
                del self.session.auth
                self.session.headers.update({"X-SessionID": self.session_id})
                print("✅ Sesión autenticada")
                return True
            else:
                print(f"❌ Login sesión falló: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error login: {e}")
            return False
    
    def login_test(self):
        """Prueba la conexión con el dispositivo"""
        endpoints = [
            "/System/deviceInfo",
            "/System/status", 
            "/AccessControl/UserInfo/Count"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5, verify=False)
                print(f"Probando {endpoint}: {response.status_code}")
                if response.status_code == 200:
                    return True
            except Exception as e:
                print(f"Error en {endpoint}: {e}")
        return False
    
    def get_fingerprint_events(self):
        """Lee eventos de huella dactilar"""
        # Sin filtro por ahora para más eventos
        url = f"{self.base_url}/Event/notification/alertStream"
        print(f"Conectando al stream: {url}")
        
        while True:
            try:
                response = self.session.get(url, stream=True, timeout=None, verify=False)
                if response.status_code == 200:
                    print("Stream conectado. Esperando eventos de huella...")
                    
                    current_data = ""
                    collecting = False
                    brace_count = 0
                    
                    for line in response.iter_lines(decode_unicode=False):  # Como bytes para evitar errores
                        if line:
                            # Decode safe
                            line_str = line.decode('utf-8', errors='replace').strip()
                            
                            # Debug: Muestra líneas no vacías (comenta si spamea)
                            if len(line_str) > 10:
                                print(f"Debug línea: {line_str[:80]}...")
                            
                            # Detectar inicio de JSON
                            if '{' in line_str and not collecting:
                                collecting = True
                                current_data = ""
                                brace_count = 0
                            
                            if collecting:
                                current_data += line_str
                                brace_count += line_str.count('{') - line_str.count('}')
                                
                                if brace_count <= 0:  # <= para cerrar extras
                                    self.process_event_data(current_data)
                                    collecting = False
                                    current_data = ""
                                    
                            # Fallback XML en línea individual
                            if not collecting and '<EventNotificationAlert>' in line_str:
                                self.process_event_data(line_str)
                                
                else:
                    print(f"Error HTTP: {response.status_code}")
                    if response.status_code == 401:
                        if self.login_session():  # Re-auth real
                            print("🔄 Reintentando stream post-login...")
                            continue
                        else:
                            print("❌ No pudo re-auth, saliendo...")
                            break
                    time.sleep(5)
                    
            except requests.exceptions.Timeout:
                print("⏰ Timeout, reconectando...")
            except Exception as e:
                print(f"Conexión perdida: {e}")
                time.sleep(5)
    
    def process_event_data(self, data_str):
        """Procesa datos (JSON o XML)"""
        try:
            # JSON primero
            event = json.loads(data_str)
            self.process_event_json(event)
        except json.JSONDecodeError:
            # XML fallback
            try:
                if '<EventNotificationAlert>' in data_str:
                    root = ET.fromstring(data_str)
                    self.process_event_xml(root)
            except ET.ParseError:
                pass  # Ignora
    
    def process_event_json(self, event):
        """Procesa JSON"""
        if 'AccessControllerEvent' in event:
            acs_event = event['AccessControllerEvent']
            sub_type = acs_event.get('subEventType')
            timestamp = event.get('dateTime', 'N/A')
            
            if sub_type == 38:
                print(f"\n🟢 ACCESO AUTORIZADO")
                print(f"Usuario: {acs_event.get('name', 'N/A')}")
                print(f"ID: {acs_event.get('employeeNoString', 'N/A')}")
                print(f"Método: {self._decode_verify_mode(acs_event.get('currentVerifyMode', 'N/A'))}")
                print(f"Lector: {acs_event.get('cardReaderNo', 'N/A')}")
                print(f"Hora: {timestamp}")
                print("─" * 50)
                
            elif sub_type == 39:
                print(f"\n🔴 ACCESO DENEGADO")
                print(f"Método: {self._decode_verify_mode(acs_event.get('currentVerifyMode', 'N/A'))}")
                print(f"Lector: {acs_event.get('cardReaderNo', 'N/A')}")
                print(f"Hora: {timestamp}")
                print("─" * 50)
                
            elif sub_type in [21, 22]:
                door_status = "Abierta" if sub_type == 21 else "Cerrada"
                print(f"\n🚪 Puerta {door_status} - {timestamp}")
    
    def process_event_xml(self, root):
        """Procesa XML"""
        print(f"\n📡 EVENTO XML:")
        timestamp_elem = root.find('.//dateTime')
        timestamp = timestamp_elem.text if timestamp_elem is not None else 'N/A'
        print(f"Hora: {timestamp}")
        
        acs_elem = root.find('.//AccessControllerEvent')
        if acs_elem is not None:
            sub_type_elem = acs_elem.find('subEventType')
            sub_type = int(sub_type_elem.text) if sub_type_elem is not None else 0
            employee_no = acs_elem.find('employeeNoString')
            verify_mode = acs_elem.find('currentVerifyMode')
            
            if sub_type == 38:
                print(f"🟢 ACCESO AUTORIZADO (XML)")
                print(f"ID: {employee_no.text if employee_no is not None else 'N/A'}")
                print(f"Método: {self._decode_verify_mode(verify_mode.text if verify_mode is not None else 'N/A')}")
            elif sub_type == 39:
                print(f"🔴 ACCESO DENEGADO (XML)")
                print(f"Método: {self._decode_verify_mode(verify_mode.text if verify_mode is not None else 'N/A')}")
            else:
                print(f"🔍 Otro: Subtipo {sub_type}")
        
        print("─" * 50)
    
    def _decode_verify_mode(self, mode_code):
        """Decodifica método"""
        modes = {
            '19': 'Huella Dactilar',
            '2': 'Tarjeta',
            '5': 'Facial',
            '7': 'PIN'
        }
        return modes.get(mode_code, mode_code)

# Uso
if __name__ == "__main__":
    DEVICE_IP = "172.10.0.66"
    USERNAME = "admin"
    PASSWORD = "PC2024*+"
    
    device = HikvisionISAPI(DEVICE_IP, USERNAME, PASSWORD)
    
    print("Probando conexión...")
    if device.login_test():
        print("\n✅ Conexión exitosa al dispositivo Hikvision")
        print("📡 Monitoreando eventos en tiempo real")
        print("👆 Pon tu huella en el lector para ver los eventos")
        print("⏹️  Presiona Ctrl+C para detener\n")
        try:
            device.get_fingerprint_events()
        except KeyboardInterrupt:
            print("\n🛑 Monitoreo detenido por el usuario")
    else:
        print("\n❌ Error: No se pudo conectar al dispositivo")
        print("💡 Chequea IP, creds, y SDK enabled en la web.")