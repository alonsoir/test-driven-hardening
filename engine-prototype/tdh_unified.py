#!/usr/bin/env python3
"""
TDH Engine - Sistema Unificado de Test-Driven Hardening
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent / "src"))

# Importar desde módulo core
try:
    from core.docker_manager import DockerManager
except ImportError:
    from core.docker_manager_fixed import DockerManagerFixed as DockerManager
from core.sast_pipeline import SASTPipeline, SASTResult
from core.sast_orchestrator import SASTOrchestrator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TDHUnified:
    """Clase principal unificada TDH Engine"""
    
    def __init__(self):
        self.docker_manager = DockerManager()
        self.sast_pipeline = SASTPipeline()
        self.sast_orchestrator = SASTOrchestrator()
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _print_sast_summary(self, sast_result: SASTResult, output_dir: str):
        """Imprimir resumen del análisis SAST"""
        print("\n" + "="*60)
        print("✅ ANÁLISIS SAST COMPLETADO")
        print("="*60)
        print(f"Repositorio: {sast_result.repo_url}")
        print(f"Vulnerabilidades encontradas: {sast_result.total_vulnerabilities}")
        print(f"\nPor severidad:")
        for severity, count in sast_result.by_severity.items():
            print(f"  - {severity.upper()}: {count}")
        print(f"\nPor herramienta:")
        for tool, count in sast_result.by_tool.items():
            print(f"  - {tool}: {count}")
        print(f"\n📄 Resultados guardados en: {output_dir}")
        
        # Mostrar vulnerabilidades críticas
        critical_vulns = [
            v for v in sast_result.vulnerabilities 
            if not v.false_positive and v.severity in ["critical", "high"]
        ]
        
        if critical_vulns:
            print(f"\n🔴 VULNERABILIDADES CRÍTICAS/ALTAS ({len(critical_vulns)}):")
            for i, vuln in enumerate(critical_vulns[:5], 1):
                print(f"\n{i}. [{vuln.severity.upper()}] {vuln.tool}: {vuln.vulnerability_id}")
                print(f"   Archivo: {vuln.file_path}:{vuln.line_number}")
                print(f"   Mensaje: {vuln.message}")
                if vuln.cwe_id:
                    print(f"   CWE: {vuln.cwe_id}")
        
        print("="*60)
    
    async def sast_real(self, repo_url: str, output_dir: str = None):
        """Ejecutar análisis SAST real en un repositorio"""
        if output_dir is None:
            output_dir = str(self.results_dir)
        else:
            output_dir = str(Path(output_dir))
            Path(output_dir).mkdir(exist_ok=True)
        
        logger.info(f"🔍 Iniciando análisis SAST real en: {repo_url}")
        
        try:
            import tempfile
            import subprocess
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                logger.info(f"📦 Clonando repositorio a: {tmp_dir}")
                
                # Clonar repositorio
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, tmp_dir],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"❌ Error clonando repositorio: {result.stderr}")
                    return
                
                # Ejecutar análisis SAST
                logger.info("🛠️  Ejecutando pipeline SAST completo...")
                sast_result = await self.sast_pipeline.run_complete_analysis(tmp_dir)
                
                # Actualizar repo_url en resultado
                sast_result.repo_url = repo_url
                
                # Guardar resultados
                await self.sast_pipeline.save_results(sast_result, output_dir)
                
                # Mostrar resumen
                self._print_sast_summary(sast_result, output_dir)
                
        except Exception as e:
            logger.error(f"❌ Error en análisis SAST: {e}")
            import traceback
            traceback.print_exc()
    
    async def sast_orchestrated(self, repo_url: str, llm_name: str = "claude-3-5"):
        """Ejecutar análisis orquestado completo"""
        logger.info(f"🚀 Ejecutando análisis orquestado para {repo_url}")
        
        result = await self.sast_orchestrator.analyze_repository(repo_url, llm_name)
        
        if result["success"]:
            print("\n" + "="*60)
            print("✅ ANÁLISIS ORQUESTADO COMPLETADO")
            print("="*60)
            print(f"Contenedor: {result.get('container', 'N/A')}")
            print(f"Vulnerabilidades encontradas: {result['sast_result'].total_vulnerabilities}")
            print(f"Output: {result['output_dir']}")
            print("="*60)
            
            # Mostrar recomendaciones para LLM
            if "llm_response" in result:
                print("\n📋 RECOMENDACIONES PARA LLM:")
                for action in result["llm_response"]["recommended_actions"]:
                    print(f"  • {action}")
        else:
            print(f"❌ Error: {result['error']}")
    
    async def docker_prepare(self, llm_name: str, repo_url: str):
        """Preparar contenedor Docker para LLM"""
        logger.info(f"🐳 Preparando contenedor para LLM: {llm_name}")
        
        try:
            container_config = await self.docker_manager.create_isolated_container(
                llm_name, repo_url
            )
            
            print("\n" + "="*60)
            print("✅ CONTENEDOR PREPARADO")
            print("="*60)
            print(f"LLM: {llm_name}")
            print(f"Repositorio: {repo_url}")
            print(f"Contenedor: {container_config.container_name}")
            print(f"Worktree: {container_config.worktree_path}")
            print(f"Estado: ✅ Listo para análisis")
            print("="*60)
            print("\nComandos disponibles:")
            print(f"  docker exec -it {container_config.container_name} bash")
            print(f"  docker logs {container_config.container_name}")
            print("="*60)
            
        except Exception as e:
            logger.error(f"❌ Error preparando contenedor: {e}")
            import traceback
            traceback.print_exc()
    
    async def docker_list(self):
        """Listar contenedores activos"""
        containers = self.docker_manager.list_containers()
        
        if not containers:
            print("📭 No hay contenedores activos")
            return
        
        print("\n" + "="*60)
        print("🐳 CONTENEDORES ACTIVOS TDH")
        print("="*60)
        
        for i, container in enumerate(containers, 1):
            print(f"\n{i}. {container['name']}")
            print(f"   LLM: {container['llm']}")
            print(f"   Repo: {container['repo']}")
            print(f"   Worktree: {container['worktree']}")
        
        print("="*60)
    
    async def docker_cleanup(self, container_name: str = None):
        """Limpiar contenedores"""
        if container_name:
            await self.docker_manager.cleanup_container(container_name)
            print(f"🧹 Contenedor {container_name} limpiado")
        else:
            await self.docker_manager.cleanup_all()
            print("🧹 Todos los contenedores limpiados")
    
    async def build_base_image(self):
        """Construir imagen base Docker"""
        dockerfile_path = os.path.join("docker", "Dockerfile.base")
        
        if not os.path.exists(dockerfile_path):
            logger.error(f"❌ Dockerfile no encontrado: {dockerfile_path}")
            return
        
        import subprocess
        
        print("🔨 Construyendo imagen base TDH...")
        print("Esto puede tomar varios minutos...")
        
        try:
            result = subprocess.run(
                ["docker", "build", "-f", dockerfile_path, "-t", "tdh-base:latest", "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Imagen base construida exitosamente")
                print("Imagen: tdh-base:latest")
            else:
                print(f"❌ Error construyendo imagen: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    async def test_repository(self, repo_url: str = None):
        """Probar el sistema con repositorio de prueba"""
        if repo_url is None:
            repo_url = "https://github.com/alonsoir/test-zeromq-c-.git"
        
        print("\n" + "="*60)
        print("🧪 EJECUTANDO PRUEBA END-TO-END")
        print("="*60)
        print(f"Repositorio: {repo_url}")
        print("="*60)
        
        # Crear directorio para resultados de prueba
        test_results_dir = Path("test-results")
        test_results_dir.mkdir(exist_ok=True)
        
        # 1. Ejecutar análisis SAST
        print("\n1️⃣  Ejecutando análisis SAST...")
        await self.sast_real(repo_url, str(test_results_dir))
        
        # 2. Preparar contenedor para Claude
        print("\n2️⃣  Preparando contenedor para Claude...")
        await self.docker_prepare("claude-3-5", repo_url)
        
        print("\n" + "="*60)
        print("✅ PRUEBA COMPLETADA")
        print("="*60)
        
        # 3. Listar contenedores
        await self.docker_list()

async def main():
    parser = argparse.ArgumentParser(
        description="TDH Engine - Sistema Unificado de Test-Driven Hardening",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s build-base                     # Construir imagen base Docker
  %(prog)s sast-real <repo_url>          # Análisis SAST en repositorio
  %(prog)s sast-orchestrated <repo_url>  # Análisis completo orquestado
  %(prog)s docker-prepare --llm claude --repo <url>  # Preparar contenedor
  %(prog)s docker-list                   # Listar contenedores activos
  %(prog)s test                          # Ejecutar prueba end-to-end
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando: sast-real
    parser_sast = subparsers.add_parser("sast-real", help="Ejecutar análisis SAST real")
    parser_sast.add_argument("repo_url", help="URL del repositorio a analizar")
    parser_sast.add_argument("--output", "-o", default="./results", 
                           help="Directorio de salida (default: ./results)")
    
    # Comando: sast-orchestrated
    parser_orchestrated = subparsers.add_parser("sast-orchestrated", 
                                                help="Ejecutar análisis orquestado completo")
    parser_orchestrated.add_argument("repo_url", help="URL del repositorio a analizar")
    parser_orchestrated.add_argument("--llm", default="claude-3-5",
                                     help="Nombre del LLM (default: claude-3-5)")
    
    # Comando: docker-prepare
    parser_docker = subparsers.add_parser("docker-prepare", 
                                        help="Preparar contenedor Docker")
    parser_docker.add_argument("--llm", required=True, help="Nombre del LLM")
    parser_docker.add_argument("--repo", required=True, help="URL del repositorio")
    
    # Comando: docker-list
    subparsers.add_parser("docker-list", help="Listar contenedores activos")
    
    # Comando: docker-cleanup
    parser_cleanup = subparsers.add_parser("docker-cleanup", 
                                         help="Limpiar contenedores")
    parser_cleanup.add_argument("--name", help="Nombre del contenedor (opcional)")
    
    # Comando: build-base
    subparsers.add_parser("build-base", help="Construir imagen base Docker")
    
    # Comando: test
    parser_test = subparsers.add_parser("test", help="Ejecutar prueba end-to-end")
    parser_test.add_argument("--repo", help="URL del repositorio de prueba")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tdh = TDHUnified()
    
    if args.command == "sast-real":
        await tdh.sast_real(args.repo_url, args.output)
    
    elif args.command == "sast-orchestrated":
        await tdh.sast_orchestrated(args.repo_url, args.llm)
    
    elif args.command == "docker-prepare":
        await tdh.docker_prepare(args.llm, args.repo)
    
    elif args.command == "docker-list":
        await tdh.docker_list()
    
    elif args.command == "docker-cleanup":
        await tdh.docker_cleanup(args.name)
    
    elif args.command == "build-base":
        await tdh.build_base_image()
    
    elif args.command == "test":
        await tdh.test_repository(args.repo)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()