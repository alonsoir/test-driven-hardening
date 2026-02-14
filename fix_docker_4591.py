#!/usr/bin/env python3
"""
Fix para Docker Desktop 4.59.1 en macOS
"""

import os
import subprocess
import sys

def run_command(cmd):
    """Ejecutar comando y devolver resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

print("🔧 Fix para Docker Desktop 4.59.1 en macOS")
print("="*60)

# 1. Verificar Docker Desktop
print("\n1. Verificando Docker Desktop...")
docker_ok, version, _ = run_command("docker --version")
if docker_ok:
    print(f"✅ {version}")
else:
    print("❌ Docker no encontrado")
    sys.exit(1)

# 2. Verificar socket Docker
print("\n2. Verificando socket Docker...")
docker_socket = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(docker_socket):
    print(f"✅ Socket encontrado: {docker_socket}")
    print(f"   Permisos: {oct(os.stat(docker_socket).st_mode)[-3:]}")
else:
    print(f"❌ Socket no encontrado: {docker_socket}")
    print("   Docker Desktop no está corriendo o está mal configurado")

# 3. Verificar variable DOCKER_HOST
print("\n3. Verificando variable DOCKER_HOST...")
docker_host = os.environ.get('DOCKER_HOST')
if docker_host:
    print(f"⚠️  DOCKER_HOST está configurada: {docker_host}")
    print("   Esto puede causar problemas en macOS 4.59.1")
    print("   Recomendación: unset DOCKER_HOST")
else:
    print("✅ DOCKER_HOST no está configurada (correcto)")

# 4. Soluciones
print("\n" + "="*60)
print("🛠️  SOLUCIONES PARA DOCKER DESKTOP 4.59.1:")
print("\nOpción A: Configurar Docker Desktop:")
print("  1. Abre Docker Desktop")
print("  2. Ve a Settings → General")
print("  3. DESMARCAR 'Use Docker Compose V2'")
print("  4. Marcar 'Expose daemon on tcp://localhost:2375 without TLS'")
print("  5. Clic en 'Apply & Restart'")

print("\nOpción B: Configurar manualmente:")
print("  export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock")
print("  o")
print("  export DOCKER_HOST=tcp://localhost:2375")

print("\nOpción C: Reiniciar Docker Desktop completamente:")
print("  1. Cierra Docker Desktop (click derecho en ícono → Quit)")
print("  2. Ejecuta: killall Docker")
print("  3. Ejecuta: rm -f ~/.docker/run/docker.sock")
print("  4. Abre Docker Desktop de nuevo")
print("  5. Espera 60 segundos")

print("\n" + "="*60)
print("📋 Para probar después de los cambios:")
print("  docker ps")
print("  python -c \"import docker; print(docker.from_env().ping())\"")
