#!/usr/bin/env python3
"""
⚛️ AI Trading System - Frontend Starter

Script para iniciar el frontend React de forma independiente.
Se conecta al backend API para obtener datos.

Author: Luis (AI Trading System)
Version: 2.0.0
"""

import subprocess
import sys
import time
from pathlib import Path
import requests

from utils.config.settings import settings


def check_backend_health():
    """Verificar si el backend está ejecutándose."""
    try:
        response = requests.get(f"http://{settings.API_HOST}:{settings.API_PORT}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_frontend():
    """Iniciar el frontend React."""
    frontend_path = Path(__file__).parent / "frontend"
    
    if not frontend_path.exists():
        print("❌ Error: Directorio frontend no encontrado")
        print("   Asegúrate de que el directorio 'frontend' existe")
        return 1
    
    print("=" * 80)
    print("⚛️ AI TRADING SYSTEM - FRONTEND REACT v2.0")
    print("=" * 80)
    print("Iniciando frontend React independiente")
    print(f"Backend API: http://{settings.API_HOST}:{settings.API_PORT}")
    print("=" * 80)
    
    # Verificar si el backend está ejecutándose
    print("🔍 Verificando conexión con backend...")
    if check_backend_health():
        print("✅ Backend API está ejecutándose")
    else:
        print("⚠️  Backend API no está disponible")
        print("   Asegúrate de ejecutar 'python backend_main.py' primero")
        print("   El frontend funcionará pero sin datos en tiempo real")
    
    print("=" * 80)
    
    try:
        # Verificar si npm está disponible
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("📦 npm encontrado")
        
        # Verificar si las dependencias están instaladas
        if not (frontend_path / "node_modules").exists():
            print("📦 Instalando dependencias de npm...")
            result = subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
            if result.returncode != 0:
                print("❌ Error instalando dependencias")
                return 1
            print("✅ Dependencias instaladas")
        
        print("🚀 Iniciando servidor de desarrollo React...")
        print("   Frontend estará disponible en: http://localhost:3000")
        print("   Usa Ctrl+C para detener")
        print("=" * 80)
        
        # Iniciar servidor de desarrollo
        subprocess.run(["npm", "run", "dev"], cwd=frontend_path)
        
    except subprocess.CalledProcessError:
        print("❌ Error: npm no está disponible")
        print("   Instala Node.js y npm para ejecutar el frontend")
        return 1
    except FileNotFoundError:
        print("❌ Error: npm no encontrado")
        print("   Instala Node.js y npm para ejecutar el frontend")
        return 1
    except KeyboardInterrupt:
        print("\n👋 ¡Frontend detenido!")
        return 0
    except Exception as e:
        print(f"❌ Error iniciando frontend: {e}")
        return 1
    
    return 0


def main():
    """Función principal."""
    return start_frontend()


if __name__ == "__main__":
    exit(main())