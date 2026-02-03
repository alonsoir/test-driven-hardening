# engine-prototype/scripts/test_with_vulnerabilities.py
#!/usr/bin/env python3
"""Prueba SAST con archivos vulnerables intencionales"""

import sys
import os
from pathlib import Path

# Configurar paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.sast_orchestrator import SASTOrchestrator

def create_vulnerable_files():
    """Crea archivos con vulnerabilidades para pruebas"""
    test_dir = project_root / "test_vulnerable_files"
    test_dir.mkdir(exist_ok=True)
    
    # 1. Python vulnerable
    py_vuln = test_dir / "vulnerable.py"
    py_vuln.write_text('''
import subprocess
import pickle

# Command injection
def run_cmd(cmd):
    subprocess.call(cmd, shell=True)

# Hardcoded password
PASSWORD = "admin123"

# SQL injection (simulado)
def query(sql):
    return f"SELECT * FROM users WHERE id = {sql}"

# Pickle deserialization
def load(pickled):
    return pickle.loads(pickled)

# Try-except-pass
def risky():
    try:
        x = 1/0
    except:
        pass
''')
    
    # 2. C vulnerable
    c_vuln = test_dir / "vulnerable.c"
    c_vuln.write_text('''
#include <stdio.h>
#include <string.h>

// Buffer overflow vulnerability
void vulnerable() {
    char buffer[10];
    gets(buffer);  // Dangerous!
    printf("Input: %s\\n", buffer);
}

// Format string vulnerability
void print_input(char *input) {
    printf(input);  // Format string vuln
}
''')
    
    # 3. JavaScript vulnerable
    js_vuln = test_dir / "vulnerable.js"
    js_vuln.write_text('''
// Eval vulnerability
function execute(code) {
    eval(code);
}

// InnerHTML vulnerability
function setContent() {
    document.getElementById("div").innerHTML = userInput;
}

// Hardcoded secret
const API_KEY = "sk_live_1234567890abcdef";
''')
    
    return test_dir

def main():
    print("🧪 Prueba SAST con vulnerabilidades intencionales")
    
    # Crear archivos vulnerables
    test_dir = create_vulnerable_files()
    print(f"📁 Archivos vulnerables creados en: {test_dir}")
    
    # Crear orquestador
    orchestrator = SASTOrchestrator(project_root=str(test_dir))
    
    # Analizar cada archivo
    total_issues = 0
    for file_path in test_dir.glob("vulnerable.*"):
        print(f"\n🔍 Analizando: {file_path.name}")
        issues = orchestrator.analyze_file(str(file_path))
        print(f"   📊 Issues encontrados: {len(issues)}")
        
        # Mostrar detalles de los issues
        for i, issue in enumerate(issues[:5], 1):  # Mostrar primeros 5
            print(f"   {i}. [{issue.get('tool')}] {issue.get('severity')}:")
            print(f"      {issue.get('message', '')[:70]}...")
            print(f"      📍 Línea {issue.get('line', '?')}")
        
        total_issues += len(issues)
    
    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"📁 Directorio analizado: {test_dir}")
    print(f"📄 Archivos analizados: {len(list(test_dir.glob('vulnerable.*')))}")
    print(f"⚠️  Issues totales: {total_issues}")
    
    # Limpieza (opcional)
    cleanup = input("\n¿Borrar archivos de prueba? (s/N): ")
    if cleanup.lower() == 's':
        import shutil
        shutil.rmtree(test_dir)
        print("🧹 Archivos de prueba eliminados")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())