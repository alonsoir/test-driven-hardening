# engine-prototype/src/core/sast_pipeline.py
import tempfile
import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import aiofiles
from datetime import datetime
import yaml

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Vulnerability:
    """Estructura para vulnerabilidades encontradas"""
    tool: str
    vulnerability_id: str
    severity: str
    confidence: str
    file_path: str
    line_number: int
    column: int
    message: str
    cwe_id: Optional[str]
    owasp_category: Optional[str]
    code_snippet: str
    fix_suggestion: Optional[str]
    false_positive: bool = False
    context: Dict[str, Any] = None
    
    def to_dict(self):
        """Convertir a diccionario para serialización JSON"""
        return {
            "tool": self.tool,
            "vulnerability_id": self.vulnerability_id,
            "severity": self.severity,
            "confidence": self.confidence,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "message": self.message,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "code_snippet": self.code_snippet,
            "fix_suggestion": self.fix_suggestion,
            "false_positive": self.false_positive,
            "context": self.context
        }

@dataclass
class SASTResult:
    """Resultados del análisis SAST"""
    repo_url: str
    timestamp: str
    total_vulnerabilities: int
    by_severity: Dict[str, int]
    by_tool: Dict[str, int]
    vulnerabilities: List[Vulnerability]
    metadata: Dict[str, Any]

class SASTPipeline:
    """Pipeline de análisis estático de seguridad"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Buscar config en la raíz del proyecto
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "sast_config.yaml"
        
        self.config = self._load_config(str(config_path))
        self.vulnerabilities: List[Vulnerability] = []
        self.false_positive_patterns = self._load_false_positive_patterns()
    
    def _load_config(self, config_path: str) -> Dict:
        """Cargar configuración de SAST"""
        default_config = {
            "tools": {
                "cppcheck": {
                    "enabled": True,
                    "command": "cppcheck",
                    "args": [
                        "--enable=all",
                        "--inconclusive",
                        "--suppress=missingIncludeSystem",
                        "--suppress=unmatchedSuppression",
                        "--xml",
                        "--xml-version=2",
                        "--output-file={output_file}",
                        "--platform=unix64",
                        "--std=c++11",
                        "--std=c99"
                    ],
                    "timeout": 600
                },
                "flawfinder": {
                    "enabled": True,
                    "command": "flawfinder",
                    "args": [
                        "--quiet",
                        "--dataonly",
                        "--csv"
                    ],
                    "timeout": 300
                },
                "bandit": {
                    "enabled": True,
                    "command": "bandit",
                    "args": [
                        "-r",
                        "-f",
                        "json",
                        "-o",
                        "{output_file}",
                        "-lll"
                    ],
                    "timeout": 180
                },
                "semgrep": {
                    "enabled": True,
                    "command": "semgrep",
                    "args": [
                        "--config",
                        "auto",
                        "--json",
                        "-o",
                        "{output_file}",
                        "--metrics",
                        "off",
                        "--no-rewrite-rule-ids"
                    ],
                    "timeout": 300
                }
            },
            "severity_mapping": {
                "critical": ["CRITICAL", "HIGH"],
                "high": ["HIGH", "MEDIUM"],
                "medium": ["MEDIUM", "LOW"],
                "low": ["LOW", "INFO"]
            },
            "output_formats": ["json", "sarif"],
            "max_file_size_mb": 10
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                default_config.update(config)
        
        return default_config
    
    def _load_false_positive_patterns(self) -> Dict:
        """Cargar patrones de falsos positivos"""
        return {
            "cppcheck": [
                {"pattern": "missingInclude", "reason": "System includes"},
                {"pattern": "unusedFunction", "reason": "Common in test code"}
            ],
            "bandit": [
                {"pattern": "B101", "reason": "Test files allowed"},
                {"pattern": "assert_used", "reason": "Testing framework"}
            ]
        }
    
    async def run_complete_analysis(self, repo_path: str) -> SASTResult:
        """Ejecutar análisis completo SAST"""
        logger.info(f"🔍 Iniciando análisis SAST en: {repo_path}")
        
        tasks = []
        
        # Ejecutar herramientas en paralelo
        if self.config["tools"]["cppcheck"]["enabled"]:
            tasks.append(self._run_cppcheck(repo_path))
        
        if self.config["tools"]["flawfinder"]["enabled"]:
            tasks.append(self._run_flawfinder(repo_path))
        
        if self.config["tools"]["bandit"]["enabled"]:
            tasks.append(self._run_bandit(repo_path))
        
        if self.config["tools"]["semgrep"]["enabled"]:
            tasks.append(self._run_semgrep(repo_path))
        
        # Esperar a que todas las herramientas terminen
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        all_vulnerabilities = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error en herramienta: {result}")
                continue
            if result:
                all_vulnerabilities.extend(result)
        
        # Filtrar falsos positivos
        filtered_vulns = await self._filter_false_positives(all_vulnerabilities)
        
        # Ordenar por severidad
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        filtered_vulns.sort(key=lambda x: severity_order.get(x.severity.lower(), 5))
        
        # Crear resultados finales
        result = self._create_result_object(filtered_vulns, repo_path)
        
        logger.info(f"✅ Análisis completado. Vulnerabilidades encontradas: {result.total_vulnerabilities}")
        
        return result
    
    async def _run_cppcheck(self, repo_path: str) -> List[Vulnerability]:
        """Ejecutar cppcheck real con configuración profesional"""
        tool_config = self.config["tools"]["cppcheck"]
        
        # Crear archivo temporal para salida XML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            output_file = tmp.name
        
        try:
            # Construir comando
            args = [arg.format(output_file=output_file) for arg in tool_config["args"]]
            cmd = [tool_config["command"], *args, repo_path]
            
            logger.info(f"🛠️  Ejecutando cppcheck: {' '.join(cmd)}")
            
            # Ejecutar cppcheck
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=tool_config["timeout"]
            )
            
            if process.returncode not in [0, 1]:  # cppcheck retorna 0 o 1 en éxito
                logger.warning(f"cppcheck retornó {process.returncode}: {stderr.decode()}")
            
            # Parsear resultados XML
            vulnerabilities = await self._parse_cppcheck_results(output_file, repo_path)
            
            return vulnerabilities
            
        except asyncio.TimeoutError:
            logger.error("cppcheck timeout")
            return []
        except Exception as e:
            logger.error(f"Error ejecutando cppcheck: {e}")
            return []
        finally:
            # Limpiar archivo temporal
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    async def _parse_cppcheck_results(self, xml_file: str, repo_path: str) -> List[Vulnerability]:
        """Parsear resultados XML de cppcheck"""
        vulnerabilities = []
        
        try:
            import xml.etree.ElementTree as ET
            
            if not os.path.exists(xml_file):
                return vulnerabilities
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for error in root.findall('errors/error'):
                # Extraer información de la vulnerabilidad
                vuln_id = error.get('id', 'UNKNOWN')
                severity = error.get('severity', 'style')
                msg = error.get('msg', '')
                
                # Mapear severidad de cppcheck a estándar
                severity_map = {
                    'error': 'high',
                    'warning': 'medium',
                    'style': 'low',
                    'performance': 'low',
                    'portability': 'low',
                    'information': 'info'
                }
                
                mapped_severity = severity_map.get(severity.lower(), 'low')
                
                # Extraer ubicación
                location = error.find('location')
                if location is not None:
                    file_path = location.get('file', '')
                    line = int(location.get('line', 0))
                    column = int(location.get('column', 0))
                    
                    # Obtener snippet de código
                    code_snippet = await self._get_code_snippet(
                        os.path.join(repo_path, file_path),
                        line,
                        max_lines=3
                    )
                    
                    # Mapear a CWE si es posible
                    cwe_id = self._map_cppcheck_to_cwe(vuln_id)
                    
                    # Crear objeto de vulnerabilidad
                    vuln = Vulnerability(
                        tool="cppcheck",
                        vulnerability_id=vuln_id,
                        severity=mapped_severity,
                        confidence="medium",
                        file_path=file_path,
                        line_number=line,
                        column=column,
                        message=msg,
                        cwe_id=cwe_id,
                        owasp_category=self._map_to_owasp(cwe_id),
                        code_snippet=code_snippet,
                        fix_suggestion=self._get_cppcheck_fix_suggestion(vuln_id),
                        context={
                            "verbose": error.get('verbose', ''),
                            "inconclusive": error.get('inconclusive', False)
                        }
                    )
                    
                    vulnerabilities.append(vuln)
            
            logger.info(f"📊 cppcheck encontró {len(vulnerabilities)} vulnerabilidades")
            
        except Exception as e:
            logger.error(f"Error parseando resultados cppcheck: {e}")
        
        return vulnerabilities
    
    def _map_cppcheck_to_cwe(self, vuln_id: str) -> Optional[str]:
        """Mapear ID de cppcheck a CWE"""
        cwe_mapping = {
            'arrayIndexOutOfBounds': 'CWE-120',
            'bufferAccessOutOfBounds': 'CWE-120',
            'nullPointer': 'CWE-476',
            'uninitvar': 'CWE-457',
            'memoryLeak': 'CWE-401',
            'resourceLeak': 'CWE-772',
            'insecureCmdLineArgs': 'CWE-78',
            'insecureFunctions': 'CWE-676',
            'useClosedFile': 'CWE-910',
            'invalidPrintfArg': 'CWE-685',
            'invalidScanfArg': 'CWE-685',
            'unsignedLessThanZero': 'CWE-570',
            'signedLessThanZero': 'CWE-570'
        }
        
        return cwe_mapping.get(vuln_id)
    
    def _get_cppcheck_fix_suggestion(self, vuln_id: str) -> str:
        """Obtener sugerencia de fix para vulnerabilidad cppcheck"""
        suggestions = {
            'nullPointer': "Verificar que el puntero no sea nulo antes de desreferenciarlo.",
            'memoryLeak': "Asegurar que toda memoria asignada sea liberada.",
            'uninitvar': "Inicializar todas las variables antes de usarlas.",
            'bufferAccessOutOfBounds': "Verificar límites de arrays antes de acceder.",
            'insecureFunctions': "Usar funciones seguras alternativas (ej: strncpy en lugar de strcpy)."
        }
        
        return suggestions.get(vuln_id, "Revisar el código para posibles errores.")
    
    async def _run_bandit(self, repo_path: str) -> List[Vulnerability]:
        """Ejecutar bandit para análisis de Python"""
        tool_config = self.config["tools"]["bandit"]
        
        # Verificar si hay archivos Python
        python_files = list(Path(repo_path).rglob("*.py"))
        if not python_files:
            return []
        
        # Crear archivo temporal para salida JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            output_file = tmp.name
        
        try:
            # Construir comando
            args = []
            for arg in tool_config["args"]:
                if arg == "{output_file}":
                    args.append(output_file)
                else:
                    args.append(arg)
            
            cmd = [tool_config["command"], *args, repo_path]
            
            logger.info(f"🛠️  Ejecutando bandit: {' '.join(cmd)}")
            
            # Ejecutar bandit
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=tool_config["timeout"]
            )
            
            if process.returncode not in [0, 1]:  # bandit retorna 0 o 1
                logger.warning(f"bandit retornó {process.returncode}: {stderr.decode()}")
            
            # Parsear resultados JSON
            vulnerabilities = await self._parse_bandit_results(output_file, repo_path)
            
            return vulnerabilities
            
        except asyncio.TimeoutError:
            logger.error("bandit timeout")
            return []
        except Exception as e:
            logger.error(f"Error ejecutando bandit: {e}")
            return []
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    async def _parse_bandit_results(self, json_file: str, repo_path: str) -> List[Vulnerability]:
        """Parsear resultados JSON de bandit"""
        vulnerabilities = []
        
        try:
            if not os.path.exists(json_file):
                return vulnerabilities
            
            async with aiofiles.open(json_file, 'r') as f:
                content = await f.read()
                results = json.loads(content)
            
            for issue in results.get('results', []):
                # Extraer información
                vuln_id = issue.get('test_id', 'UNKNOWN')
                severity = issue.get('issue_severity', 'MEDIUM').lower()
                confidence = issue.get('issue_confidence', 'MEDIUM').lower()
                
                # Obtener snippet de código
                code_snippet = issue.get('code', '')
                
                # Crear objeto de vulnerabilidad
                vuln = Vulnerability(
                    tool="bandit",
                    vulnerability_id=vuln_id,
                    severity=severity,
                    confidence=confidence,
                    file_path=issue.get('filename', '').replace(repo_path + '/', ''),
                    line_number=issue.get('line_number', 0),
                    column=0,
                    message=issue.get('issue_text', ''),
                    cwe_id=issue.get('cwe', {}).get('id') if isinstance(issue.get('cwe'), dict) else None,
                    owasp_category=None,
                    code_snippet=code_snippet,
                    fix_suggestion=issue.get('fix', {}).get('recommendation', ''),
                    context={
                        "more_info": issue.get('more_info'),
                        "test_name": issue.get('test_name')
                    }
                )
                
                vulnerabilities.append(vuln)
            
            logger.info(f"📊 bandit encontró {len(vulnerabilities)} vulnerabilidades")
            
        except Exception as e:
            logger.error(f"Error parseando resultados bandit: {e}")
        
        return vulnerabilities
    
    async def _run_semgrep(self, repo_path: str) -> List[Vulnerability]:
        """Ejecutar semgrep para análisis multi-lenguaje"""
        tool_config = self.config["tools"]["semgrep"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            output_file = tmp.name
        
        try:
            # Construir comando
            args = []
            for arg in tool_config["args"]:
                if arg == "{output_file}":
                    args.append(output_file)
                else:
                    args.append(arg)
            
            cmd = [tool_config["command"], *args, repo_path]
            
            logger.info(f"🛠️  Ejecutando semgrep: {' '.join(cmd)}")
            
            # Ejecutar semgrep
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=tool_config["timeout"]
            )
            
            # DEBUG: Ver qué devuelve semgrep
            logger.debug(f"semgrep stdout: {stdout[:500]}")
            logger.debug(f"semgrep stderr: {stderr[:500]}")
            
            # Parsear resultados JSON
            vulnerabilities = await self._parse_semgrep_results(output_file, repo_path)
            
            return vulnerabilities
            
        except asyncio.TimeoutError:
            logger.error("semgrep timeout")
            return []
        except Exception as e:
            logger.error(f"Error ejecutando semgrep: {e}")
            return []
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    async def _parse_semgrep_results(self, json_file: str, repo_path: str) -> List[Vulnerability]:
        """Parsear resultados JSON de semgrep"""
        vulnerabilities = []
        
        try:
            if not os.path.exists(json_file) or os.path.getsize(json_file) == 0:
                logger.warning(f"semgrep output file is empty or doesn't exist: {json_file}")
                return vulnerabilities
            
            async with aiofiles.open(json_file, 'r') as f:
                content = await f.read()
                
            if not content.strip():
                logger.warning("semgrep returned empty output")
                return vulnerabilities
                
            results = json.loads(content)
            
            for result in results.get('results', []):
                # Extraer información básica
                check_id = result.get('check_id', 'UNKNOWN')
                severity = result.get('extra', {}).get('severity', 'WARNING').lower()
                message = result.get('extra', {}).get('message', '')
                
                # Mapear severidad de semgrep a estándar
                severity_map = {
                    'error': 'high',
                    'warning': 'medium',
                    'info': 'low'
                }
                mapped_severity = severity_map.get(severity, 'low')
                
                # Obtener ubicación
                path = result.get('path', '')
                line = result.get('start', {}).get('line', 0)
                col = result.get('start', {}).get('col', 0)
                
                # Obtener snippet de código
                code_snippet = await self._get_code_snippet(
                    os.path.join(repo_path, path),
                    line
                )
                
                # Intentar extraer CWE si está disponible
                cwe_id = None
                metadata = result.get('extra', {}).get('metadata', {})
                if 'cwe' in metadata:
                    cwe_list = metadata['cwe']
                    if cwe_list:
                        # Tomar el primer CWE
                        cwe_id = cwe_list[0]
                
                # Crear objeto de vulnerabilidad
                vuln = Vulnerability(
                    tool="semgrep",
                    vulnerability_id=check_id,
                    severity=mapped_severity,
                    confidence="medium",
                    file_path=path,
                    line_number=line,
                    column=col,
                    message=message,
                    cwe_id=cwe_id,
                    owasp_category=None,
                    code_snippet=code_snippet,
                    fix_suggestion=result.get('extra', {}).get('fix', ''),
                    context={
                        "metadata": metadata,
                        "rule_id": check_id
                    }
                )
                
                vulnerabilities.append(vuln)
            
            logger.info(f"📊 semgrep encontró {len(vulnerabilities)} vulnerabilidades")

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de semgrep: {e}. Content: {content[:200]}")
            return []
            
        except Exception as e:
            logger.error(f"Error parseando resultados semgrep: {e}")
        
        return vulnerabilities
    
    async def _run_flawfinder(self, repo_path: str) -> List[Vulnerability]:
        """Ejecutar flawfinder para análisis C/C++"""
        tool_config = self.config["tools"]["flawfinder"]
        
        try:
            cmd = [tool_config["command"]]
            cmd.extend(tool_config["args"])
            cmd.append(repo_path)
            
            logger.info(f"🛠️  Ejecutando flawfinder: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=tool_config["timeout"]
            )
            
            if process.returncode not in [0, 1]:  # flawfinder retorna 0 o 1
                logger.warning(f"flawfinder retornó {process.returncode}: {stderr.decode()}")
            
            # Parsear resultados CSV
            vulnerabilities = await self._parse_flawfinder_results(
                stdout.decode('utf-8', errors='ignore'),
                repo_path
            )
            
            return vulnerabilities
            
        except asyncio.TimeoutError:
            logger.error("flawfinder timeout")
            return []
        except Exception as e:
            logger.error(f"Error ejecutando flawfinder: {e}")
            return []

    async def _parse_flawfinder_results(self, csv_output: str, repo_path: str) -> List[Vulnerability]:
        """Parsear resultados CSV de flawfinder"""
        vulnerabilities = []
        
        try:
            import csv
            import io
            
            # Leer CSV
            csv_reader = csv.reader(io.StringIO(csv_output))
            rows = list(csv_reader)
            
            # Saltar encabezado si existe
            start_idx = 0
            if rows and rows[0] and 'File' in rows[0][0]:
                start_idx = 1
            
            for row in rows[start_idx:]:
                if len(row) < 6:
                    continue
                
                file_path = row[0]
                line = int(row[1]) if row[1].isdigit() else 0
                col = int(row[2]) if row[2].isdigit() else 0
                vuln_id = row[3]
                severity = row[4]
                message = row[5] if len(row) > 5 else ""
                
                # Mapear severidad de flawfinder
                severity_map = {
                    '5': 'high',
                    '4': 'high',
                    '3': 'medium',
                    '2': 'low',
                    '1': 'low',
                    '0': 'info'
                }
                mapped_severity = severity_map.get(severity, 'low')
                
                # Obtener snippet
                code_snippet = await self._get_code_snippet(
                    os.path.join(repo_path, file_path),
                    line
                )
                
                # Mapear a CWE si es posible
                cwe_id = self._map_flawfinder_to_cwe(vuln_id)
                
                vuln = Vulnerability(
                    tool="flawfinder",
                    vulnerability_id=vuln_id,
                    severity=mapped_severity,
                    confidence="medium",
                    file_path=file_path,
                    line_number=line,
                    column=col,
                    message=message,
                    cwe_id=cwe_id,
                    owasp_category=self._map_to_owasp(cwe_id),
                    code_snippet=code_snippet,
                    fix_suggestion=self._get_flawfinder_fix_suggestion(vuln_id),
                    context={"raw_severity": severity}
                )
                
                vulnerabilities.append(vuln)
            
            logger.info(f"📊 flawfinder encontró {len(vulnerabilities)} vulnerabilidades")
            
        except Exception as e:
            logger.error(f"Error parseando resultados flawfinder: {e}")
        
        return vulnerabilities

    def _map_flawfinder_to_cwe(self, vuln_id: str) -> Optional[str]:
        """Mapear ID de flawfinder a CWE"""
        # Mapeo básico, puedes expandirlo
        cwe_mapping = {
            'buffer': 'CWE-120',
            'format': 'CWE-134',
            'race': 'CWE-362',
            'shell': 'CWE-78',
            'tmp': 'CWE-377'
        }
        
        for key, cwe in cwe_mapping.items():
            if key in vuln_id.lower():
                return cwe
        return None

    def _get_flawfinder_fix_suggestion(self, vuln_id: str) -> str:
        """Obtener sugerencia de fix para flawfinder"""
        suggestions = {
            'buffer': "Usar funciones seguras que verifiquen límites (ej: strncpy en lugar de strcpy).",
            'format': "Validar y sanitizar entradas antes de usarlas en funciones de formato.",
            'race': "Usar mecanismos de sincronización (mutex, semáforos).",
            'shell': "Evitar ejecución de comandos de shell con entradas no validadas.",
            'tmp': "Usar funciones seguras para creación de archivos temporales (mkstemp)."
        }
        
        for key, suggestion in suggestions.items():
            if key in vuln_id.lower():
                return suggestion
        return "Revisar la documentación de flawfinder para más detalles."
    
    async def _get_code_snippet(self, file_path: str, line_number: int, max_lines: int = 3) -> str:
        """Obtener snippet de código alrededor de la línea especificada"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            async with aiofiles.open(file_path, 'r') as f:
                lines = await f.readlines()
            
            start_line = max(0, line_number - max_lines - 1)
            end_line = min(len(lines), line_number + max_lines)
            
            snippet_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1
                prefix = ">>> " if line_num == line_number else "    "
                snippet_lines.append(f"{prefix}{line_num}: {lines[i].rstrip()}")
            
            return "\n".join(snippet_lines)
            
        except Exception as e:
            logger.warning(f"Error obteniendo snippet: {e}")
            return ""
    
    def _map_to_owasp(self, cwe_id: Optional[str]) -> Optional[str]:
        """Mapear CWE a categoría OWASP Top 10"""
        if not cwe_id:
            return None
        
        owasp_mapping = {
            'CWE-78': 'A03:2021-Injection',
            'CWE-79': 'A03:2021-Injection',
            'CWE-89': 'A03:2021-Injection',
            'CWE-120': 'A07:2021-Identification and Authentication Failures',
            'CWE-401': 'A09:2021-Security Logging and Monitoring Failures',
            'CWE-476': 'A04:2021-Insecure Design',
            'CWE-798': 'A07:2021-Identification and Authentication Failures'
        }
        
        return owasp_mapping.get(cwe_id)
    
    async def _filter_false_positives(self, vulnerabilities: List[Vulnerability]) -> List[Vulnerability]:
        """Filtrar falsos positivos basado en patrones"""
        filtered = []
        
        for vuln in vulnerabilities:
            is_fp = False
            
            # Verificar patrones específicos por herramienta
            if vuln.tool in self.false_positive_patterns:
                for pattern in self.false_positive_patterns[vuln.tool]:
                    if pattern["pattern"].lower() in vuln.vulnerability_id.lower():
                        is_fp = True
                        logger.info(f"Marcando como falso positivo: {vuln.vulnerability_id}")
                        break
            
            # Verificar archivos de test
            if not is_fp:
                test_patterns = ["test_", "_test", "spec.", "mock", "fixture"]
                if any(pattern in vuln.file_path.lower() for pattern in test_patterns):
                    is_fp = True
            
            if not is_fp:
                filtered.append(vuln)
            else:
                vuln.false_positive = True
        
        return filtered
    
    def _create_result_object(self, vulnerabilities: List[Vulnerability], repo_path: str) -> SASTResult:
        """Crear objeto de resultados estructurado"""
        # Contar por severidad
        by_severity = {}
        by_tool = {}
        
        for vuln in vulnerabilities:
            if vuln.false_positive:
                continue
            
            by_severity[vuln.severity] = by_severity.get(vuln.severity, 0) + 1
            by_tool[vuln.tool] = by_tool.get(vuln.tool, 0) + 1
        
        return SASTResult(
            repo_url=repo_path,
            timestamp=datetime.now().isoformat(),
            total_vulnerabilities=len([v for v in vulnerabilities if not v.false_positive]),
            by_severity=by_severity,
            by_tool=by_tool,
            vulnerabilities=vulnerabilities,
            metadata={
                "analysis_duration": "N/A",
                "files_scanned": self._count_files_scanned(repo_path),
                "tools_used": list(by_tool.keys())
            }
        )
    
    def _count_files_scanned(self, repo_path: str) -> int:
        """Contar archivos escaneados"""
        try:
            count = 0
            for ext in ['.c', '.cpp', '.h', '.hpp', '.py', '.java', '.js']:
                count += len(list(Path(repo_path).rglob(f"*{ext}")))
            return count
        except:
            return 0
    
    async def save_results(self, result: SASTResult, output_dir: str):
        """Guardar resultados en múltiples formatos"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar como JSON
        json_file = os.path.join(output_dir, "sast_results.json")
        async with aiofiles.open(json_file, 'w') as f:
            await f.write(json.dumps({
                "repo_url": result.repo_url,
                "timestamp": result.timestamp,
                "summary": {
                    "total_vulnerabilities": result.total_vulnerabilities,
                    "by_severity": result.by_severity,
                    "by_tool": result.by_tool
                },
                "vulnerabilities": [v.to_dict() for v in result.vulnerabilities],
                "metadata": result.metadata
            }, indent=2, default=str))
        
        # Guardar como SARIF (para GitHub Code Scanning)
        sarif_file = os.path.join(output_dir, "sast_results.sarif")
        sarif_data = self._convert_to_sarif(result)
        async with aiofiles.open(sarif_file, 'w') as f:
            await f.write(json.dumps(sarif_data, indent=2))
        
        # Crear reporte resumido en texto
        txt_file = os.path.join(output_dir, "summary.txt")
        summary = self._generate_text_summary(result)
        async with aiofiles.open(txt_file, 'w') as f:
            await f.write(summary)
        
        logger.info(f"💾 Resultados guardados en: {output_dir}")
    
    def _convert_to_sarif(self, result: SASTResult) -> Dict:
        """Convertir resultados a formato SARIF"""
        # Implementación básica de SARIF
        sarif = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "TDH Engine SAST Pipeline",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/tdh-engine",
                        "rules": []
                    }
                },
                "results": []
            }]
        }
        
        return sarif
    
    def _generate_text_summary(self, result: SASTResult) -> str:
        """Generar resumen en texto legible"""
        summary_lines = [
            "=" * 60,
            "TDH ENGINE - REPORTE DE ANÁLISIS SAST",
            "=" * 60,
            f"Repositorio: {result.repo_url}",
            f"Fecha: {result.timestamp}",
            "",
            f"📊 RESUMEN ESTADÍSTICO",
            f"   Vulnerabilidades totales: {result.total_vulnerabilities}",
            "",
            f"   Por severidad:",
        ]
        
        for severity, count in sorted(result.by_severity.items()):
            summary_lines.append(f"     - {severity.upper()}: {count}")
        
        summary_lines.extend([
            "",
            f"   Por herramienta:",
        ])
        
        for tool, count in sorted(result.by_tool.items()):
            summary_lines.append(f"     - {tool}: {count}")
        
        summary_lines.extend([
            "",
            f"🔍 VULNERABILIDADES DETALLADAS",
            ""
        ])
        
        for i, vuln in enumerate(result.vulnerabilities, 1):
            if vuln.false_positive:
                continue
                
            summary_lines.extend([
                f"{i}. [{vuln.severity.upper()}] {vuln.tool}: {vuln.vulnerability_id}",
                f"   Archivo: {vuln.file_path}:{vuln.line_number}",
                f"   Mensaje: {vuln.message}",
                f"   CWE: {vuln.cwe_id or 'N/A'}",
                f"   Código:",
                f"   {vuln.code_snippet}",
                ""
            ])
        
        return "\n".join(summary_lines)