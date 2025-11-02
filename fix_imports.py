#!/usr/bin/env python3
"""
🔧 Script para arreglar imports del logger en todos los archivos
"""

import os
import re
from pathlib import Path

def fix_logger_imports(file_path):
    """Arreglar imports del logger en un archivo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar imports del logger
        old_import = r'from utils\.logging\.logger import ([^\n]+)'
        
        if re.search(old_import, content):
            print(f"🔧 Arreglando {file_path}")
            
            # Reemplazar con import seguro
            new_import = '''# Importar logger con fallback
try:
    from utils.logging.logger import \\1
except ImportError:
    from utils.logging.simple_logger import \\1'''
            
            content = re.sub(old_import, new_import, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
    except Exception as e:
        print(f"❌ Error procesando {file_path}: {e}")
        return False
    
    return False

def main():
    """Procesar todos los archivos Python."""
    print("🔧 Arreglando imports del logger...")
    
    # Buscar todos los archivos Python
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Ignorar directorios específicos
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    fixed_count = 0
    for file_path in python_files:
        if fix_logger_imports(file_path):
            fixed_count += 1
    
    print(f"✅ Arreglados {fixed_count} archivos")
    print("🎉 Ahora puedes ejecutar: python3 main.py")

if __name__ == "__main__":
    main()