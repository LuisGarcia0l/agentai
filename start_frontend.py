#!/usr/bin/env python3
"""
Script para iniciar solo el frontend React del sistema de trading.
Útil para desarrollo y testing del frontend.
"""

import subprocess
import sys
import time
from pathlib import Path

def start_frontend():
    """Iniciar el servidor de desarrollo React."""
    frontend_path = Path(__file__).parent / "frontend"
    
    if not frontend_path.exists():
        print("❌ Error: Directorio frontend no encontrado")
        return 1
    
    print("=" * 60)
    print("⚛️  INICIANDO FRONTEND REACT")
    print("=" * 60)
    print(f"📁 Directorio: {frontend_path}")
    print("🌐 URL: http://localhost:3000")
    print("=" * 60)
    
    try:
        # Verificar si npm está disponible
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("✅ npm encontrado")
        
        # Verificar si las dependencias están instaladas
        if not (frontend_path / "node_modules").exists():
            print("📦 Instalando dependencias...")
            result = subprocess.run(["npm", "install"], cwd=frontend_path)
            if result.returncode != 0:
                print("❌ Error instalando dependencias")
                return 1
            print("✅ Dependencias instaladas")
        
        # Iniciar servidor de desarrollo
        print("🚀 Iniciando servidor de desarrollo...")
        print("💡 Usa Ctrl+C para detener")
        print("-" * 60)
        
        process = subprocess.run(["npm", "run", "dev"], cwd=frontend_path)
        return process.returncode
        
    except subprocess.CalledProcessError:
        print("❌ Error: npm no está disponible")
        print("💡 Instala Node.js y npm para usar el frontend React")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Frontend detenido")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(start_frontend())