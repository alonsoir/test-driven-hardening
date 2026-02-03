# engine-prototype/scripts/diagnose_sast.py
#!/usr/bin/env python3
"""Script de diagnóstico para SAST Orchestrator"""

import sys
import os
from pathlib import Path

print("🔍 Diagnóstico de SASTOrchestrator")
print("="*50)

# 1. Verificar Python y paths
print("\n1. Configuración de Python:")
print(f"   Python: {sys.executable}")
print(f"   Versión: {sys.version}")
print(f"   Paths: {sys.path[:3]}...")

# 2. Verificar archivo sast_orchestrator.py
print("\n2. Verificando archivo sast_orchestrator.py:")
sast_path = Path(__file__).parent.parent / 'src' / 'core' / 'sast_orchestrator.py'
if sast_path.exists():
    print(f"   ✅ Existe en: {sast_path}")
    
    # Verificar contenido
    with open(sast_path, 'r') as f:
        content = f.read()
    
    # Buscar métodos clave
    key_methods = ['class SASTOrchestrator', 'def _detect_available_tools', 'def __init__']
    for method in key_methods:
        if method in content:
            print(f"   ✅ Contiene: {method}")
        else:
            print(f"   ❌ FALTA: {method}")
else:
    print(f"   ❌ No existe: {sast_path}")

# 3. Verificar dependencias
print("\n3. Verificando dependencias:")
try:
    import yaml
    print("   ✅ PyYAML instalado")
except ImportError:
    print("   ❌ PyYAML NO instalado")

try:
    import xml.etree.ElementTree as ET
    print("   ✅ xml.etree.ElementTree disponible")
except ImportError:
    print("   ❌ xml.etree.ElementTree NO disponible")

# 4. Intentar importar directamente
print("\n4. Intentando importar SASTOrchestrator:")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("sast_orchestrator", sast_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("   ✅ Módulo cargado correctamente")
    
    # Verificar clase
    if hasattr(module, 'SASTOrchestrator'):
        print("   ✅ Clase SASTOrchestrator encontrada")
        
        # Verificar métodos
        methods_to_check = ['_detect_available_tools', '__init__', 'analyze_file']
        for method in methods_to_check:
            if hasattr(module.SASTOrchestrator, method):
                print(f"   ✅ Método {method} encontrado")
            else:
                print(f"   ❌ Método {method} NO encontrado")
    else:
        print("   ❌ Clase SASTOrchestrator NO encontrada")
        
except Exception as e:
    print(f"   ❌ Error cargando módulo: {e}")

print("\n" + "="*50)
print("💡 Si hay errores, intenta recrear sast_orchestrator.py con:")
print("cat > src/core/sast_orchestrator.py << 'EOF'")
print("[código completo]")
print("EOF")