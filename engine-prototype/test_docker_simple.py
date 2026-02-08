#!/usr/bin/env python3
"""
Prueba de conexión a Docker en macOS
"""

import docker
import os
import sys

print("🔍 Probando conexión Docker en macOS...")
print("="*50)

# Método 1: from_env() simple
print("\n1. Probando docker.from_env()...")
try:
    client = docker.from_env()
    print(f"   ✅ Conectado")
    print(f"   Versión API: {client.version()['ApiVersion']}")
    print(f"   Ping: {client.ping()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Método 2: Verificar DOCKER_HOST
print("\n2. Verificando variable DOCKER_HOST...")
docker_host = os.getenv('DOCKER_HOST')
if docker_host:
    print(f"   DOCKER_HOST={docker_host}")
    try:
        client = docker.DockerClient(base_url=docker_host)
        print(f"   ✅ Conectado via DOCKER_HOST")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("   DOCKER_HOST no está configurada")

# Método 3: Probar socket común de macOS
print("\n3. Probando socket común de macOS...")
sockets = [
    'unix:///var/run/docker.sock',
    'unix:///Users/aironman/.docker/run/docker.sock',
    'tcp://localhost:2375'
]

for socket in sockets:
    try:
        print(f"   Probando {socket}...")
        client = docker.DockerClient(base_url=socket, timeout=2)
        client.ping()
        print(f"   ✅ Conectado via {socket}")
        break
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("💡 Si nada funciona, en Docker Desktop:")
print("   Settings → General → Expose daemon on tcp://localhost:2375 without TLS")
