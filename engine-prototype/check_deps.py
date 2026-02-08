# engine-prototype/check_deps.py
#!/usr/bin/env python3
"""
Verificador completo de dependencias
"""

import sys
import subprocess

def check_module(module_name, pip_name=None):
    """Verificar si un módulo está instalado"""
    if pip_name is None:
        pip_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError:
        print(f"❌ {module_name} (instalar: pip install {pip_name})")
        return False

def check_system_tool(tool_name, install_cmd=None):
    """Verificar si una herramienta del sistema está instalada"""
    try:
        result = subprocess.run(
            ["which", tool_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {tool_name}")
            return True
        else:
            msg = f"❌ {tool_name}"
            if install_cmd:
                msg += f" (instalar: {install_cmd})"
            print(msg)
            return False
    except:
        print(f"❌ {tool_name} (no se pudo verificar)")
        return False

def main():
    print("🔍 Verificando dependencias del TDH Engine")
    print("=" * 60)
    
    # Módulos de Python
    print("\n📦 MÓDULOS PYTHON:")
    python_modules = [
        ("docker", "docker"),
        ("aiohttp", "aiohttp"),
        ("aiofiles", "aiofiles"),
        ("yaml", "PyYAML"),
        ("pydantic", "pydantic"),
        ("rich", "rich"),
        ("magic", "python-magic"),
        ("git", "gitpython"),
        ("semgrep", "semgrep"),
        ("bandit", "bandit"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("pytest", "pytest"),
        ("httpx", "httpx"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn[standard]"),
    ]
    
    python_ok = True
    for module, pip_name in python_modules:
        if not check_module(module, pip_name):
            python_ok = False
    
    # Herramientas del sistema
    print("\n🔧 HERRAMIENTAS DEL SISTEMA:")
    system_tools = [
        ("docker", "brew install docker (macOS) o apt-get install docker (Linux)"),
        ("git", "brew install git (macOS) o apt-get install git (Linux)"),
        ("cppcheck", "brew install cppcheck (macOS) o apt-get install cppcheck (Linux)"),
        ("flawfinder", "brew install flawfinder (macOS) o apt-get install flawfinder (Linux)"),
    ]
    
    system_ok = True
    for tool, install_cmd in system_tools:
        if not check_system_tool(tool, install_cmd):
            system_ok = False
    
    # Verificar imagen Docker
    print("\n🐳 IMAGEN DOCKER:")
    try:
        result = subprocess.run(
            ["docker", "images", "tdh-base:latest", "--quiet"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print("✅ tdh-base:latest")
        else:
            print("❌ tdh-base:latest (construir con: make build-base)")
            system_ok = False
    except:
        print("❌ No se pudo verificar Docker")
        system_ok = False
    
    print("\n" + "=" * 60)
    
    if python_ok and system_ok:
        print("🎉 ¡Todas las dependencias están instaladas!")
        print("\nPrueba el sistema con:")
        print("  python tdh_unified.py sast-real https://github.com/alonsoir/test-zeromq-c-.git")
        return 0
    else:
        print("⚠️  Hay dependencias faltantes.")
        print("\nInstala las dependencias faltantes y vuelve a ejecutar:")
        print("  pip install -r requirements.txt")
        print("  make build-base")
        return 1

if __name__ == "__main__":
    sys.exit(main())