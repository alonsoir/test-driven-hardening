# tdh_engine.py (en la raíz de engine-prototype)
#!/usr/bin/env python3
"""
TDH Engine - Command Line Interface
Punto de entrada principal para el Test Driven Hardening Engine
"""

import sys
import argparse
from pathlib import Path

# Añadir src al path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from core.sast_integration import SASTScanner
from core.workspace import WorkspaceManager, create_test_workspace
from core.scorer import FixScorer  # To be implemented
from council.mock import MockCouncil  # To be implemented


def analyze_command(args):
    """Comando: Analizar un repositorio"""
    print(f"🔍 Analyzing: {args.target}")
    
    # Inicializar scanner
    scanner = SASTScanner()
    
    try:
        # Escanear
        vulns = scanner.scan(args.target)
        
        # Mostrar resultados
        print(f"\n📊 Found {len(vulns)} vulnerabilities")
        
        stats = scanner.get_stats(vulns)
        for severity, count in stats['by_severity'].items():
            print(f"  {severity}: {count}")
        
        # Mostrar vulnerabilidades críticas
        critical = [v for v in vulns if v.severity == 'CRITICAL']
        if critical:
            print(f"\n🚨 Critical vulnerabilities ({len(critical)}):")
            for i, vuln in enumerate(critical[:5], 1):
                print(f"  {i}. {vuln.message}")
                print(f"     Location: {vuln.path}:{vuln.line}")
                if vuln.cwe:
                    print(f"     CWE: {vuln.cwe}")
                print()
        
        # Si hay vulnerabilidades y se solicita demo
        if critical and args.demo:
            print("🎭 Starting TDH demo with first critical vulnerability...")
            # Aquí iría la lógica completa del TDH
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def demo_command(args):
    """Comando: Ejecutar demo con ejemplos predefinidos"""
    print("🎭 TDH Engine - Demo Mode")
    
    # Crear workspace de prueba
    if args.example == "buffer_overflow":
        code = """
#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // CWE-120: Buffer overflow
    printf("%s\n", buffer);
}
"""
        workspace = create_test_workspace(code, "c")
        print(f"✅ Created test workspace: {workspace.id}")
        print(f"   Path: {workspace.path}")
        print(f"   Code: C buffer overflow example")
        
        # Aquí continuaría el flujo TDH completo
        
    elif args.example == "sql_injection":
        code = """
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # CWE-89: SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    return cursor.fetchone()
"""
        workspace = create_test_workspace(code, "python")
        print(f"✅ Created test workspace: {workspace.id}")
        
    else:
        print(f"❌ Unknown example: {args.example}")
        print("   Available examples: buffer_overflow, sql_injection")
        return 1
    
    return 0


def version_command(args):
    """Comando: Mostrar versión"""
    print("TDH Engine v0.1.0 (Community Edition)")
    print("Test Driven Hardening Prototype")
    print("University of Extremadura Alumni Research Project")
    return 0


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="TDH Engine - Test Driven Hardening Prototype",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tdh_engine analyze /path/to/repo          # Analyze a repository
  tdh_engine demo --example buffer_overflow # Run demo with example
  tdh_engine --version                      # Show version
        
For more information, see README.md
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Comando: analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a repository')
    analyze_parser.add_argument('target', help='Path or URL to analyze')
    analyze_parser.add_argument('--demo', action='store_true', 
                               help='Run TDH demo on found vulnerabilities')
    analyze_parser.add_argument('--severity', default='CRITICAL',
                               choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
                               help='Minimum severity to show')
    
    # Comando: demo
    demo_parser = subparsers.add_parser('demo', help='Run TDH demo with examples')
    demo_parser.add_argument('--example', default='buffer_overflow',
                            choices=['buffer_overflow', 'sql_injection'],
                            help='Example to demonstrate')
    
    # Comando: version
    subparsers.add_parser('version', help='Show version information')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Ejecutar comando correspondiente
    try:
        if args.command == 'analyze':
            return analyze_command(args)
        elif args.command == 'demo':
            return demo_command(args)
        elif args.command == 'version':
            return version_command(args)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())