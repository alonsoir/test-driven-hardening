#!/usr/bin/env python3
"""
Orquestador SAST Multi‑SOTA con Worktrees y Pull Requests.
Carga credenciales desde un archivo .env para mayor seguridad.
"""

import asyncio
import json
import logging
import os
import re
import sys
import uuid
import yaml
import subprocess
import tempfile
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

# Intentamos importar dotenv, si no está instalado, avisamos al usuario
try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: La librería 'python-dotenv' es necesaria. Instálala con: pip install python-dotenv")
    sys.exit(1)

from github import Github
import docker

# Importar pipeline SAST
from core.sast_pipeline import SASTPipeline

# Cargar variables de entorno desde el archivo .env en la raíz
load_dotenv()

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes y Configuración de Secretos
# ----------------------------------------------------------------------
COUNCIL_CONFIG_PATH = Path("config/llm_council.yaml")
DEFAULT_BASE_IMAGE = "tdh-base:latest"
GITHUB_TOKEN_KEY = "GITHUB_TOKEN"
OPENROUTER_API_KEY = "OPENROUTER_API_KEY"

# ----------------------------------------------------------------------
# Modelo de Vulnerabilidad
# ----------------------------------------------------------------------
@dataclass
class Vulnerability:
    id: str
    file: str
    line: int
    description: str
    severity: str
    rule_id: Optional[str] = None
    additional_properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_sast_result(cls, result_dict: Dict) -> Optional["Vulnerability"]:
        """Extrae una vulnerabilidad del formato de SASTResult (legacy)."""
        try:
            return cls(
                id=result_dict.get("cwe", result_dict.get("id", "unknown")),
                file=result_dict.get("file", ""),
                line=result_dict.get("line", 0),
                description=result_dict.get("message", ""),
                severity=result_dict.get("severity", "unknown").upper(),
                rule_id=result_dict.get("rule_id"),
                additional_properties=result_dict
            )
        except Exception as e:
            logger.warning(f"No se pudo extraer vulnerabilidad: {e}")
            return None

# ----------------------------------------------------------------------
# Máquina de Estados
# ----------------------------------------------------------------------
class TaskState(Enum):
    PENDING = "pending"
    WORKTREE_CREATED = "worktree_created"
    CONTAINER_STARTED = "container_started"
    TEST_DESIGNING = "test_designing"
    FIX_DESIGNING = "fix_designing"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"
    PR_CREATED = "pr_created"

    @classmethod
    def from_log(cls, log_line: str) -> Optional["TaskState"]:
        match = re.search(r'\[STATE:(\w+)\]', log_line)
        if match:
            state_str = match.group(1).lower()
            for state in cls:
                if state.value == state_str:
                    return state
        return None

# ----------------------------------------------------------------------
# Modelo de Tarea
# ----------------------------------------------------------------------
@dataclass
class SOTATask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    vulnerability: Vulnerability = None
    model_key: str = ""
    model_display: str = ""
    worktree_path: Path = None
    container_name: str = ""
    state: TaskState = TaskState.PENDING
    result: Dict[str, Any] = field(default_factory=dict)
    pr_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_state(self, new_state: TaskState):
        self.state = new_state
        self.updated_at = datetime.now()
        logger.info(f"[TASK:{self.task_id}] Estado → {new_state.value}")

# ----------------------------------------------------------------------
# Orquestador Principal
# ----------------------------------------------------------------------
class SASTOrchestrator:
    def __init__(self, council_path: Path = COUNCIL_CONFIG_PATH):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

        # Cargar configuración del consejo
        self.council_config = self._load_council_config(council_path)
        self.llm_configs = self.council_config.get("llm_configs", {})
        self.orchestrator_config = self.council_config.get("orchestrator", {})

        # Secretos
        self.github_token = os.getenv(GITHUB_TOKEN_KEY)
        self.openrouter_key = os.getenv(OPENROUTER_API_KEY)

        self._validate_secrets()

        self.tasks: Dict[str, SOTATask] = {}
        self.active_containers: Set[str] = set()
        self.docker_client = docker.from_env()

    def _validate_secrets(self):
        missing = []
        if not self.github_token:
            missing.append(GITHUB_TOKEN_KEY)
        if not self.openrouter_key:
            missing.append(OPENROUTER_API_KEY)
        if missing:
            logger.error(f"❌ Faltan secretos en .env: {', '.join(missing)}")
        else:
            logger.info("🔐 Secretos cargados correctamente")

    def _load_council_config(self, path: Path) -> Dict:
        if not path.exists():
            logger.warning(f"Archivo {path} no encontrado. Usando valores por defecto.")
            return {}
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error cargando {path}: {e}")
            return {}

    def _get_authenticated_repo_url(self, repo_url: str) -> str:
        """
        Si hay token de GitHub, lo inyecta en la URL para autenticación.
        Retorna la URL original si no hay token o la URL ya contiene credenciales.
        """
        if not self.github_token:
            return repo_url
        # Solo modificar URLs https
        if repo_url.startswith("https://"):
            # Insertar token antes del @ o al principio
            if "@" in repo_url:
                # Ya tiene credenciales, no sobrescribir
                return repo_url
            # Insertar token
            return repo_url.replace("https://", f"https://{self.github_token}@")
        return repo_url

    async def _run_sast(self, repo_url: str) -> List[Vulnerability]:
        """
        Ejecuta análisis SAST sobre el repositorio y retorna lista de vulnerabilidades
        en el formato esperado por el orquestador (objetos Vulnerability de este módulo).
        """
        logger.info(f"🔍 Ejecutando análisis SAST en {repo_url}")
        
        # Usar URL autenticada para clonar (si el repo es privado)
        auth_url = self._get_authenticated_repo_url(repo_url)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger.info(f"📦 Clonando repositorio a {tmp_dir}")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", auth_url, tmp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Error clonando repositorio: {e.stderr}")
                return []
            
            # Ejecutar pipeline SAST
            sast_pipeline = SASTPipeline()
            sast_result = await sast_pipeline.run_complete_analysis(tmp_dir)
            
            # Convertir resultados al formato de Vulnerability del orquestador
            vulnerabilities = []
            for vuln in sast_result.vulnerabilities:
                if vuln.false_positive:
                    continue
                # Crear objeto Vulnerability (definido en este módulo)
                orch_vuln = Vulnerability(
                    id=vuln.vulnerability_id,
                    file=vuln.file_path,
                    line=vuln.line_number,
                    description=vuln.message,
                    severity=vuln.severity.upper(),
                    rule_id=vuln.cwe_id,
                    additional_properties={
                        "tool": vuln.tool,
                        "confidence": vuln.confidence,
                        "owasp": vuln.owasp_category
                    }
                )
                vulnerabilities.append(orch_vuln)
            
            logger.info(f"✅ SAST completado. {len(vulnerabilities)} vulnerabilidades encontradas.")
            return vulnerabilities

    async def orchestrate(self, repo_url: str, council_filter: Optional[List[str]] = None, dry_run: bool = False):
        """
        Punto de entrada principal.
        - Ejecuta SAST
        - Filtra vulnerabilidades HIGH/CRITICAL
        - Asigna modelos según el consejo
        - Crea worktrees y lanza contenedores
        - Espera resultados y genera PRs
        """
        logger.info("🚀 Iniciando orquestación SAST multi‑SOTA")

        # 1. Ejecutar SAST y obtener vulnerabilidades
        logger.info(f"🔍 Ejecutando análisis SAST en {repo_url}")
        vulnerabilities = await self._run_sast(repo_url)

        if not vulnerabilities:
            logger.warning("No se encontraron vulnerabilidades")
            return self._empty_result()

        # 2. Filtrar por severidad HIGH/CRITICAL
        severities_to_process = {"high", "critical"}
        filtered_vulns = [
            v for v in vulnerabilities
            if v.severity.lower() in severities_to_process
        ]

        logger.info(f"Vulnerabilidades totales: {len(vulnerabilities)}")
        logger.info(f"Vulnerabilidades HIGH/CRITICAL: {len(filtered_vulns)}")

        if not filtered_vulns:
            logger.info("No hay vulnerabilidades HIGH/CRITICAL que procesar")
            return self._empty_result()

        # (Opcional) Limitar a un máximo para pruebas
        MAX_VULNS = 2  # Ajusta según necesidad
        if len(filtered_vulns) > MAX_VULNS:
            logger.warning(f"Demasiadas vulnerabilidades, procesando solo las primeras {MAX_VULNS}")
            filtered_vulns = filtered_vulns[:MAX_VULNS]

        # 3. Asignar modelos (round‑robin sobre los modelos configurados)
        model_keys = list(self.llm_configs.keys())
        if council_filter:
            # Si se pasa un filtro, usar solo esos modelos (si existen)
            model_keys = [m for m in model_keys if m in council_filter]

        if not model_keys:
            logger.error("No hay modelos configurados para usar")
            return self._empty_result()

        tasks = []
        for i, vuln in enumerate(filtered_vulns):
            model_key = model_keys[i % len(model_keys)]
            model_display = self.llm_configs[model_key].get("model", model_key)
            task = SOTATask(
                vulnerability=vuln,
                model_key=model_key,
                model_display=model_display
            )
            self.tasks[task.task_id] = task
            tasks.append(task)

        # 4. Crear worktrees (con nombre único)
        for task in tasks:
            try:
                # Crear un identificador único para el worktree
                vuln_id_safe = re.sub(r'[^\w\-]', '_', task.vulnerability.id)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # incluye microsegundos
                branch_name = f"tdh-fix/{vuln_id_safe}-{timestamp}"

                worktree_path = await self._create_worktree(
                    repo_url,
                    self.orchestrator_config.get("base_branch", "main"),
                    branch_name  # pasamos el nombre completo
                )
                task.worktree_path = worktree_path
                task.update_state(TaskState.WORKTREE_CREATED)
            except Exception as e:
                task.update_state(TaskState.FAILED)
                task.error = f"Error creando worktree: {e}"

        # 5. Ejecutar tareas en paralelo con límite de concurrencia para evitar rate limiting
        semaphore = asyncio.Semaphore(1)  # solo una tarea a la vez

        async def run_with_semaphore(task):
            async with semaphore:
                await self._run_single_task(task, dry_run)

        agent_tasks = []
        for task in tasks:
            if task.state != TaskState.FAILED:
                agent_tasks.append(run_with_semaphore(task))

        if agent_tasks:
            await asyncio.gather(*agent_tasks, return_exceptions=True)

        # 6. Procesar resultados y crear PRs
        pr_tasks = []
        for task in tasks:
            if task.state == TaskState.COMPLETED:
                fix_info = self._parse_agent_output(task)
                task.result.update(fix_info)
                pr_tasks.append(self._create_pull_request(task, repo_url, dry_run))
            elif task.state == TaskState.FAILED:
                logger.error(f"Tarea {task.task_id} falló: {task.error}")

        if pr_tasks:
            await asyncio.gather(*pr_tasks, return_exceptions=True)

        # 7. Generar reporte
        return self._generate_report()

    async def _create_worktree(self, repo_url: str, base_branch: str, branch_name: str) -> Path:
        """
        Crea un worktree con el nombre de rama dado.
        Retorna la ruta absoluta al worktree.
        """
        worktrees_base = Path("/tmp/tdh-worktrees")
        worktrees_base.mkdir(exist_ok=True, parents=True)

        worktree_path = worktrees_base / branch_name

        # Clonar el repositorio en un directorio temporal si no existe
        repo_dir = worktrees_base / "repo"
        if not repo_dir.exists():
            logger.info(f"Clonando {repo_url} en {repo_dir}")
            auth_url = self._get_authenticated_repo_url(repo_url)
            subprocess.run(
                ["git", "clone", auth_url, str(repo_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            # Configurar remote con token para futuros pushes (si ya lo tiene, no hace falta)
            # Aseguramos que el remote tenga la URL autenticada
            if self.github_token:
                subprocess.run(
                    ["git", "-C", str(repo_dir), "remote", "set-url", "origin", auth_url],
                    check=True,
                    capture_output=True,
                    text=True
                )

        # Crear el worktree
        logger.info(f"Creando worktree {branch_name} en {worktree_path}")
        subprocess.run(
            ["git", "-C", str(repo_dir), "worktree", "add", "-b", branch_name, str(worktree_path)],
            check=True,
            capture_output=True,
            text=True
        )

        return worktree_path

    def _generate_task_input(self, task: SOTATask) -> Dict:
        return {
            "model": task.model_key,  # antes era task.model_display
            "vulnerability": {
                "id": task.vulnerability.id,
                "file": task.vulnerability.file,
                "line": task.vulnerability.line,
                "description": task.vulnerability.description,
                "severity": task.vulnerability.severity
            },
            "repo_path": str(task.worktree_path),
            "openrouter_api_key": self.openrouter_key
        }

    async def _run_single_task(self, task: SOTATask, dry_run: bool = False):
        """
        Ejecuta un agente SOTA en un contenedor Docker para una vulnerabilidad específica.
        Crea un archivo input.json en el worktree y ejecuta el agente con redirección de stdin.
        """
        if not self.openrouter_key:
            task.error = f"Falta {OPENROUTER_API_KEY}. Tarea abortada."
            task.update_state(TaskState.FAILED)
            return

        if dry_run:
            logger.info(f"[DRY RUN] Simulando ejecución para tarea {task.task_id}")
            task.result = {"fix": "simulated", "test": "simulated"}
            task.update_state(TaskState.COMPLETED)
            return

        # Preparar el input JSON para el agente
        input_json = self._generate_task_input(task)
        container_name = f"tdh-agent-{task.task_id}"
        task.container_name = container_name

        # Crear archivo input.json en el worktree (accesible desde el contenedor)
        input_file = task.worktree_path / "input.json"
        try:
            with open(input_file, 'w') as f:
                json.dump(input_json, f, indent=2)
            logger.info(f"📄 Archivo de input creado en {input_file}")
            
            # Verificar que el archivo existe
            if input_file.exists():
                logger.info(f"✅ El archivo existe, tamaño: {input_file.stat().st_size} bytes")
            else:
                logger.error(f"❌ El archivo no existe después de escribirlo")
                task.error = "No se pudo crear input.json (desapareció)"
                task.update_state(TaskState.FAILED)
                return
        except Exception as e:
            logger.error(f"Error creando input.json: {e}")
            task.error = f"No se pudo crear input.json: {e}"
            task.update_state(TaskState.FAILED)
            return

        try:
            # Iniciar contenedor en segundo plano con sleep infinity para mantenerlo vivo
            container = self.docker_client.containers.run(
                image=DEFAULT_BASE_IMAGE,
                command=["sleep", "infinity"],
                name=container_name,
                detach=True,
                remove=False,
                volumes={
                    str(task.worktree_path): {"bind": "/workspace", "mode": "rw"},
                    # Montar el archivo de configuración del consejo
                    str(COUNCIL_CONFIG_PATH.absolute()): {"bind": "/etc/tdh/llm_council.yaml", "mode": "ro"}
                },
                working_dir="/workspace",
                environment={
                    "OPENROUTER_API_KEY": self.openrouter_key,
                    "TDH_COUNCIL_CONFIG": "/etc/tdh/llm_council.yaml"
                }
            )
            self.active_containers.add(container_name)
            task.update_state(TaskState.CONTAINER_STARTED)

            # Verificar que el archivo sigue existiendo antes de ejecutar
            if not input_file.exists():
                logger.error(f"❌ El archivo input.json desapareció antes de ejecutar el agente")
                task.error = "input.json desapareció"
                task.update_state(TaskState.FAILED)
                return

            # Ejecutar el agente dentro del contenedor, redirigiendo stdin desde el archivo
            exec_result = container.exec_run(
                "bash -c 'python /usr/local/bin/sota_agent.py < /workspace/input.json'"
            )
            output = exec_result.output.decode()
            exit_code = exec_result.exit_code

            # Obtener logs completos del contenedor
            logs = container.logs(stdout=True, stderr=True).decode()
            task.result["logs"] = logs
            task.result["output"] = output
            task.result["exit_code"] = exit_code

            # Mostrar logs para depuración
            logger.error(f"🔍 DEBUG - Salida del agente (primeros 500 chars): {output[:500]}")
            logger.error(f"🔍 DEBUG - Logs del contenedor (primeros 500 chars): {logs[:500]}")

            # Parsear la salida del agente (se espera JSON)
            json_output = self._extract_json_from_output(output)
            if json_output:
                task.result.update(json_output)
            else:
                # Si no hay JSON, al menos guardamos la salida como texto
                task.result["raw_output"] = output

            if exit_code == 0:
                task.update_state(TaskState.COMPLETED)
            else:
                task.update_state(TaskState.FAILED)
                task.error = f"Agente falló con código {exit_code}"

        except Exception as e:
            task.update_state(TaskState.FAILED)
            task.error = str(e)
            logger.exception(f"Error en contenedor para tarea {task.task_id}")
        finally:
            # Limpiar: eliminar contenedor
            if container_name in self.active_containers:
                self.active_containers.remove(container_name)
            try:
                container = self.docker_client.containers.get(container_name)
                container.remove(force=True)
            except:
                pass
            # No eliminar input.json para depuración (comentado)
            # try:
            #     input_file.unlink()
            # except:
            #     pass

    def _extract_json_from_output(self, output: str) -> Optional[Dict]:
        """
        Extrae el primer bloque JSON válido de la salida.
        Busca desde el final hacia el principio para encontrar el último JSON.
        """
        import re
        # Patrón para encontrar objetos JSON (no perfecto pero funciona)
        pattern = r'(\{.*\})'
        matches = re.findall(pattern, output, re.DOTALL)
        for match in reversed(matches):
            try:
                return json.loads(match)
            except:
                continue
        return None

    def _parse_agent_output(self, task: SOTATask) -> Dict:
        output = task.result.get("output", "")
        try:
            match = re.search(r'({.*})', output, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        return {}

    async def _create_pull_request(self, task: SOTATask, repo_url: str, dry_run: bool = False):
        if dry_run:
            logger.info(f"[DRY RUN] Se crearía PR para {task.task_id}")
            task.pr_url = "https://github.com/dry-run/pr"
            task.update_state(TaskState.PR_CREATED)
            return

        if not self.github_token:
            task.error = "No hay token de GitHub, no se puede crear PR"
            return

        try:
            repo = self._get_github_repo(repo_url)
            branch_name = task.worktree_path.name

            # Configurar identidad de git
            subprocess.run(
                ["git", "-C", str(task.worktree_path), "config", "user.email", "tdh-bot@example.com"],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["git", "-C", str(task.worktree_path), "config", "user.name", "TDH Bot"],
                check=True,
                capture_output=True,
                text=True
            )

            # Hacer commit de los cambios
            subprocess.run(
                ["git", "-C", str(task.worktree_path), "add", "."],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["git", "-C", str(task.worktree_path), "commit", "-m", f"Fix {task.vulnerability.id}"],
                check=True,
                capture_output=True,
                text=True
            )

            # Hacer push
            subprocess.run(
                ["git", "-C", str(task.worktree_path), "push", "-u", "origin", branch_name],
                check=True,
                capture_output=True,
                text=True
            )

            pr_title = f"Fix: {task.vulnerability.id} - {task.vulnerability.description[:50]}"
            pr_body = f"Este PR soluciona la vulnerabilidad **{task.vulnerability.id}**.\n\n"
            pr_body += f"**Archivo:** {task.vulnerability.file}:{task.vulnerability.line}\n"
            pr_body += f"**Descripción:** {task.vulnerability.description}\n\n"
            pr_body += "**Cambios realizados por el agente autónomo.**"

            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=self.orchestrator_config.get("base_branch", "main")
            )
            task.pr_url = pr.html_url
            task.update_state(TaskState.PR_CREATED)
            logger.info(f"✅ Pull request creado: {pr.html_url}")

        except subprocess.CalledProcessError as e:
            task.error = f"Error en git: {e.stderr}"
            logger.exception(f"Error en git para tarea {task.task_id}: {e.stderr}")
        except Exception as e:
            task.error = f"Error creando PR: {e}"
            logger.exception("Error en creación de PR")

    def _get_github_repo(self, repo_url: str):
        if not self.github_token:
            raise ValueError("GitHub token no disponible")
        g = Github(self.github_token)
        match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(\.git)?$", repo_url)
        if not match:
            raise ValueError(f"URL de repositorio no válida: {repo_url}")
        owner, repo_name = match.group(1), match.group(2)
        return g.get_repo(f"{owner}/{repo_name}")

    def _generate_report(self) -> Dict:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.state == TaskState.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.state == TaskState.FAILED)
        pr_created = sum(1 for t in self.tasks.values() if t.pr_url is not None)

        prs = [{"task_id": t.task_id, "pr_url": t.pr_url} for t in self.tasks.values() if t.pr_url]

        tasks_list = []
        for t in self.tasks.values():
            tasks_list.append({
                "task_id": t.task_id,
                "model": t.model_display,
                "vuln_id": t.vulnerability.id,
                "cwe": t.vulnerability.id,
                "state": t.state.value,
                "pr_url": t.pr_url,
                "error": t.error
            })

        report = {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pr_created": pr_created,
            "prs": prs,
            "tasks": tasks_list
        }

        # Guardar en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.results_dir / f"orchestration_results_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"📊 Reporte guardado en {report_path}")

        return report

    def _empty_result(self) -> Dict:
        return {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "pr_created": 0,
            "prs": [],
            "tasks": []
        }