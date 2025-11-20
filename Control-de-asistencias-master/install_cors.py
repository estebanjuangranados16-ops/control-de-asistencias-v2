#!/usr/bin/env python3
"""
Instalar flask-cors
"""

import subprocess
import sys

def install_cors():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-cors"])
        print("✅ flask-cors instalado correctamente")
    except subprocess.CalledProcessError:
        print("❌ Error al instalar flask-cors")

if __name__ == "__main__":
    install_cors()