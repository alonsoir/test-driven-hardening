# examples/buffer_overflow/demo.py
"""
TDH Engine - Demo Completo Sin APIs de Pago
"""
from src.orchestrator import TDHEngine
from src.council.deepseek_local import DeepSeekLocalProvider

# 1. Configurar engine con proveedor gratuito
engine = TDHEngine(providers=[DeepSeekLocalProvider()])

# 2. Analizar vulnerabilidad de ejemplo
vuln_code = """
#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // CWE-120: Buffer overflow
    printf("%s\n", buffer);
}
"""

# 3. Ejecutar análisis completo
result = engine.analyze_and_fix(
    code=vuln_code,
    vulnerability_type="CWE-120",
    language="c"
)

# 4. Mostrar resultados
print(f"Puntuación del fix: {result.score}/100")
print(f"Fix propuesto:\n{result.fixed_code}")