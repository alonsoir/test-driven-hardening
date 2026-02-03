# engine-prototype/scripts/test_sast_simple.py
#!/usr/bin/env python3
"""Script de prueba simple y robusto para SAST Orchestrator"""

import sys
import os
from pathlib import Path

# Configurar paths de forma robusta
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent

# Añadir al path
sys.path.insert(0, str(project_root))
if (project_root / 'src').exists():
    sys.path.insert(0, str(project_root / 'src'))

print("🔍 Verificando entorno...")
print(f"📁 Directorio actual: {os.getcwd()}")
print(f"📁 Script en: {current_dir}")
print(f"📁 Project root: {project_root}")

# Verificar dependencias críticas
try:
    import yaml
    print("✅ PyYAML instalado")
except ImportError:
    print("❌ PyYAML no instalado. Instala con: pip install PyYAML")
    sys.exit(1)

# Intentar importar SASTOrchestrator
try:
    from core.sast_orchestrator import SASTOrchestrator
    print("✅ SASTOrchestrator importado")
except ImportError as e:
    print(f"❌ Error importando SASTOrchestrator: {e}")
    print("\n💡 Intentando estructura alternativa...")
    
    # Intentar importación relativa
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "sast_orchestrator",
            project_root / "src" / "core" / "sast_orchestrator.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        SASTOrchestrator = module.SASTOrchestrator
        print("✅ SASTOrchestrator cargado directamente")
    except Exception as e2:
        print(f"❌ Error cargando módulo: {e2}")
        sys.exit(1)

def test_basic():
    """Prueba básica del SASTOrchestrator"""
    print("\n🧪 Probando SASTOrchestrator básico...")
    
    # Directorio de prueba (el directorio actual)
    test_dir = os.getcwd()
    
    try:
        # Crear orquestador
        print(f"🔧 Creando SASTOrchestrator para: {test_dir}")
        orchestrator = SASTOrchestrator(project_root=test_dir)
        
        # Verificar herramientas detectadas
        print(f"\n📊 Herramientas detectadas: {len(orchestrator.available_tools)}")
        
        available_count = 0
        for tool_name, tool_info in orchestrator.available_tools.items():
            if tool_info.get('available', False):
                available_count += 1
                print(f"  ✅ {tool_name}: {tool_info.get('command')}")
            else:
                print(f"  ❌ {tool_name}: NO disponible")
        
        if available_count == 0:
            print("⚠️  ¡No hay herramientas disponibles! Instala al menos semgrep:")
            print("   pip install semgrep")
            return 1
        
        # Crear un archivo de prueba simple
        test_file = Path(test_dir) / "test_sast_example.py"
        test_content = '''# Archivo de prueba para SAST
import os
import subprocess

def insecure_function(user_input):
    # Vulnerabilidad de inyección de comandos
    subprocess.call(f"echo {user_input}", shell=True)
    
def hardcoded_password():
    password = "supersecret123"  # Hardcoded password
    return password

def test_main():
    user_input = input("Enter your name: ")
    insecure_function(user_input)
    
if __name__ == "__main__":
    test_main()
'''
        
        print(f"\n📝 Creando archivo de prueba: {test_file.name}")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Analizar el archivo de prueba
        print(f"🔍 Analizando archivo de prueba...")
        issues = orchestrator.analyze_file(str(test_file))
        
        print(f"📊 Issues encontrados: {len(issues)}")
        
        if issues:
            print("\n⚠️  Issues detectados:")
            for i, issue in enumerate(issues[:5], 1):
                tool = issue.get('tool', 'unknown')
                severity = issue.get('severity', 'UNKNOWN')
                message = issue.get('message', '')[:80]
                line = issue.get('line', 0)
                print(f"  {i}. [{tool}] {severity} (línea {line}): {message}")
        else:
            print("✅ No se encontraron issues (puede que las herramientas no estén configuradas correctamente)")
        
        # Limpiar
        if test_file.exists():
            test_file.unlink()
            print(f"\n🧹 Archivo de prueba eliminado")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Función principal"""
    print("🚀 Iniciando prueba simple de SAST")
    
    result = test_basic()
    
    if result == 0:
        print("\n✅ Prueba completada exitosamente")
    else:
        print("\n❌ Prueba fallida")
    
    return result

if __name__ == "__main__":
    sys.exit(main())