# engine-prototype/scripts/quick_test.py
#!/usr/bin/env python3
"""Script de prueba rápida para SAST Orchestrator"""

import sys
import os

# Asegurar que PyYAML está instalado
try:
    import yaml
    print("✅ PyYAML está instalado")
except ImportError:
    print("❌ PyYAML no está instalado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
    import yaml

# Configurar el path para importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, "src")

sys.path.insert(0, src_dir)
sys.path.insert(0, project_root)

# Importar SASTOrchestrator
try:
    from src.core.sast_orchestrator import SASTOrchestrator
    print("✅ SASTOrchestrator importado correctamente")
except ImportError as e:
    print(f"❌ Error importando SASTOrchestrator: {e}")
    print(f"📁 Paths de búsqueda:")
    for p in sys.path:
        print(f"  - {p}")
    sys.exit(1)

def test_basic_functionality():
    """Prueba básica de funcionalidad"""
    print("\n🧪 Probando funcionalidad básica...")
    
    # Crear un directorio de prueba temporal
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📁 Directorio de prueba creado: {tmpdir}")
        
        # Crear algunos archivos de prueba
        test_files = {
            "test.py": "import os\ndef insecure():\n    password = 'secret123'\n    os.system(f'echo {password}')\n",
            "test.c": "#include <stdio.h>\nvoid vulnerable() {\n    char buffer[10];\n    gets(buffer);  // Inseguro!\n}\n",
            "test.txt": "Este es un archivo de texto normal.",
        }
        
        for filename, content in test_files.items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  📄 Creado: {filename}")
        
        # Crear orquestador
        print("\n🔧 Creando SASTOrchestrator...")
        orchestrator = SASTOrchestrator(project_root=tmpdir)
        
        # Analizar el directorio
        print("🔍 Ejecutando análisis SAST...")
        try:
            results = orchestrator.analyze_directory(tmpdir)
            
            print(f"✅ Análisis completado")
            print(f"📊 Estadísticas:")
            print(f"  - Archivos analizados: {results['stats']['total_files']}")
            print(f"  - Issues encontrados: {results['stats']['total_issues']}")
            
            if results['issues']:
                print("\n⚠️  Issues detectados:")
                for issue in results['issues'][:5]:  # Mostrar solo los primeros 5
                    print(f"  - [{issue.get('tool', '?')}] {issue.get('severity', '?')}: "
                          f"{issue.get('message', 'Sin mensaje')[:60]}...")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error durante el análisis: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    print("🚀 Iniciando prueba rápida de SASTOrchestrator")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"📁 Script en: {current_dir}")
    
    result = test_basic_functionality()
    
    if result == 0:
        print("\n🎉 ¡Prueba completada exitosamente!")
    else:
        print("\n💥 Prueba fallida")
    
    sys.exit(result)