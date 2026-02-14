# engine-prototype/test_docker_api.py
#!/usr/bin/env python3
"""
Probar la API actual de Docker SDK
"""

import docker
import json

def test_docker_api():
    """Probar diferentes formas de crear contenedores"""
    
    client = docker.from_env()
    
    print("🔍 Probando API de Docker SDK")
    print("="*50)
    
    # 1. Verificar versión del SDK
    print(f"📦 Docker SDK versión: {docker.__version__}")
    
    # 2. Probar crear un contenedor simple
    print("\n🧪 Probando creación de contenedor...")
    
    try:
        # Método 1: Usando containers.run (más simple)
        print("\nMétodo 1: containers.run()")
        container = client.containers.run(
            "alpine:latest",
            "echo 'Hello from Docker!'",
            name="test-container-1",
            detach=True,
            remove=True,
            mem_limit="128m"
        )
        print(f"✅ Contenedor creado: {container.id}")
        container.remove(force=True)
        
    except Exception as e:
        print(f"❌ Error método 1: {e}")
    
    try:
        # Método 2: Usando containers.create
        print("\nMétodo 2: containers.create()")
        container = client.containers.create(
            image="alpine:latest",
            name="test-container-2",
            command="echo 'Hello'",
            host_config=client.api.create_host_config(
                mem_limit="128m",
                auto_remove=True
            )
        )
        print(f"✅ Contenedor creado: {container.id}")
        container.remove()
        
    except Exception as e:
        print(f"❌ Error método 2: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
    
    try:
        # Método 3: Con HostConfig de docker.types
        print("\nMétodo 3: docker.types.HostConfig")
        from docker.types import HostConfig
        
        host_config = HostConfig(
            mem_limit="128m",
            auto_remove=True
        )
        
        container = client.containers.create(
            image="alpine:latest",
            name="test-container-3",
            command="echo 'Hello'",
            host_config=host_config
        )
        print(f"✅ Contenedor creado: {container.id}")
        container.remove()
        
    except Exception as e:
        print(f"❌ Error método 3: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
    
    print("\n" + "="*50)
    print("✅ Prueba de API completada")

if __name__ == "__main__":
    test_docker_api()