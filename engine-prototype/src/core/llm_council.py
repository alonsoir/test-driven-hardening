# src/core/llm_council.py
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import yaml
from pathlib import Path
from src.llms.openrouter_adapter import OpenRouterLLM


class LLMCouncil:
    """
    Consejo de LLMs SOTA que colaboran para fixear vulnerabilidades.
    
    Responsabilidades:
    - Gestionar 5+ LLMs SOTA impares
    - Asignar vulnerabilidades a LLMs disponibles
    - Coordinar trabajo paralelo
    - Recopilar y comparar resultados
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.llms: List[OpenRouterLLM] = []
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, List[Dict]] = {}
        self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]):
        """Carga configuración de LLMs desde YAML."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "llm_council.yaml"
        
        if not Path(config_path).exists():
            # Configuración por defecto (para desarrollo)
            default_config = {
                "llms": [
                    {
                        "name": "Claude-3.5-Sonnet",
                        "model": "anthropic/claude-3.5-sonnet",
                        "api_key_env": "OPENROUTER_API_KEY"
                    },
                    {
                        "name": "GPT-4-Turbo",
                        "model": "openai/gpt-4-turbo",
                        "api_key_env": "OPENROUTER_API_KEY"
                    },
                    {
                        "name": "DeepSeek-Coder",
                        "model": "deepseek/deepseek-coder",
                        "api_key_env": "OPENROUTER_API_KEY"
                    },
                    {
                        "name": "Gemini-Pro",
                        "model": "google/gemini-pro",
                        "api_key_env": "OPENROUTER_API_KEY"
                    },
                    {
                        "name": "Llama-3.1-70B",
                        "model": "meta-llama/llama-3.1-70b-instruct",
                        "api_key_env": "OPENROUTER_API_KEY"
                    }
                ],
                "settings": {
                    "min_llms": 3,
                    "preferred_odd_number": 5,
                    "timeout_per_llm": 120,
                    "max_retries": 2
                }
            }
            
            # Guardar configuración por defecto
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            print(f"📝 Configuración por defecto creada en: {config_path}")
            config = default_config
        else:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        
        # Inicializar LLMs
        for llm_config in config.get("llms", []):
            api_key = self._get_api_key(llm_config.get("api_key_env"))
            if api_key:
                llm = OpenRouterLLM(
                    name=llm_config["name"],
                    api_key=api_key,
                    model=llm_config["model"]
                )
                self.llms.append(llm)
        
        self.settings = config.get("settings", {})
        print(f"🤖 Consejo inicializado con {len(self.llms)} LLMs")
    
    def _get_api_key(self, env_var: str) -> Optional[str]:
        """Obtiene API key de variable de entorno."""
        import os
        return os.getenv(env_var, os.getenv("OPENROUTER_API_KEY"))
    
    async def initialize_council(self) -> Tuple[int, List[str]]:
        """
        Inicializa el consejo verificando disponibilidad de LLMs.
        
        Returns:
            (available_count, available_names)
        """
        print("\n🤖 Inicializando Consejo de LLMs...")
        
        tasks = [llm.check_availability() for llm in self.llms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        available_llms = []
        for llm, result in zip(self.llms, results):
            if isinstance(result, Exception) or not result:
                print(f"   ❌ {llm.name} - NO disponible")
                llm.is_available = False
            else:
                print(f"   ✅ {llm.name} - Disponible")
                llm.is_available = True
                available_llms.append(llm)
        
        # Mantener solo LLMs disponibles
        self.llms = available_llms
        
        min_required = self.settings.get("min_llms", 3)
        if len(self.llms) < min_required:
            print(f"⚠️  Advertencia: Solo {len(self.llms)} LLMs disponibles (mínimo: {min_required})")
        
        # Asegurar número impar para "votaciones"
        if len(self.llms) % 2 == 0 and len(self.llms) > 0:
            # Remover el menos preferido si hay número par
            print(f"   🔄 Ajustando a número impar de LLMs")
            self.llms = self.llms[:-1]
        
        return len(self.llms), [llm.name for llm in self.llms]
    
    async def assign_vulnerability(
        self,
        worktree_manager,
        branch_name: str,
        sast_issue: Dict[str, Any],
        llm_indices: Optional[List[int]] = None
    ) -> Dict[str, Dict]:
        """
        Asigna una vulnerabilidad a múltiples LLMs para fixes paralelos.
        
        Returns:
            Dict con resultados por LLM: {llm_name: {files_fixed, success, error}}
        """
        if not self.llms:
            raise Exception("No hay LLMs disponibles en el consejo")
        
        # Seleccionar LLMs (todos disponibles o subconjunto)
        if llm_indices is None:
            selected_llms = self.llms[:self.settings.get("preferred_odd_number", 5)]
        else:
            selected_llms = [self.llms[i] for i in llm_indices if i < len(self.llms)]
        
        print(f"\n🎯 Asignando vulnerabilidad a {len(selected_llms)} LLMs:")
        for llm in selected_llms:
            print(f"   • {llm.name}")
        
        # Preparar contexto para cada LLM
        context = worktree_manager.prepare_llm_context(branch_name, sast_issue)
        
        # Ejecutar fixes en paralelo
        tasks = {}
        for llm in selected_llms:
            task_name = f"{llm.name}_{sast_issue.get('rule_id', 'unknown')}"
            task = asyncio.create_task(
                self._generate_fix_with_retry(llm, context),
                name=task_name
            )
            tasks[llm.name] = task
        
        # Esperar resultados con timeout
        timeout = self.settings.get("timeout_per_llm", 120) * len(selected_llms)
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"⏰ Timeout esperando fixes de LLMs")
            results = [Exception("Timeout")] * len(selected_llms)
        
        # Procesar resultados
        final_results = {}
        for llm, result in zip(selected_llms, results):
            if isinstance(result, Exception):
                final_results[llm.name] = {
                    "success": False,
                    "error": str(result),
                    "fixed_files": {}
                }
            else:
                final_results[llm.name] = {
                    "success": True,
                    "error": None,
                    "fixed_files": result
                }
        
        # Guardar resultados
        issue_id = sast_issue.get("rule_id", "unknown")
        self.results[issue_id] = final_results
        
        return final_results
    
    async def _generate_fix_with_retry(
        self,
        llm: OpenRouterLLM,
        context: Dict[str, Any],
        max_retries: int = 2
    ) -> Dict[str, str]:
        """Genera fix con reintentos en caso de error."""
        for attempt in range(max_retries + 1):
            try:
                print(f"   🔄 {llm.name} generando fix (intento {attempt + 1})...")
                return await llm.generate_fix(context)
            except Exception as e:
                if attempt < max_retries:
                    print(f"   ⚠️  {llm.name} falló, reintentando...")
                    await asyncio.sleep(1)  # Esperar antes de reintentar
                else:
                    raise e
    
    def get_best_fix(self, issue_id: str) -> Optional[Tuple[str, Dict[str, str]]]:
        """
        Selecciona el mejor fix entre todos los generados.
        (Por ahora, simplemente el primero exitoso)
        """
        if issue_id not in self.results:
            return None
        
        results = self.results[issue_id]
        
        for llm_name, result in results.items():
            if result["success"] and result["fixed_files"]:
                return llm_name, result["fixed_files"]
        
        return None
    
    def get_council_status(self) -> Dict[str, Any]:
        """Obtiene estado del consejo."""
        return {
            "total_llms": len(self.llms),
            "available_llms": [llm.name for llm in self.llms if llm.is_available],
            "active_tasks": len(self.active_tasks),
            "completed_issues": list(self.results.keys())
        }