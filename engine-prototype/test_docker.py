#!/usr/bin/env python3
import docker
import os

try:
    # Probar conexión específica para macOS
    docker_socket = os.path.expanduser("~/.docker/run/docker.sock")
    print(f"Socket de Docker: {docker_socket}")
    print(f"¿Existe?: {os.path.exists(docker_socket)}")
    
    if os.path.exists(docker_socket):
        client = docker.DockerClient(base_url=f'unix://{docker_socket}')
    else:
        client = docker.from_env()
    
    # Verificar conexión
    print("Ping a Docker:", client.ping())
    
    # Verificar imágenes
    print("\nImágenes disponibles:")
    for image in client.images.list():
        if image.tags:
            print(f"  - {image.tags[0]}")
    
    print("\n✅ Docker funciona correctamente")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
