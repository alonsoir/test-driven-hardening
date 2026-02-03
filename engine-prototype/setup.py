# engine-prototype/setup.py
#!/usr/bin/env python3
"""Setup script para TDH Engine"""

import subprocess
import sys

def install_dependencies():
    """Instala las dependencias necesarias"""
    dependencies = [
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
        "xmltodict>=0.13.0",
    ]
    
    print("📦 Instalando dependencias...")
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"  ✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"  ❌ Error instalando {dep}")
    
    print("\n🎉 Dependencias instaladas.")

if __name__ == "__main__":
    install_dependencies()