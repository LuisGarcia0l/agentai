#!/usr/bin/env python3
"""
🚀 AI Trading System v2.0 - System Starter

Script para iniciar el sistema completo refactorizado.
Permite elegir entre backend solo, frontend solo, o ambos.

Author: Luis (AI Trading System)
Version: 2.0.0
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path


def print_banner():
    """Mostrar banner del sistema."""
    print("=" * 80)
    print("🤖 AI TRADING SYSTEM v2.0 - ARQUITECTURA REFACTORIZADA")
    print("=" * 80)
    print("✅ Backend: Python + FastAPI (Puerto 8000)")
    print("✅ Frontend: React + TypeScript (Puerto 3000)")
    print("✅ Arquitectura separada y escalable")
    print("=" * 80)


def start_backend():
    """Iniciar solo el backend."""
    print("🐍 Iniciando Backend (Python + FastAPI)...")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/api/health")
    print("-" * 40)
    
    try:
        # Usar el backend de prueba si el principal falla
        try:
            subprocess.run([sys.executable, "backend_main.py"], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("⚠️  Usando backend de prueba...")
            subprocess.run([sys.executable, "test_backend.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Backend detenido!")
    except Exception as e:
        print(f"❌ Error iniciando backend: {e}")
        return 1
    
    return 0


def start_frontend():
    """Iniciar solo el frontend."""
    print("⚛️ Iniciando Frontend (React + TypeScript)...")
    print("   App: http://localhost:3000")
    print("   Conecta con API en: http://localhost:8000")
    print("-" * 40)
    
    try:
        subprocess.run([sys.executable, "frontend_main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Frontend detenido!")
    except Exception as e:
        print(f"❌ Error iniciando frontend: {e}")
        return 1
    
    return 0


def start_both():
    """Iniciar backend y frontend."""
    print("🚀 Iniciando sistema completo...")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:3000")
    print("-" * 40)
    
    try:
        # Iniciar backend en background
        backend_process = subprocess.Popen([sys.executable, "test_backend.py"])
        
        # Esperar un poco para que el backend inicie
        time.sleep(3)
        
        # Iniciar frontend
        frontend_process = subprocess.Popen([sys.executable, "frontend_main.py"])
        
        print("✅ Sistema iniciado!")
        print("   Usa Ctrl+C para detener ambos servicios")
        
        # Esperar a que terminen
        try:
            backend_process.wait()
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema...")
            backend_process.terminate()
            frontend_process.terminate()
            backend_process.wait()
            frontend_process.wait()
            print("👋 Sistema detenido!")
            
    except Exception as e:
        print(f"❌ Error iniciando sistema: {e}")
        return 1
    
    return 0


def show_status():
    """Mostrar estado del sistema."""
    print("📊 ESTADO DEL SISTEMA")
    print("-" * 40)
    
    # Verificar archivos principales
    files_to_check = [
        ("backend_main.py", "🐍 Backend principal"),
        ("test_backend.py", "🧪 Backend de prueba"),
        ("frontend_main.py", "⚛️ Frontend starter"),
        ("frontend/package.json", "📦 Frontend config"),
        ("api/main.py", "🔌 API endpoints"),
        ("requirements_backend.txt", "📋 Backend deps"),
        ("README_REFACTORED.md", "📖 Documentación")
    ]
    
    for file_path, description in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - FALTA")
    
    print("-" * 40)
    print("🔗 URLs importantes:")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Frontend: http://localhost:3000")
    print("   Health Check: http://localhost:8000/api/health")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="AI Trading System v2.0 - System Starter"
    )
    parser.add_argument(
        "mode",
        choices=["backend", "frontend", "both", "status"],
        help="Modo de inicio: backend, frontend, both, o status"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.mode == "backend":
        return start_backend()
    elif args.mode == "frontend":
        return start_frontend()
    elif args.mode == "both":
        return start_both()
    elif args.mode == "status":
        show_status()
        return 0
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
        exit(0)