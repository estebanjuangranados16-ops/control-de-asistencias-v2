#!/usr/bin/env python3
"""
Script de prueba directa del dispositivo Hikvision
"""

import requests
from requests.auth import HTTPDigestAuth
import json
import time

def test_device_direct():
    """Probar conexión directa al dispositivo"""
    device_ip = "172.10.0.66"
    username = "admin"
    password = "PC2024*+"
    
    session = requests.Session()
    session.auth = HTTPDigestAuth(username, password)
    
    print("Probando conexion al dispositivo...")
    
    # Probar info del dispositivo
    try:
        response = session.get(f"http://{device_ip}/ISAPI/System/deviceInfo", timeout=5)
        if response.status_code == 200:
            print("✓ Dispositivo conectado")
            try:
                info = response.json()
                print(f"  Modelo: {info.get('DeviceInfo', {}).get('model', 'N/A')}")
                print(f"  Version: {info.get('DeviceInfo', {}).get('firmwareVersion', 'N/A')}")
            except:
                print("  Info basica obtenida")
        else:
            print(f"✗ Error de conexion: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Probar stream de eventos
    print("\nProbando stream de eventos (10 segundos)...")
    try:
        url = f"http://{device_ip}/ISAPI/Event/notification/alertStream"
        response = session.get(url, stream=True, timeout=15)
        
        if response.status_code == 200:
            print("✓ Stream conectado - esperando eventos...")
            
            start_time = time.time()
            buffer = ""
            event_count = 0
            
            for chunk in response.iter_content(chunk_size=1024):
                if time.time() - start_time > 10:  # 10 segundos
                    break
                    
                if chunk:
                    try:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        buffer += chunk_str
                        
                        # Buscar eventos JSON
                        while '{' in buffer and '}' in buffer:
                            start = buffer.find('{')
                            if start == -1:
                                break
                                
                            brace_count = 0
                            end = start
                            
                            for i in range(start, len(buffer)):
                                if buffer[i] == '{':
                                    brace_count += 1
                                elif buffer[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end = i
                                        break
                            
                            if brace_count == 0:
                                json_str = buffer[start:end+1]
                                buffer = buffer[end+1:]
                                
                                try:
                                    event = json.loads(json_str)
                                    event_count += 1
                                    
                                    # Mostrar evento
                                    if 'AccessControllerEvent' in event:
                                        acs = event['AccessControllerEvent']
                                        sub_type = acs.get('subEventType')
                                        emp_id = acs.get('employeeNoString', 'N/A')
                                        timestamp = event.get('dateTime', 'N/A')
                                        
                                        if sub_type == 38:
                                            print(f"  ✓ ACCESO AUTORIZADO - ID: {emp_id} - {timestamp}")
                                        elif sub_type == 39:
                                            print(f"  ✗ ACCESO DENEGADO - ID: {emp_id} - {timestamp}")
                                        else:
                                            print(f"  ? Evento tipo {sub_type} - ID: {emp_id}")
                                    else:
                                        print(f"  • Evento: {list(event.keys())}")
                                        
                                except json.JSONDecodeError:
                                    pass
                            else:
                                break
                                
                    except Exception as e:
                        continue
            
            print(f"\n✓ Prueba completada - {event_count} eventos detectados")
            if event_count == 0:
                print("  Nota: No se detectaron eventos. Prueba poner la huella durante la prueba.")
            
        else:
            print(f"✗ Error en stream: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error en stream: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Prueba Directa del Dispositivo Hikvision")
    print("=" * 45)
    
    success = test_device_direct()
    
    print("\n" + "=" * 45)
    if success:
        print("Dispositivo funcionando correctamente")
        print("Ahora puedes ejecutar: python system_optimized.py")
    else:
        print("Revisar conexion del dispositivo")
        print("Verificar IP, usuario y contraseña")