# engine-prototype/scripts/test_sast.py (versión corregida)
#!/usr/bin/env python3
"""
Script de prueba para SAST Orchestrator
Usa: source venv/bin/activate && python scripts/test_sast.py .
"""

import sys
import os
import subprocess
from pathlib import Path

def check_and_install_deps():
    """Verifica e instala dependencias si es necesario"""
    try:
        import yaml
        print("✅ PyYAML está disponible")
        return True
    except ImportError:
        print("❌ PyYAML no encontrado. Por favor activa el entorno virtual:")
        print("   source venv/bin/activate")
        print("   pip install PyYAML")
        
        # Preguntar si queremos intentar instalar
        response = input("\n¿Quieres que intente instalar PyYAML en el entorno virtual? (s/N): ")
        if response.lower() == 's':
            try:
                venv_python = Path(__file__).parent.parent / 'venv' / 'bin' / 'python'
                if venv_python.exists():
                    subprocess.run([str(venv_python), "-m", "pip", "install", "PyYAML"], check=True)
                    print("✅ PyYAML instalado. Por favor ejecuta de nuevo el script.")
                else:
                    print("❌ Entorno virtual no encontrado. Ejecuta:")
                    print("   cd engine-prototype && python3 -m venv venv")
                    print("   source venv/bin/activate")
                    print("   pip install PyYAML")
            except subprocess.CalledProcessError:
                print("❌ Error instalando PyYAML")
        return False

# Verificar dependencias
if not check_and_install_deps():
    sys.exit(1)

# Configurar paths de importación
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Añadir al path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.core.sast_orchestrator import SASTOrchestrator
    print("✅ SASTOrchestrator importado correctamente")
except ImportError as e:
    print(f"❌ Error importando SASTOrchestrator: {e}")
    print("\n💡 Posibles soluciones:")
    print("1. Asegúrate de estar en el entorno virtual: source venv/bin/activate")
    print("2. Verifica la estructura de directorios")
    print("3. Ejecuta desde el directorio correcto: cd engine-prototype")
    sys.exit(1)

def main():
    """Función principal"""
    print("🧪 Probando SAST Orchestrator")
    print(f"📁 Directorio actual: {os.getcwd()}")
    
    # Directorio a analizar
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = str(project_root)
    
    print(f"🔍 Analizando directorio: {target_dir}")
    
    # Verificar que existe
    if not os.path.exists(target_dir):
        print(f"❌ Directorio no existe: {target_dir}")
        return 1
    
    try:
        # Crear orquestador
        orchestrator = SASTOrchestrator(project_root=target_dir)
        
        # Ejecutar análisis
        results = orchestrator.analyze_directory(target_dir)
        
        # Mostrar resultados
        print(f"\n✅ Análisis completado")
        print(f"📄 Archivos analizados: {results['stats']['total_files']}")
        print(f"⚠️  Issues encontrados: {results['stats']['total_issues']}")
        
        if results['report_path'] and results['report_path'] != 'console':
            print(f"📊 Reporte generado: {results['report_path']}")
        
        # Mostrar issues por severidad
        if results['stats'].get('issues_by_severity'):
            print("\n📊 Issues por severidad:")
            for severity, count in sorted(results['stats']['issues_by_severity'].items()):
                print(f"  {severity}: {count}")
        
        # Mostrar issues por herramienta
        if results['stats'].get('issues_by_tool'):
            print("\n🛠️  Issues por herramienta:")
            for tool, count in sorted(results['stats']['issues_by_tool'].items()):
                print(f"  {tool}: {count}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())