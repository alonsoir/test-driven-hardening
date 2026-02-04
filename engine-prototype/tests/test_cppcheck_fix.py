# test_cppcheck_fix.py
import sys
sys.path.append('src')
from core.sast_orchestrator import SASTOrchestrator

# Crear archivo C vulnerable
with open('test_vuln.c', 'w') as f:
    f.write("""
#include <string.h>
int main() {
    char buf[10];
    strcpy(buf, "too long string");
    return 0;
}
""")

orchestrator = SASTOrchestrator('.')
print("🔧 Herramientas disponibles:", orchestrator.available_tools)

if 'cppcheck' in orchestrator.available_tools:
    print("\n🔍 Probando cppcheck...")
    issues = orchestrator.analyze_file('test_vuln.c')
    print(f"📊 Issues encontrados: {len(issues)}")
    for issue in issues:
        print(f"  - {issue.get('severity')}: {issue.get('message')}")
else:
    print("❌ cppcheck no disponible")