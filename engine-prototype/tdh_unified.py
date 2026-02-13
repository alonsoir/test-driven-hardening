#!/usr/bin/env python3
"""
TDH Engine - Sistema Unificado de Test-Driven Hardening
Versión con orquestación multi‑SOTA, worktrees y generación automática de PRs.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Cargar variables de entorno desde .env
from dotenv import load_dotenv

# Agregar src al path
sys.path.append(str(Path(__file__).parent / "src"))

# Importar módulos del core
try:
    from core.docker_manager import DockerManager
except ImportError:
    # Fallback para compatibilidad
    from core.docker_manager_fixed import DockerManagerFixed as DockerManager

# Nuevo orquestador (refactorizado)
from core.sast_orchestrator import SASTOrchestrator

# Pipeline SAST legacy (aún usado para análisis inicial)
from core.sast_pipeline import SASTPipeline, SASTResult

# ----------------------------------------------------------------------
# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
class TDHUnified:
    """Clase principal unificada TDH Engine"""

    def __init__(self):
        # Cargar .env automáticamente
        load_dotenv()

        self.docker_manager = DockerManager()
        self.sast_pipeline = SASTPipeline()
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

        # El nuevo orquestador se instancia bajo demanda

    # ------------------------------------------------------------------
    # Métodos legacy (con advertencia de deprecación)
    # ------------------------------------------------------------------
    async def docker_prepare(self, llm_name: str, repo_url: str):
        """
        [DEPRECADO] Prepara un contenedor persistente para depuración.
        Use el nuevo flujo 'sast-orchestrated' para análisis real.
        """
        logger.warning("⚠️  'docker-prepare' está obsoleto y será eliminado en futuras versiones.")
        logger.warning("    Para depuración manual, considere usar 'docker-shell' (próximamente).")

        try:
            container_config = await self.docker_manager.create_isolated_container(
                llm_name, repo_url
            )
            print("\n" + "=" * 60)
            print("🐳 CONTENEDOR LEGACY CREADO (solo depuración)")
            print("=" * 60)
            print(f"LLM: {llm_name}")
            print(f"Repositorio: {repo_url}")
            print(f"Contenedor: {container_config.container_name}")
            print(f"Worktree: {container_config.worktree_path}")
            print("\nComandos útiles:")
            print(f"  docker exec -it {container_config.container_name} bash")
            print(f"  docker logs {container_config.container_name}")
            print("=" * 60)
        except Exception as e:
            logger.error(f"❌ Error preparando contenedor: {e}")
            import traceback
            traceback.print_exc()

    async def docker_list(self):
        """Lista contenedores activos (legacy)."""
        containers = self.docker_manager.list_containers()
        if not containers:
            print("📭 No hay contenedores activos")
            return
        print("\n" + "=" * 60)
        print("🐳 CONTENEDORES ACTIVOS (legacy)")
        print("=" * 60)
        for i, c in enumerate(containers, 1):
            print(f"\n{i}. {c['name']}")
            print(f"   LLM: {c['llm']}")
            print(f"   Repo: {c['repo']}")
            print(f"   Worktree: {c['worktree']}")
        print("=" * 60)

    async def docker_cleanup(self, container_name: Optional[str] = None):
        """Limpia contenedores legacy."""
        if container_name:
            await self.docker_manager.cleanup_container(container_name)
            print(f"🧹 Contenedor {container_name} limpiado")
        else:
            await self.docker_manager.cleanup_all()
            print("🧹 Todos los contenedores legacy limpiados")

    # ------------------------------------------------------------------
    # Métodos del pipeline SAST (legacy, aún útiles)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # NUEVO: Orquestación multi‑SOTA
    # ------------------------------------------------------------------
    async def sast_orchestrated(
        self,
        repo_url: str,
        council: Optional[List[str]] = None,
        dry_run: bool = False
    ):
        """
        Ejecuta orquestación multi‑SOTA completa:
        - Análisis SAST
        - Filtrado HIGH/CRITICAL
        - Creación de worktrees por vulnerabilidad/SOTA
        - Lanzamiento de contenedores efímeros con sota_agent.py
        - Monitorización de estados vía logs
        - Generación automática de Pull Requests (si dry_run=False y GITHUB_TOKEN presente)
        """
        logger.info("=" * 60)
        logger.info(f"🚀 ORQUESTACIÓN MULTI‑SOTA para {repo_url}")
        logger.info("=" * 60)

        # Instanciar el nuevo orquestador
        orchestrator = SASTOrchestrator()

        try:
            result = await orchestrator.orchestrate(
                repo_url=repo_url,
                council_filter=council,
                dry_run=dry_run
            )
            if result is None:
                result = {
                    "total_tasks": 0,
                    "completed": 0,
                    "failed": 0,
                    "pr_created": 0,
                    "prs": [],
                    "tasks": []
                }
        except Exception as e:
            logger.exception("Error fatal en orquestación")
            print(f"❌ Error: {e}")
            return

        # ------------------------------------------------------------------
        # Mostrar resumen
        print("\n" + "=" * 60)
        print("📊 REPORTE DE ORQUESTACIÓN")
        print("=" * 60)
        print(f"Total tareas:          {result['total_tasks']}")
        print(f"Completadas:           {result['completed']}")
        print(f"Fallidas:              {result['failed']}")
        print(f"Pull Requests creadas: {result['pr_created']}")

        if result.get('prs'):
            print("\n🔗 Pull Requests:")
            for pr in result['prs']:
                print(f"  - {pr['pr_url']}")

        if result.get('tasks'):
            print("\n📋 Detalle por tarea:")
            for task in result['tasks']:
                estado = task['state']
                icon = "✅" if estado == "completed" else "❌" if estado == "failed" else "⏳"
                print(f"  {icon} [{task['model']}] {task['vuln_id']} - {task['cwe']} -> {estado}")
                if task.get('pr_url'):
                    print(f"       PR: {task['pr_url']}")
                if task.get('error'):
                    print(f"       Error: {task['error']}")

        print("=" * 60)

        # ------------------------------------------------------------------
        # Guardar reporte detallado en JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"orchestration_{timestamp}.json"
        with open(report_file, "w") as f:
            # Convertir objetos no serializables (Path, datetime) a string
            json.dump(result, f, indent=2, default=str)
        print(f"\n📄 Reporte detallado guardado en: {report_file}")

        return result

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    async def build_base_image(self):
        """Construye la imagen Docker base (tdh-base:latest)."""
        dockerfile_path = Path("docker") / "Dockerfile.base"
        if not dockerfile_path.exists():
            logger.error(f"❌ Dockerfile no encontrado: {dockerfile_path}")
            return

        import subprocess
        print("🔨 Construyendo imagen base TDH... (puede tomar varios minutos)")
        try:
            subprocess.run(
                ["docker", "build", "-f", str(dockerfile_path), "-t", "tdh-base:latest", "."],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Imagen base construida exitosamente: tdh-base:latest")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error construyendo imagen: {e.stderr}")

    async def test_repository(self, repo_url: Optional[str] = None):
        """Prueba end‑to‑end del pipeline completo."""
        if repo_url is None:
            repo_url = "https://github.com/alonsoir/test-zeromq-c-.git"

        print("\n" + "=" * 60)
        print("🧪 PRUEBA END‑TO‑END (SAST + orquestación)")
        print("=" * 60)
        print(f"Repositorio: {repo_url}")
        print("=" * 60)

        # 1. Ejecutar SAST y guardar resultados
        test_results_dir = Path("test-results")
        test_results_dir.mkdir(exist_ok=True)
        await self.sast_real(repo_url, str(test_results_dir))

        # 2. Ejecutar orquestación multi‑SOTA en modo dry-run (para pruebas)
        print("\n2️⃣  Ejecutando orquestación multi‑SOTA (dry-run)...")
        await self.sast_orchestrated(repo_url, dry_run=True)

        print("\n" + "=" * 60)
        print("✅ PRUEBA COMPLETADA")
        print("=" * 60)


# ----------------------------------------------------------------------
async def main():
    # Cargar variables de entorno al inicio
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="TDH Engine - Test-Driven Hardening",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s build-base                     # Construir imagen base
  %(prog)s sast-real <repo_url>          # Solo análisis SAST
  %(prog)s sast-orchestrated <repo_url>  # Análisis + fixes + PRs
  %(prog)s docker-prepare --llm claude --repo <url>  # [DEPRECADO]
  %(prog)s docker-list                   # Contenedores legacy
  %(prog)s test                         # Prueba end-to-end
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos")

    # ------------------------------------------------------------------
    # Comando: sast-real (análisis SAST puro)
    parser_sast = subparsers.add_parser("sast-real", help="Análisis SAST sin LLMs")
    parser_sast.add_argument("repo_url", help="URL del repositorio")
    parser_sast.add_argument("--output", "-o", default="./results",
                             help="Directorio de salida")

    # ------------------------------------------------------------------
    # Comando: sast-orchestrated (NUEVO FLUJO PRINCIPAL)
    parser_orch = subparsers.add_parser(
        "sast-orchestrated",
        help="Orquestación multi‑SOTA: worktrees, contenedores, PRs"
    )
    parser_orch.add_argument("repo_url", help="URL del repositorio")
    parser_orch.add_argument(
        "--council",
        nargs="+",
        help="Modelos a usar (ej. claude-3-5-sonnet gpt-4-turbo). Por defecto todos."
    )
    parser_orch.add_argument(
        "--dry-run",
        action="store_true",
        help="No crear PRs ni hacer push, solo simular"
    )

    # ------------------------------------------------------------------
    # Comandos legacy Docker (deprecados)
    parser_docker = subparsers.add_parser(
        "docker-prepare",
        help="[DEPRECADO] Preparar contenedor persistente para depuración"
    )
    parser_docker.add_argument("--llm", required=True, help="Nombre del LLM")
    parser_docker.add_argument("--repo", required=True, help="URL del repositorio")

    subparsers.add_parser("docker-list", help="[DEPRECADO] Listar contenedores legacy")
    parser_cleanup = subparsers.add_parser("docker-cleanup", help="[DEPRECADO] Limpiar contenedores legacy")
    parser_cleanup.add_argument("--name", help="Nombre del contenedor (opcional)")

    # ------------------------------------------------------------------
    # Comando: build-base
    subparsers.add_parser("build-base", help="Construir imagen base Docker")

    # ------------------------------------------------------------------
    # Comando: test
    parser_test = subparsers.add_parser("test", help="Prueba end-to-end completa")
    parser_test.add_argument("--repo", help="URL del repositorio de prueba")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tdh = TDHUnified()

    # ------------------------------------------------------------------
    # Dispatch de comandos
    if args.command == "sast-real":
        await tdh.sast_real(args.repo_url, args.output)

    elif args.command == "sast-orchestrated":
        await tdh.sast_orchestrated(args.repo_url, args.council, args.dry_run)

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