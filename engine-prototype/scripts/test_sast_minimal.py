# engine-prototype/scripts/test_sast_minimal.py
#!/usr/bin/env python3
"""Script de prueba mínima para SAST Orchestrator"""

import sys
import os
from pathlib import Path

# Configurar paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.core.sast_orchestrator import SASTOrchestrator
    print("✅ SASTOrchestrator importado correctamente")
except Exception as e:
    print(f"❌ Error importando: {e}")
    sys.exit(1)

def main():
    print("🧪 Prueba mínima de SASTOrchestrator")
    
    # Crear instancia
    try:
        orchestrator = SASTOrchestrator(project_root=str(project_root))
        print("✅ SASTOrchestrator creado")
        
        # Verificar herramientas detectadas
        print(f"\n🔧 Herramientas detectadas: {len(orchestrator.available_tools)}")
        for tool_name, tool_info in orchestrator.available_tools.items():
            status = "✅" if tool_info.get('available') else "❌"
            print(f"  {status} {tool_name}: {tool_info.get('command')}")
        
        # Probar con un archivo específico
        test_file = project_root / "scripts" / "test_sast_minimal.py"
        if test_file.exists():
            print(f"\n🔍 Probando análisis en: {test_file.name}")
            issues = orchestrator.analyze_file(str(test_file))
            print(f"📊 Issues encontrados: {len(issues)}")
            
            if issues:
                for i, issue in enumerate(issues[:3], 1):
                    print(f"  {i}. [{issue.get('tool')}] {issue.get('severity')}: {issue.get('message')[:60]}...")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())