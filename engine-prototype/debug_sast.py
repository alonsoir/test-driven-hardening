# engine-prototype/debug_sast.py
#!/usr/bin/env python3
"""
Depuración del pipeline SAST
"""

import subprocess
import sys
import tempfile
import os

def test_tool(tool_name, test_command, test_file_content=None):
    """Probar una herramienta específica"""
    print(f"\n🔍 Probando {tool_name}...")
    
    # Crear archivo temporal de prueba si se proporciona contenido
    test_path = None
    if test_file_content:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(test_file_content)
            test_path = f.name
    
    try:
        # Ejecutar comando
        if test_path and '{file}' in test_command:
            cmd = test_command.format(file=test_path)
        else:
            cmd = test_command
        
        print(f"Comando: {cmd}")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        
        if result.returncode in [0, 1]:  # 0=éxito, 1=hallazgos
            print(f"✅ {tool_name} funciona")
            print(f"Salida: {result.stdout[:200]}...")
            return True
        else:
            print(f"❌ {tool_name} falló (código: {result.returncode})")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando {tool_name}: {e}")
        return False
    finally:
        # Limpiar archivo temporal
        if test_path and os.path.exists(test_path):
            os.unlink(test_path)

def main():
    print("🧪 DEPURACIÓN HERRAMIENTAS SAST")
    print("="*60)
    
    # Contenido de prueba C con vulnerabilidad
    test_c_code = """
#include <stdio.h>
#include <string.h>

void vulnerable_function(char *input) {
    char buffer[10];
    strcpy(buffer, input);  // Vulnerabilidad: buffer overflow
}

int main() {
    char large_input[50] = "This is a very long input that will cause overflow";
    vulnerable_function(large_input);
    return 0;
}
    """
    
    # Contenido de prueba Python con vulnerabilidad
    test_py_code = """
import subprocess
import os

def vulnerable():
    user_input = input("Enter command: ")
    # Vulnerabilidad: ejecución de comandos
    subprocess.call(user_input, shell=True)
    
def another_vulnerability():
    password = "secret123"  # Vulnerabilidad: contraseña hardcodeada
    print(password)
    
if __name__ == "__main__":
    vulnerable()
    """
    
    # Probar herramientas
    tools = [
        ("cppcheck", f"cppcheck --enable=all --inconclusive {{file}}", test_c_code),
        ("bandit", f"bandit -f json {{file}}", test_py_code),
        ("semgrep", f"semgrep --config auto --json {{file}}", test_c_code),
        ("flawfinder", f"flawfinder {{file}}", test_c_code),
    ]
    
    all_ok = True
    for tool_name, command, test_content in tools:
        if not test_tool(tool_name, command, test_content):
            all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ Todas las herramientas funcionan correctamente")
        return 0
    else:
        print("❌ Algunas herramientas tienen problemas")
        print("\n💡 Instala las herramientas faltantes:")
        print("  brew install cppcheck flawfinder")
        print("  pip install bandit semgrep")
        return 1

if __name__ == "__main__":
    sys.exit(main())