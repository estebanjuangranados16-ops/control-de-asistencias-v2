import requests
from requests.auth import HTTPDigestAuth
import time

def test_hikvision_connection():
    """Probar conexión con el dispositivo Hikvision"""
    DEVICE_IP = "172.10.0.66"
    USERNAME = "admin"
    PASSWORD = "PC2024*+"
    
    session = requests.Session()
    session.auth = HTTPDigestAuth(USERNAME, PASSWORD)
    base_url = f"http://{DEVICE_IP}/ISAPI"
    
    print("🔍 Probando conexión con dispositivo Hikvision...")
    print(f"📍 IP: {DEVICE_IP}")
    
    # Probar diferentes endpoints
    endpoints = [
        "/System/deviceInfo",
        "/System/status",
        "/AccessControl/UserInfo/Count",
        "/System/capabilities"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🔗 Probando: {endpoint}")
            response = session.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Éxito")
                if endpoint == "/System/deviceInfo":
                    try:
                        data = response.json()
                        print(f"   📱 Modelo: {data.get('DeviceInfo', {}).get('model', 'N/A')}")
                        print(f"   🔢 Firmware: {data.get('DeviceInfo', {}).get('firmwareVersion', 'N/A')}")
                    except:
                        print(f"   📄 Respuesta XML/Texto")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Error de conexión")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Probar stream de eventos
    print(f"\n🎯 Probando stream de eventos...")
    try:
        stream_url = f"{base_url}/Event/notification/alertStream"
        response = session.get(stream_url, stream=True, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Stream disponible")
            print(f"   📡 Esperando eventos por 10 segundos...")
            
            start_time = time.time()
            for line in response.iter_lines():
                if time.time() - start_time > 10:
                    break
                if line:
                    line_str = line.decode('utf-8', errors='replace')
                    if len(line_str) > 20:
                        print(f"   📨 Evento: {line_str[:50]}...")
            
            print(f"   ✅ Stream funcionando")
        else:
            print(f"   ❌ Stream no disponible: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error en stream: {e}")
    
    print(f"\n🏁 Prueba completada")

if __name__ == "__main__":
    test_hikvision_connection()