import docker
import logging
import os
import secrets
import sys
import time
import shutil
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

@dataclass
class ContainerConfig:
    """Configuración para contenedores Docker"""
    llm_name: str
    repo_url: str
    worktree_path: str
    container_name: str
    cpu_limit: float = 1.0
    memory_limit: str = "512m"
    network_enabled: bool = True
    auto_remove: bool = True

    def to_dict(self):
        return asdict(self)

class DockerManager:
    """Gestor de contenedores Docker para análisis TDH - Versión macOS"""
    
    def __init__(self, config_path: str = None):
        try:
            # FORMA SEGURA PARA macOS: usar from_env() sin especificar socket
            # Docker SDK debería detectar automáticamente
            logger.info("Conectando a Docker via from_env()...")
            self.client = docker.from_env()
            
            # Verificar que funciona
            self.client.ping()
            logger.info("✅ Conectado a Docker correctamente")
            
        except Exception as e:
            logger.error(f"❌ No se pudo conectar a Docker: {e}")
            logger.info("\n💡 Para macOS, asegúrate de:")
            logger.info("1. Docker Desktop esté corriendo")
            logger.info("2. En Docker Desktop: Settings → General")
            logger.info("   → Marcar 'Expose daemon on tcp://localhost:2375 without TLS'")
            logger.info("3. Luego cerrar y abrir Docker Desktop")
            sys.exit(1)
        
        self.active_containers: Dict[str, ContainerConfig] = {}
    
    async def create_isolated_container(self, llm_name: str, repo_url: str) -> ContainerConfig:
        """Crear contenedor aislado para un LLM específico"""
        
        container_name = f"tdh-{llm_name}-{secrets.token_hex(4)}"
        worktree_path = f"/tmp/tdh-volumes/{container_name}"
        
        # Crear directorio
        os.makedirs(worktree_path, exist_ok=True)
        logger.info(f"📁 Volumen creado: {worktree_path}")
        
        try:
            # Usar containers.run sin parámetros complejos
            logger.info(f"🐳 Creando contenedor {container_name}...")
            
            container = self.client.containers.run(
                image="tdh-base:latest",
                name=container_name,
                volumes={worktree_path: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir="/workspace",
                detach=True,
                tty=True,
                stdin_open=True,
                environment={
                    "LLM_NAME": llm_name,
                    "REPO_URL": repo_url,
                    "PYTHONUNBUFFERED": "1"
                },
                # En macOS, a veces es mejor no especificar límites
                # mem_limit="512m",
                # cpu_quota=50000,
                auto_remove=False
            )
            
            # Esperar a que el contenedor se inicie completamente
            logger.info("⏳ Esperando a que el contenedor se inicie...")
            time.sleep(3)
            
            # Clonar repositorio
            logger.info(f"📦 Clonando repositorio {repo_url}...")
            exit_code, output = container.exec_run(
                f"git clone {repo_url} /workspace/repo",
                workdir="/workspace"
            )
            
            if exit_code != 0:
                error_msg = output.decode() if output else "Sin mensaje de error"
                raise Exception(f"Error clonando repositorio: {error_msg}")
            
            logger.info(f"✅ Repositorio clonado")
            
            # Instalar dependencias básicas
            await self._install_dependencies(container)
            
            # Crear y devolver la configuración del contenedor
            config = ContainerConfig(
                llm_name=llm_name,
                repo_url=repo_url,
                worktree_path=worktree_path,
                container_name=container_name
            )
            
            self.active_containers[container_name] = config
            logger.info(f"✅ Contenedor creado exitosamente: {container_name}")
            
            return config
            
        except Exception as e:
            logger.error(f"❌ Error creando contenedor: {e}")
            # Limpieza en caso de error
            await self.cleanup_container(container_name)
            raise
    
    async def _install_dependencies(self, container):
        """Instalar dependencias básicas del proyecto"""
        try:
            # Verificar si es proyecto Python
            exit_code, _ = container.exec_run(
                "test -f /workspace/repo/requirements.txt",
                workdir="/workspace"
            )
            
            if exit_code == 0:
                logger.info("⚙️ Instalando dependencias Python...")
                container.exec_run(
                    "pip install -r /workspace/repo/requirements.txt",
                    workdir="/workspace"
                )
            
        except Exception as e:
            logger.warning(f"No se pudieron instalar dependencias: {e}")
    
    async def cleanup_container(self, container_name: str):
        """Limpiar contenedor"""
        try:
            # Detener y remover contenedor
            try:
                container = self.client.containers.get(container_name)
                container.stop(timeout=10)
                container.remove()
            except:
                pass
            
            # Eliminar directorio de trabajo
            if container_name in self.active_containers:
                config = self.active_containers[container_name]
                if os.path.exists(config.worktree_path):
                    shutil.rmtree(config.worktree_path, ignore_errors=True)
                
                # Remover de lista activa
                del self.active_containers[container_name]
            
            logger.info(f"🧹 Contenedor limpiado: {container_name}")
            
        except Exception as e:
            logger.warning(f"Error limpiando contenedor: {e}")
    
    async def cleanup_all(self):
        """Limpiar todos los contenedores activos"""
        containers_to_clean = list(self.active_containers.keys())
        for container_name in containers_to_clean:
            await self.cleanup_container(container_name)
    
    def list_containers(self) -> List[Dict[str, Any]]:
        """Listar contenedores activos"""
        return [
            {
                "name": config.container_name,
                "llm": config.llm_name,
                "repo": config.repo_url,
                "worktree": config.worktree_path
            }
            for config in self.active_containers.values()
        ]
