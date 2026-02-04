# test_unified_system.py
#!/usr/bin/env python3
"""
Script de prueba para el sistema unificado TDH
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_basic_functionality():
    """Prueba básica del sistema unificado"""
    
    print("🧪 Probando sistema unificado TDH...")
    
    # 1. Probar que los módulos se importan correctamente
    try:
        from core.sast_orchestrator import SASTOrchestrator
        from integration.unified_analyzer import UnifiedAnalyzer
        print("✅ Módulos importados correctamente")
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    
    # 2. Probar SASTOrchestrator básico
    try:
        orchestrator = SASTOrchestrator('.')
        print(f"✅ SASTOrchestrator creado, herramientas: {len(orchestrator.available_tools)}")
    except Exception as e:
        print(f"❌ Error creando SASTOrchestrator: {e}")
        return False
    
    # 3. Probar UnifiedAnalyzer
    try:
        analyzer = UnifiedAnalyzer()
        print("✅ UnifiedAnalyzer creado correctamente")
    except Exception as e:
        print(f"❌ Error creando UnifiedAnalyzer: {e}")
        return False
    
    # 4. Probar análisis de archivo simple
    test_file = Path(__file__).parent / 'test_sample.py'
    test_file.write_text('''
import os
import subprocess

# Código vulnerable de ejemplo
def vulnerable_function(user_input):
    # Vulnerabilidad: command injection
    os.system(f"echo {user_input}")
    
    # Vulnerabilidad: shell=True
    subprocess.run(f"ls {user_input}", shell=True)
    
    # Contraseña hardcodeada
    password = "supersecret123"
    return password
''')
    
    try:
        issues = orchestrator.analyze_file(str(test_file))
        print(f"✅ Análisis SAST completado: {len(issues)} issues encontrados")
        
        for issue in issues[:3]:  # Mostrar primeros 3
            print(f"  - {issue.get('tool')}: {issue.get('severity')} - {issue.get('message')[:50]}...")
            
    except Exception as e:
        print(f"❌ Error en análisis SAST: {e}")
    finally:
        # Limpiar archivo de prueba
        if test_file.exists():
            test_file.unlink()
    
    print("\n" + "="*60)
    print("✅ Pruebas básicas completadas")
    print("="*60)
    
    return True

if __name__ == '__main__':
    success = test_basic_functionality()
    sys.exit(0 if success else 1)