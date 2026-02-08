# engine-prototype/diagnose.py
#!/usr/bin/env python3
"""
Diagnóstico de problemas de importación
"""

import sys
import os

# Asegurar que estamos en el directorio correcto
print(f"Directorio actual: {os.getcwd()}")
print(f"Python path: {sys.executable}")

# Intentar importar cada módulo
modules = [
    'aiofiles',
    'aiohttp',
    'docker',
    'yaml',
    'pydantic',
    'git',
    'semgrep',
    'bandit',
]

print("\n🔍 Probando importaciones...")
for module in modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")

# Verificar estructura de directorios
print("\n📁 Verificando estructura...")
required_dirs = [
    'src/core',
    'docker',
    'config',
]
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"✅ {dir_path}/")
    else:
        print(f"❌ {dir_path}/ (no existe)")

# Verificar archivos clave
required_files = [
    'src/core/__init__.py',
    'src/core/sast_pipeline.py',
    'src/core/docker_manager.py',
    'tdh_unified.py',
    'requirements.txt',
]
for file_path in required_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} (no existe)")