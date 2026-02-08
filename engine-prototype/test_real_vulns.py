# engine-prototype/test_real_vulns.py
#!/usr/bin/env python3
"""
Prueba TDH Engine con repositorios reales con vulnerabilidades
"""

import asyncio
import sys
from tdh_unified import TDHUnified

# Lista de repositorios reales con vulnerabilidades
REAL_VULN_REPOS = [
    ("https://github.com/WebGoat/WebGoat.git", "java", "WebGoat - Java"),
    ("https://github.com/digininja/DVWA.git", "php", "DVWA - PHP"),
    ("https://github.com/hardik05/Damn_Vulnerable_C_Program.git", "c", "Vulnerable C Program"),
    ("https://github.com/justinsteven/dostackbufferoverflowgood.git", "c", "Buffer Overflow Examples"),
    ("https://github.com/alonsoir/test-zeromq-c-.git", "cpp", "ZeroMQ Test (sin vulnerabilidades conocidas)"),
]

async def test_all_repos():
    """Probar todos los repositorios"""
    tdh = TDHUnified()
    
    for repo_url, language, description in REAL_VULN_REPOS:
        print(f"\n{'='*60}")
        print(f"🔍 Probando: {description}")
        print(f"   URL: {repo_url}")
        print(f"   Lenguaje: {language}")
        print(f"{'='*60}")
        
        try:
            await tdh.sast_real(repo_url, f"./results/{language}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await asyncio.sleep(2)  # Esperar entre pruebas

async def main():
    print("🧪 TDH Engine - Prueba con repositorios vulnerables reales")
    print("="*60)
    
    await test_all_repos()
    
    print("\n" + "="*60)
    print("✅ Pruebas completadas")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())