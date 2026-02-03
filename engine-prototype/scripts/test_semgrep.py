#!/usr/bin/env python3
import subprocess
import json
import sys

print("🧪 Probando semgrep...")
result = subprocess.run(['semgrep', '--version'], capture_output=True, text=True)
print(f"Versión: {result.stdout}")

# Probar con un archivo simple
test_code = '''
# test_vulnerable.py
import subprocess
def insecure():
    user_input = input("Enter command: ")
    subprocess.call(user_input, shell=True)  # Inseguro!
'''

with open('test_vulnerable.py', 'w') as f:
    f.write(test_code)

result = subprocess.run(['semgrep', '--config', 'auto', '--json', 'test_vulnerable.py'], 
                       capture_output=True, text=True)

if result.returncode in [0, 1]:
    data = json.loads(result.stdout)
    print(f"✅ semgrep funciona. Encontrados {len(data.get('results', []))} issues")
    for finding in data.get('results', []):
        print(f"  - {finding.get('check_id')}: {finding.get('extra', {}).get('message')}")
else:
    print(f"❌ Error: {result.stderr}")

import os
if os.path.exists('test_vulnerable.py'):
    os.remove('test_vulnerable.py')
