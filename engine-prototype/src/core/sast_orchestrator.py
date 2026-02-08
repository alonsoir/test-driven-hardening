# engine-prototype/src/core/sast_orchestrator.py
"""
Orquestador SAST que integra Docker Manager y SAST Pipeline
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .docker_manager import DockerManager
from .sast_pipeline import SASTPipeline, SASTResult, Vulnerability

logger = logging.getLogger(__name__)

class SASTOrchestrator:
    """Orquestador que coordina análisis SAST en contenedores Docker"""
    
    def __init__(self):
        self.docker_manager = DockerManager()
        self.sast_pipeline = SASTPipeline()
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def analyze_repository(self, repo_url: str, llm_name: str = "claude-3-5") -> Dict[str, Any]:
        """
        Análisis completo: crear contenedor → ejecutar SAST → limpiar
        
        Args:
            repo_url: URL del repositorio a analizar
            llm_name: Nombre del LLM para el contenedor
        
        Returns:
            Dict con resultados del análisis
        """
        logger.info(f"🚀 Iniciando análisis para {repo_url}")
        
        try:
            # 1. Crear contenedor aislado
            logger.info(f"🐳 Creando contenedor para {llm_name}...")
            container_config = await self.docker_manager.create_isolated_container(
                llm_name, repo_url
            )
            
            # 2. Ejecutar análisis SAST dentro del contenedor
            logger.info("🔍 Ejecutando análisis SAST...")
            sast_result = await self._run_sast_in_container(
                container_config.container_name,
                repo_url
            )
            
            # 3. Limpiar contenedor
            logger.info("🧹 Limpiando contenedor...")
            await self.docker_manager.cleanup_container(container_config.container_name)
            
            # 4. Guardar resultados
            output_dir = self.results_dir / f"analysis_{Path(repo_url).stem}"
            await self.sast_pipeline.save_results(sast_result, str(output_dir))
            
            # 5. Preparar respuesta para LLM
            llm_response = await self._prepare_llm_response(sast_result)
            
            return {
                "success": True,
                "container": container_config.container_name,
                "sast_result": sast_result,
                "llm_response": llm_response,
                "output_dir": str(output_dir)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_sast_in_container(self, container_name: str, repo_url: str) -> SASTResult:
        """Ejecutar análisis SAST dentro de un contenedor Docker"""
        # Obtener ruta del repositorio dentro del contenedor
        repo_path = "/workspace/repo"
        
        # Ejecutar comandos de análisis
        tools_to_run = [
            ("cppcheck", f"cppcheck --enable=all --inconclusive {repo_path}"),
            ("bandit", f"cd {repo_path} && bandit -r . -f json"),
            ("semgrep", f"cd {repo_path} && semgrep --config auto --json")
        ]
        
        results = {}
        for tool_name, command in tools_to_run:
            try:
                logger.info(f"🛠️  Ejecutando {tool_name}...")
                result = await self.docker_manager.execute_command(
                    container_name, command
                )
                results[tool_name] = result
            except Exception as e:
                logger.warning(f"⚠️  Error con {tool_name}: {e}")
        
        # Para esta versión, simulamos análisis directo en host
        # (en producción se ejecutaría dentro del contenedor)
        logger.info("📊 Analizando código localmente...")
        
        # Clonar repo localmente temporalmente
        import tempfile
        import subprocess
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Clonar repositorio
            subprocess.run(["git", "clone", repo_url, tmp_dir], 
                         capture_output=True)
            
            # Ejecutar pipeline SAST
            sast_result = await self.sast_pipeline.run_complete_analysis(tmp_dir)
            
            return sast_result
    
    async def _prepare_llm_response(self, sast_result: SASTResult) -> Dict[str, Any]:
        """Preparar respuesta estructurada para LLM"""
        # Filtrar vulnerabilidades críticas/altas
        critical_vulns = [
            v for v in sast_result.vulnerabilities 
            if not v.false_positive and v.severity in ["critical", "high"]
        ]
        
        # Agrupar por tipo
        grouped_vulns = {}
        for vuln in critical_vulns:
            if vuln.cwe_id not in grouped_vulns:
                grouped_vulns[vuln.cwe_id] = []
            grouped_vulns[vuln.cwe_id].append(vuln)
        
        # Preparar contexto para LLM
        return {
            "summary": {
                "total_vulnerabilities": sast_result.total_vulnerabilities,
                "critical_high": len(critical_vulns),
                "by_severity": sast_result.by_severity,
                "by_tool": sast_result.by_tool
            },
            "critical_vulnerabilities": [
                {
                    "cwe": vuln.cwe_id,
                    "severity": vuln.severity,
                    "file": vuln.file_path,
                    "line": vuln.line_number,
                    "description": vuln.message,
                    "code_snippet": vuln.code_snippet,
                    "fix_suggestion": vuln.fix_suggestion
                }
                for vuln in critical_vulns[:10]  # Limitar a 10 para contexto
            ],
            "recommended_actions": self._generate_recommendations(critical_vulns)
        }
    
    def _generate_recommendations(self, vulnerabilities: List[Vulnerability]) -> List[str]:
        """Generar recomendaciones basadas en vulnerabilidades"""
        recommendations = []
        
        cwe_counts = {}
        for vuln in vulnerabilities:
            if vuln.cwe_id:
                cwe_counts[vuln.cwe_id] = cwe_counts.get(vuln.cwe_id, 0) + 1
        
        # Recomendaciones específicas por CWE
        for cwe_id, count in sorted(cwe_counts.items(), key=lambda x: x[1], reverse=True):
            if cwe_id == "CWE-78":
                recommendations.append(
                    f"Reemplazar {count} llamadas a system()/popen() con funciones seguras"
                )
            elif cwe_id == "CWE-120":
                recommendations.append(
                    f"Corregir {count} accesos fuera de límites en buffers/arrays"
                )
            elif cwe_id == "CWE-476":
                recommendations.append(
                    f"Agregar {count} verificaciones de punteros nulos"
                )
        
        # Recomendaciones generales
        if len(vulnerabilities) > 0:
            recommendations.append(
                "Implementar pruebas unitarias específicas para casos de borde"
            )
            recommendations.append(
                "Revisar la gestión de memoria en funciones críticas"
            )
        
        return recommendations