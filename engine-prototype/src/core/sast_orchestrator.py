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
import uuid
import yaml
import subprocess
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

# Cargar variables de entorno desde el archivo .env en la raíz
load_dotenv()

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes y Configuración de Secretos (Nombres de variables, no valores)
# ----------------------------------------------------------------------
COUNCIL_CONFIG_PATH = Path("/config/prompts/llm_council.yaml")
DEFAULT_BASE_IMAGE = "tdh-base:latest"
GITHUB_TOKEN_KEY = "GITHUB_TOKEN"
OPENROUTER_API_KEY = "OPENROUTER_API_KEY"

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
        """Extrae el estado de una línea de log con formato [STATE:...]."""
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
    model_key: str = ""          # clave en llm_configs
    model_display: str = ""      # nombre real para OpenRouter
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
        logger.info(f"[TASK:{self.task_id}] Estado → {new_state.value}"

class SASTOrchestrator:
    def __init__(self):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

        # Cargar configuración del consejo
        self.council_config = self._load_council_config()
        self.llm_configs = self.council_config.get("llm_configs", {})

        # --- GESTIÓN DE SECRETOS DESDE EL ENTORNO (.env) ---
        self.github_token = os.getenv(GITHUB_TOKEN_KEY)
        self.openrouter_key = os.getenv(OPENROUTER_API_KEY)

        self._validate_secrets()

        self.tasks: Dict[str, SOTATask] = {}
        self.active_containers: Set[str] = set()

    def _validate_secrets(self):
        """Verifica que las credenciales críticas estén presentes."""
        missing = []
        if not self.github_token:
            missing.append(GITHUB_TOKEN_KEY)
        if not self.openrouter_key:
            missing.append(OPENROUTER_API_KEY)
        
        if missing:
            logger.error(f"❌ Faltan secretos en el archivo .env: {', '.join(missing)}")
            # No salimos aquí para permitir ejecuciones de análisis parciales si fuera necesario,
            # pero lanzamos advertencias críticas.
        else:
            logger.info("🔐 Secretos cargados correctamente desde .env")

    # ... [Resto de métodos: _load_council_config, orchestrate, etc.] ...

    async def _run_single_task(self, task: SOTATask):
        """Ejecuta una tarea asegurando que el API Key se pase al contenedor."""
        if not self.openrouter_key:
            task.error = f"Falta {OPENROUTER_API_KEY}. Tarea abortada."
            task.update_state(TaskState.FAILED)
            return

        # El resto de la lógica de Docker y comunicación por stdin se mantiene igual
        # usando self.openrouter_key cargada desde el .env
        # ...