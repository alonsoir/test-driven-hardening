# engine-prototype/scripts/test_full_analysis.py
#!/usr/bin/env python3
"""Prueba completa del análisis SAST"""

import sys
from pathlib import Path

# Configurar paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.sast_orchestrator import SASTOrchestrator

def main():
    print("🚀 Prueba completa del análisis SAST")
    
    # Directorios de prueba (puedes cambiarlos)
    test_dirs = [
        project_root / "scripts",
        project_root / "src",
        project_root
    ]
    
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        
        print(f"\n{'='*60}")
        print(f"ANALIZANDO: {test_dir}")
        print(f"{'='*60}")
        
        try:
            orchestrator = SASTOrchestrator(project_root=str(test_dir))
            results = orchestrator.analyze_directory(str(test_dir))
            
            print(f"✅ Análisis completado para {test_dir}")
            print(f"📊 Estadísticas:")
            print(f"  - Archivos: {results['stats']['total_files']}")
            print(f"  - Issues: {results['stats']['total_issues']}")
            
            # Mostrar issues por severidad
            if results['stats'].get('issues_by_severity'):
                print(f"  - Por severidad:")
                for sev, count in results['stats']['issues_by_severity'].items():
                    print(f"    * {sev}: {count}")
            
            # Mostrar issues por herramienta
            if results['stats'].get('issues_by_tool'):
                print(f"  - Por herramienta:")
                for tool, count in results['stats']['issues_by_tool'].items():
                    print(f"    * {tool}: {count}")
            
            # Guardar reporte si se generó
            if results['report_path'] and results['report_path'] != 'console':
                print(f"📄 Reporte guardado en: {results['report_path']}")
            
        except Exception as e:
            print(f"❌ Error analizando {test_dir}: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 Todas las pruebas completadas")
    return 0

if __name__ == "__main__":
    sys.exit(main())