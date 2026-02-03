# engine-prototype/scripts/test_sast_focused.py
#!/usr/bin/env python3
"""Script de prueba enfocado para SAST Orchestrator"""

import sys
import os
from pathlib import Path

# Configurar paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.sast_orchestrator import SASTOrchestrator

def test_with_specific_files():
    """Prueba con archivos específicos en lugar de todo el directorio"""
    print("🎯 Prueba enfocada de SAST Orchestrator")
    
    # Crear orquestador
    orchestrator = SASTOrchestrator(project_root=str(project_root))
    
    # Archivos específicos para probar
    test_files = [
        project_root / "scripts" / "test_sast.py",
        project_root / "src" / "core" / "sast_orchestrator.py",
        project_root / "config" / "sast_tools.yaml",
        project_root / "config" / "tdh_config.yaml",
    ]
    
    # Buscar algunos archivos .py y .c adicionales
    py_files = list(project_root.glob("*.py"))
    c_files = list(project_root.glob("*.c"))
    
    # Añadir algunos archivos de ejemplo (máximo 2 de cada tipo)
    test_files.extend(py_files[:2])
    test_files.extend(c_files[:2])
    
    # Filtrar solo los que existen
    test_files = [f for f in test_files if f.exists()]
    
    print(f"📄 Analizando {len(test_files)} archivos específicos")
    
    all_issues = []
    for file_path in test_files:
        rel_path = file_path.relative_to(project_root)
        print(f"\n🔍 Analizando: {rel_path}")
        
        try:
            issues = orchestrator.analyze_file(str(file_path))
            print(f"   📊 Issues encontrados: {len(issues)}")
            
            # Mostrar los primeros 2 issues de cada archivo
            for i, issue in enumerate(issues[:2], 1):
                tool = issue.get('tool', 'unknown')
                severity = issue.get('severity', 'UNKNOWN')
                message = issue.get('message', '')[:60]
                print(f"   {i}. [{tool}] {severity}: {message}...")
            
            all_issues.extend(issues)
            
        except Exception as e:
            print(f"   ❌ Error analizando {rel_path}: {e}")
    
    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN DEL ANÁLISIS")
    print(f"{'='*60}")
    print(f"📄 Archivos analizados: {len(test_files)}")
    print(f"⚠️  Issues totales: {len(all_issues)}")
    
    if all_issues:
        # Agrupar por severidad
        by_severity = {}
        by_tool = {}
        
        for issue in all_issues:
            severity = issue.get('severity', 'UNKNOWN')
            tool = issue.get('tool', 'UNKNOWN')
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_tool[tool] = by_tool.get(tool, 0) + 1
        
        print("\n📊 Issues por severidad:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO', 'UNKNOWN']:
            if severity in by_severity:
                print(f"  {severity}: {by_severity[severity]}")
        
        print("\n🛠️  Issues por herramienta:")
        for tool, count in sorted(by_tool.items()):
            print(f"  {tool}: {count}")
        
        # Mostrar algunos issues críticos
        critical_issues = [i for i in all_issues if i.get('severity') in ['CRITICAL', 'HIGH']]
        if critical_issues:
            print(f"\n⛔ Issues CRÍTICOS/ALTOS encontrados ({len(critical_issues)}):")
            for i, issue in enumerate(critical_issues[:3], 1):
                print(f"  {i}. {issue.get('message', '')[:80]}...")
                print(f"     📍 {issue.get('file', '')}:{issue.get('line', 0)}")

def main():
    """Función principal"""
    print("🧪 Iniciando prueba enfocada de SAST")
    print(f"📁 Directorio del proyecto: {project_root}")
    
    try:
        test_with_specific_files()
        return 0
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())