#!/usr/bin/env python3
"""
Script para iniciar solo la API FastAPI del sistema de trading.
Útil para desarrollo y testing de la API.
"""

import subprocess
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from utils.config.settings import settings

def start_api():
    """Iniciar el servidor FastAPI."""
    print("=" * 60)
    print("🚀 INICIANDO API FASTAPI")
    print("=" * 60)
    print(f"🌐 Host: {settings.API_HOST}")
    print(f"🔌 Puerto: {settings.API_PORT}")
    print(f"📚 Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"🔧 Modo: {'Desarrollo' if settings.DEBUG else 'Producción'}")
    print("=" * 60)
    print("💡 Usa Ctrl+C para detener")
    print("-" * 60)
    
    try:
        # Iniciar servidor con uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api.main:app",
            "--host", settings.API_HOST,
            "--port", str(settings.API_PORT),
        ]
        
        if settings.DEBUG:
            cmd.extend(["--reload", "--log-level", "debug"])
        
        process = subprocess.run(cmd)
        return process.returncode
        
    except KeyboardInterrupt:
        print("\n👋 API detenida")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(start_api())