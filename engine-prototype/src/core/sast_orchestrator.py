# engine-prototype/src/core/sast_orchestrator.py
import yaml
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
from datetime import datetime


class SASTOrchestrator:
    """Orquestador SAST que integra con la configuración existente de TDH"""

    def __init__(self, project_root: str = None, config_base_path: str = None):
        """
        Inicializa el orquestador SAST.

        Args:
            project_root: Ruta raíz del proyecto a analizar
            config_base_path: Ruta base para configuraciones (por defecto: directorio actual)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_base_path = (
            Path(config_base_path) if config_base_path else self.project_root
        )

        # Cargar configuraciones
        self.main_config = self._load_main_config()
        self.sast_config = self._load_sast_tools_config()

        # Inicializar herramientas disponibles
        self.available_tools = self._detect_available_tools()
        self.results = []
        self.stats = {
            "total_files": 0,
            "total_issues": 0,
            "issues_by_severity": {},
            "issues_by_tool": {},
            "start_time": None,
            "end_time": None,
        }

    def _load_main_config(self) -> Dict[str, Any]:
        """Carga la configuración principal de TDH"""
        config_path = self.config_base_path / "config" / "tdh_config.yaml"

        if not config_path.exists():
            # Si no existe en la ruta base, buscar en el proyecto
            config_path = self.project_root / "config" / "tdh_config.yaml"

        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)

        # Configuración por defecto si no existe
        return {
            "sast": {
                "tools": ["semgrep", "bandit", "cppcheck"],
                "severity_filter": ["CRITICAL", "HIGH", "MEDIUM"],
            }
        }

    def _load_sast_tools_config(self) -> Dict[str, Any]:
        """Carga la configuración específica de herramientas SAST"""
        # Primero intentar cargar desde la configuración principal
        sast_config_file = self.main_config.get("sast", {}).get(
            "config_file", "config/sast_tools.yaml"
        )

        config_paths = [
            self.config_base_path / sast_config_file,
            self.project_root / sast_config_file,
            self.config_base_path / "config" / "sast_tools.yaml",
            self.project_root / "config" / "sast_tools.yaml",
            Path(__file__).parent.parent.parent / "config" / "sast_tools.yaml",
        ]

        for config_path in config_paths:
            if config_path.exists():
                print(f"📋 Cargando configuración SAST desde: {config_path}")
                with open(config_path, "r") as f:
                    return yaml.safe_load(f)

        # Configuración por defecto si no existe
        print("⚠️  No se encontró configuración SAST, usando valores por defecto")
        return {
            "global": {
                "min_severity": "MEDIUM",
                "timeout_per_tool": 60,
                "parallel_execution": False,
            },
            "tools": {
                "semgrep": {
                    "enabled": True,
                    "command": "semgrep",
                    "args": {"base": ["--json", "--quiet", "--config", "auto"]},
                    "file_extensions": [".py", ".js", ".ts", ".java", ".c", ".cpp"],
                },
                "bandit": {
                    "enabled": True,
                    "command": "bandit",
                    "args": {"base": ["-f", "json"]},
                    "file_extensions": [".py"],
                },
            },
        }

    def _detect_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Detecta qué herramientas SAST están instaladas y disponibles"""
        available_tools = {}
        configured_tools = self.sast_config.get("tools", {})

        for tool_name, tool_config in configured_tools.items():
            if not tool_config.get("enabled", False):
                continue

            # Verificar si el comando existe
            command = tool_config.get("command", tool_name)
            is_available = self._check_tool_installed(command)

            if is_available:
                available_tools[tool_name] = {
                    "config": tool_config,
                    "command": command,
                    "args": tool_config.get("args", {}).get("base", []),
                    "available": True,
                }
                print(f"✅ Herramienta '{tool_name}' ({command}) está disponible")
            else:
                print(f"❌ Herramienta '{tool_name}' ({command}) NO está disponible")
                # No la agregamos a available_tools

        print(f"🔧 Herramientas realmente disponibles: {list(available_tools.keys())}")
        return available_tools

    def _check_tool_installed(self, command: str) -> bool:
        """Verifica si una herramienta está instalada"""
        try:
            # Para version
            result = subprocess.run(
                [command, "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            # Intentar con -v o help
            for flag in ["-v", "-V", "--help", "--version"]:
                try:
                    subprocess.run([command, flag], capture_output=True, timeout=2)
                    return True
                except:
                    continue
            return False

    def analyze_directory(self, directory_path: str = None) -> Dict[str, Any]:
        """
        Analiza un directorio completo con las herramientas SAST configuradas.

        Args:
            directory_path: Ruta al directorio a analizar (None = project_root)

        Returns:
            Diccionario con resultados del análisis
        """
        if directory_path is None:
            directory_path = self.project_root
        else:
            directory_path = Path(directory_path)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {directory_path}")

        print(f"🔍 Iniciando análisis SAST en: {directory_path}")
        self.stats["start_time"] = datetime.now()

        # Obtener lista de archivos a analizar
        files_to_analyze = self._get_files_to_analyze(directory_path)
        self.stats["total_files"] = len(files_to_analyze)

        print(f"📄 Encontrados {len(files_to_analyze)} archivos para analizar")

        # Analizar cada archivo
        for file_path in files_to_analyze:
            self.analyze_file(str(file_path))

        self.stats["end_time"] = datetime.now()
        self.stats["total_issues"] = len(self.results)

        # Generar reporte
        report_path = self.generate_report()

        return {"stats": self.stats, "issues": self.results, "report_path": report_path}

    def _get_files_to_analyze(self, directory_path: Path) -> List[Path]:
        """Obtiene la lista de archivos a analizar según extensiones y exclusiones"""
        all_files = []

        # Obtener todas las extensiones de herramientas habilitadas y disponibles
        extensions = set()
        for tool_name, tool_info in self.available_tools.items():
            if tool_info.get("available", False):
                tool_extensions = tool_info["config"].get("file_extensions", [])
                extensions.update(tool_extensions)

        print(f"🔍 Buscando archivos con extensiones: {sorted(extensions)}")

        # Para pruebas, limitar el número de archivos
        max_files_total = 50  # Limitar para pruebas

        for ext in extensions:
            pattern = f"**/*{ext}"
            try:
                # Excluir explícitamente venv y otros directorios no deseados
                files = []
                for f in directory_path.glob(pattern):
                    # EXCLUSIÓN MANUAL DE DIRECTORIOS NO DESEADOS
                    excluded_dirs = [
                        "venv",
                        ".venv",
                        "env",
                        ".env",
                        "__pycache__",
                        "node_modules",
                        ".git",
                        "dist",
                        "build",
                        "target",
                    ]
                    if any(excluded_dir in str(f) for excluded_dir in excluded_dirs):
                        continue
                    files.append(f)

                all_files.extend(files[:10])  # Máximo 10 archivos por extensión
            except Exception as e:
                print(f"   ⚠️  Error buscando archivos {ext}: {e}")

        # Aplicar exclusiones configuradas
        filtered_files = self._apply_exclusions(all_files, directory_path)

        # Limitar el total para pruebas
        if len(filtered_files) > max_files_total:
            print(
                f"📊 Limitando análisis a {max_files_total} archivos (de {len(filtered_files)})"
            )
            filtered_files = filtered_files[:max_files_total]

        return filtered_files

    def _apply_exclusions(self, files: List[Path], base_dir: Path) -> List[Path]:
        """Aplica patrones de exclusión a la lista de archivos"""
        exclusions = self.sast_config.get("exclusions", {})
        global_exclusions = exclusions.get("global", {})

        filtered_files = []

        for file_path in files:
            rel_path = file_path.relative_to(base_dir)
            exclude = False

            # Verificar exclusiones de directorios
            excluded_dirs = global_exclusions.get("directories", [])
            for pattern in excluded_dirs:
                if rel_path.match(pattern):
                    exclude = True
                    break

            # Verificar exclusiones de archivos
            if not exclude:
                excluded_files = global_exclusions.get("files", [])
                for pattern in excluded_files:
                    if rel_path.match(pattern):
                        exclude = True
                        break

            if not exclude:
                filtered_files.append(file_path)

        return filtered_files

    def analyze_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Analiza un archivo individual con herramientas SAST"""
        file_path = Path(filepath)
        if not file_path.exists():
            print(f"❌ Archivo no encontrado: {filepath}")
            return []

        file_ext = file_path.suffix.lower()
        file_issues = []

        # Determinar qué herramientas usar para esta extensión
        tools_for_file = self._get_tools_for_extension(file_ext)

        for tool_name in tools_for_file:
            if (
                tool_name in self.available_tools
                and self.available_tools[tool_name]["available"]
            ):
                print(f"  🛠️  Ejecutando {tool_name} en {file_path.name}...")
                try:
                    issues = self._run_tool(tool_name, str(file_path))
                    file_issues.extend(issues)
                except Exception as e:
                    print(f"    ❌ Error con {tool_name}: {e}")

        # Actualizar estadísticas
        for issue in file_issues:
            self._update_stats(issue)

        self.results.extend(file_issues)
        return file_issues

    def _get_tools_for_extension(self, extension: str) -> List[str]:
        """Devuelve herramientas recomendadas para una extensión específica"""
        # Primero buscar en toolchains por lenguaje
        language_toolchains = self.sast_config.get("language_toolchains", {})

        # Mapeo de extensiones a lenguaje
        extension_to_lang = {
            ".py": "python",
            ".c": "c_cpp",
            ".cpp": "c_cpp",
            ".h": "c_cpp",
            ".hpp": "c_cpp",
            ".java": "java",
            ".js": "javascript",
            ".ts": "javascript",
            ".jsx": "javascript",
            ".tsx": "javascript",
        }

        lang = extension_to_lang.get(extension)
        if lang and lang in language_toolchains:
            toolchain = language_toolchains[lang]
            return toolchain.get("primary", []) + toolchain.get("secondary", [])

        # Fallback: herramientas que soportan esta extensión
        tools_for_ext = []
        for tool_name, tool_info in self.available_tools.items():
            if tool_info["available"]:
                tool_extensions = tool_info["config"].get("file_extensions", [])
                if extension in tool_extensions:
                    tools_for_ext.append(tool_name)

        return tools_for_ext

    def _run_tool(self, tool_name: str, filepath: str) -> List[Dict[str, Any]]:
        """Ejecuta una herramienta específica en un archivo"""
        tool_info = self.available_tools[tool_name]
        command = tool_info["command"]
        args = tool_info["args"]

        try:
            timeout = self.sast_config.get("global", {}).get("timeout_per_tool", 60)

            if tool_name == "cppcheck":
                # Configuración específica para cppcheck
                cmd = [command, "--enable=all", "--xml", "--xml-version=2", filepath]

                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=timeout
                    )

                    # cppcheck escribe XML en stderr, no stdout
                    output = result.stderr if result.stderr else result.stdout
        
                    # DEBUG: Mostrar qué estamos parseando
                    if output:
                        print(f"    📄 Parseando cppcheck (primeras 500 chars): {output[:500]}")
        
                    return self._parse_cppcheck_output(output, filepath)

                except subprocess.TimeoutExpired:
                    print(f"    ⏰ cppcheck excedió el tiempo límite")
                    return []
                except Exception as e:
                    print(f"    ❌ Error ejecutando cppcheck: {e}")
                    return []
            else:
                # Para otras herramientas
                full_args = args + [filepath]
                result = subprocess.run(
                    [command] + full_args,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                # Parsear salida según la herramienta
                if tool_name == "semgrep":
                    return self._parse_semgrep_output(result.stdout, filepath)
                elif tool_name == "bandit":
                    return self._parse_bandit_output(result.stdout, filepath)
                else:
                    # Parseo genérico
                    return self._parse_generic_output(
                        tool_name, result.stdout, filepath
                    )

        except subprocess.TimeoutExpired:
            print(f"    ⏰ {tool_name} excedió el tiempo límite")
            return []
        except Exception as e:
            print(f"    ❌ Error ejecutando {tool_name}: {e}")
            return []

    def _parse_semgrep_output(self, output: str, filepath: str) -> List[Dict[str, Any]]:
        """Parsea la salida de semgrep"""
        issues = []

        try:
            data = json.loads(output)
            for finding in data.get("results", []):
                severity = finding.get("extra", {}).get("severity", "MEDIUM").upper()

                # Filtrar por severidad mínima
                min_severity = self.sast_config.get("global", {}).get(
                    "min_severity", "MEDIUM"
                )
                severity_order = {
                    "CRITICAL": 0,
                    "HIGH": 1,
                    "MEDIUM": 2,
                    "LOW": 3,
                    "INFO": 4,
                }

                if severity_order.get(severity, 99) > severity_order.get(
                    min_severity, 99
                ):
                    continue

                issues.append(
                    {
                        "tool": "semgrep",
                        "rule_id": finding.get("check_id", ""),
                        "severity": severity,
                        "message": finding.get("extra", {}).get("message", ""),
                        "file": filepath,
                        "line": finding.get("start", {}).get("line", 0),
                        "end_line": finding.get("end", {}).get("line", 0),
                        "confidence": finding.get("extra", {}).get(
                            "confidence", "MEDIUM"
                        ),
                        "category": finding.get("extra", {})
                        .get("metadata", {})
                        .get("category", ""),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        except json.JSONDecodeError as e:
            print(f"    ❌ Error parseando JSON de semgrep: {e}")

        return issues

    def _parse_bandit_output(self, output: str, filepath: str) -> List[Dict[str, Any]]:
        """Parsea la salida de bandit"""
        issues = []

        try:
            data = json.loads(output)
            for issue in data.get("results", []):
                severity = issue.get("issue_severity", "MEDIUM").upper()

                issues.append(
                    {
                        "tool": "bandit",
                        "rule_id": issue.get("test_id", ""),
                        "severity": severity,
                        "message": issue.get("issue_text", ""),
                        "file": filepath,
                        "line": issue.get("line_number", 0),
                        "confidence": issue.get("issue_confidence", "MEDIUM"),
                        "more_info": issue.get("more_info", ""),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        except json.JSONDecodeError as e:
            print(f"    ❌ Error parseando JSON de bandit: {e}")

        return issues

    def _parse_cppcheck_output(self, output: str, filepath: str) -> List[Dict[str, Any]]:
        """Parsea la salida de cppcheck (XML o texto)"""
        issues = []
        
        if not output.strip():
            return issues
        
        # Obtener configuración para mapeo de severidades
        cppcheck_config = self.sast_config.get('tools', {}).get('cppcheck', {})
        severity_mapping = cppcheck_config.get('severity_mapping', {})
        
        # Intentar parsear como XML
        if '<?xml' in output:
            try:
                import xml.etree.ElementTree as ET
                from xml.parsers.expat import ExpatError
                
                # Intentar parsear
                try:
                    root = ET.fromstring(output)
                except ExpatError:
                    # Intentar limpiar líneas problemáticas
                    lines = output.split('\n')
                    clean_lines = [l for l in lines if not l.strip().startswith('Checking')]
                    clean_output = '\n'.join(clean_lines)
                    root = ET.fromstring(clean_output)
                
                # Procesar errores
                for error in root.findall('.//error'):
                    severity = error.get('severity', 'information').lower()
                    error_id = error.get('id', '')
                    
                    # MAPEAR SEVERIDAD CORRECTAMENTE
                    mapped_severity = severity_mapping.get(severity, 'INFO')
                    
                    # Obtener línea y columna
                    line = error.get('line', '0')
                    column = error.get('column', '0')
                    
                    issue = {
                        'tool': 'cppcheck',
                        'rule_id': error_id,
                        'severity': mapped_severity,
                        'message': error.get('msg', ''),
                        'file': filepath,
                        'line': int(line) if line.isdigit() else 0,
                        'column': int(column) if column.isdigit() else 0,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # APLICAR FILTRO
                    if self._should_include_issue(issue, 'cppcheck'):
                        issues.append(issue)
                
                return issues
                
            except Exception as e:
                print(f"    ⚠️  Error parseando XML de cppcheck: {e}")
                # Continuar con parsing de texto

        # Parsear como texto (formato por defecto)
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Formato típico de cppcheck: [archivo:linea] (severidad) mensaje
            if line.startswith("[") and "]" in line:
                parts = line.split("]", 1)
                location = parts[0][1:]  # Quitar el '['
                rest = parts[1].strip() if len(parts) > 1 else ""

                # Extraer archivo y línea
                if ":" in location:
                    file_part, line_part = location.split(":", 1)
                    try:
                        line_num = int(line_part.strip())
                    except ValueError:
                        line_num = 0
                else:
                    line_num = 0

                # Extraer severidad y mensaje
                severity = "MEDIUM"
                if "(error)" in rest:
                    severity = "ERROR"
                    rest = rest.replace("(error)", "").strip()
                elif "(warning)" in rest:
                    severity = "WARNING"
                    rest = rest.replace("(warning)", "").strip()
                elif "(style)" in rest:
                    severity = "STYLE"
                    rest = rest.replace("(style)", "").strip()
                elif "(performance)" in rest:
                    severity = "PERFORMANCE"
                    rest = rest.replace("(performance)", "").strip()

                # Mapear a severidades estándar
                severity_map = {
                    "ERROR": "CRITICAL",
                    "WARNING": "HIGH",
                    "STYLE": "MEDIUM",
                    "PERFORMANCE": "LOW",
                }

                issues.append(
                    {
                        "tool": "cppcheck",
                        "severity": severity_map.get(severity, "MEDIUM"),
                        "message": rest,
                        "file": filepath,
                        "line": line_num,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return issues

    def _parse_generic_output(
        self, tool_name: str, output: str, filepath: str
    ) -> List[Dict[str, Any]]:
        """Parsea salida genérica de herramientas"""
        issues = []

        # Intentar parsear como JSON
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for item in data:
                    issues.append(
                        {
                            "tool": tool_name,
                            "severity": "MEDIUM",
                            "message": str(item),
                            "file": filepath,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
        except:
            # Si no es JSON, tratar como texto
            for line in output.split("\n"):
                if line.strip():
                    issues.append(
                        {
                            "tool": tool_name,
                            "severity": "INFO",
                            "message": line.strip(),
                            "file": filepath,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        return issues

    def _update_stats(self, issue: Dict[str, Any]):
        """Actualiza estadísticas con un nuevo issue"""
        severity = issue.get("severity", "UNKNOWN")
        tool = issue.get("tool", "UNKNOWN")

        # Contar por severidad
        self.stats["issues_by_severity"][severity] = (
            self.stats["issues_by_severity"].get(severity, 0) + 1
        )

        # Contar por herramienta
        self.stats["issues_by_tool"][tool] = (
            self.stats["issues_by_tool"].get(tool, 0) + 1
        )

    def generate_report(self, output_format: str = None, output_dir: str = None) -> str:
        """Genera un reporte con los resultados del análisis"""
        if output_format is None:
            output_format = self.sast_config.get("reporting", {}).get(
                "default_format", "json"
            )

        if output_dir is None:
            output_dir = self.sast_config.get("reporting", {}).get(
                "output_dir", "reports/sast"
            )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format == "json":
            return self._generate_json_report(output_path, timestamp)
        elif output_format == "console":
            self._generate_console_report()
            return "console"
        else:
            print(f"⚠️  Formato de reporte no soportado: {output_format}, usando JSON")
            return self._generate_json_report(output_path, timestamp)

    def _generate_json_report(self, output_dir: Path, timestamp: str) -> str:
        """Genera un reporte en formato JSON"""
        report_data = {
            "metadata": {
                "project": str(self.project_root),
                "scan_id": timestamp,
                "start_time": (
                    self.stats["start_time"].isoformat()
                    if self.stats["start_time"]
                    else None
                ),
                "end_time": (
                    self.stats["end_time"].isoformat()
                    if self.stats["end_time"]
                    else None
                ),
                "duration_seconds": (
                    (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
                    if self.stats["start_time"] and self.stats["end_time"]
                    else None
                ),
                "tdh_version": self.main_config.get("engine", {}).get(
                    "version", "0.1.0"
                ),
            },
            "statistics": self.stats,
            "issues": self.results,
            "configuration": {
                "tools_used": [
                    name
                    for name, info in self.available_tools.items()
                    if info["available"]
                ],
                "sast_config": self.sast_config.get("global", {}),
            },
        }

        report_path = output_dir / f"sast_report_{timestamp}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"📊 Reporte JSON generado: {report_path}")
        return str(report_path)

    def _generate_console_report(self):
        """Muestra un resumen del análisis en consola"""
        print("\n" + "=" * 60)
        print("SAST ANALYSIS REPORT")
        print("=" * 60)

        # Información básica
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()
            print(f"⏱️  Duración: {duration:.2f} segundos")

        print(f"📄 Archivos analizados: {self.stats['total_files']}")
        print(f"⚠️  Issues encontrados: {self.stats['total_issues']}")

        # Issues por severidad
        if self.stats["issues_by_severity"]:
            print("\n📊 Issues por severidad:")
            for severity, count in sorted(self.stats["issues_by_severity"].items()):
                print(f"  {severity}: {count}")

        # Issues por herramienta
        if self.stats["issues_by_tool"]:
            print("\n🛠️  Issues por herramienta:")
            for tool, count in sorted(self.stats["issues_by_tool"].items()):
                print(f"  {tool}: {count}")

        # Issues críticos/altos
        critical_issues = [
            issue
            for issue in self.results
            if issue.get("severity") in ["CRITICAL", "HIGH"]
        ]

        if critical_issues:
            print(f"\n⛔ Issues CRÍTICOS/ALTOS encontrados ({len(critical_issues)}):")
            for i, issue in enumerate(critical_issues[:10], 1):
                print(f"  {i}. [{issue.get('tool')}] {issue.get('message', '')}")
                print(f"     📍 {issue.get('file')}:{issue.get('line', 0)}")

            if len(critical_issues) > 10:
                print(f"     ... y {len(critical_issues) - 10} más")

        print("=" * 60)

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Determina si un archivo debe ser excluido del análisis"""
        
        exclusion_patterns = [
            # Directorios
            "**/venv/**",
            "**/.venv/**",
            "**/env/**",
            "**/.env/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
            "**/target/**",
            "**/.idea/**",
            "**/.vscode/**",
            
            # Archivos específicos
            "**/*.min.js",
            "**/*.min.css",
            "**/*.bundle.js",
            "**/*.log",
            "**/package-lock.json",
            "**/yarn.lock",
        ]
        
        for pattern in exclusion_patterns:
            if file_path.match(pattern):
                return True
        
        return False

    def _should_include_issue(self, issue: Dict[str, Any], tool_name: str) -> bool:
        """Determina si un issue debe ser incluido basado en severidad y filtros"""
        
        # Obtener severidad mínima configurada
        min_severity = self.sast_config.get('global', {}).get('min_severity', 'MEDIUM')
        
        # Orden de severidad (de mayor a menor)
        severity_order = {
            'CRITICAL': 0,
            'HIGH': 1,
            'MEDIUM': 2,
            'LOW': 3,
            'INFO': 4,
            'UNKNOWN': 5
        }
        
        issue_severity = issue.get('severity', 'UNKNOWN')
        issue_level = severity_order.get(issue_severity, 99)
        min_level = severity_order.get(min_severity, 99)
        
        # Si el issue es menos severo que el mínimo, excluirlo
        if issue_level > min_level:
            return False
        
        # Filtros específicos por herramienta
        if tool_name == 'cppcheck':
            return self._filter_cppcheck_issue(issue)
        elif tool_name == 'bandit':
            return self._filter_bandit_issue(issue)
        elif tool_name == 'semgrep':
            return self._filter_semgrep_issue(issue)
        
        return True

    def _filter_cppcheck_issue(self, issue: Dict[str, Any]) -> bool:
        """Filtra issues específicos de cppcheck que no son relevantes"""
        
        rule_id = issue.get('rule_id', '').lower()
        message = issue.get('message', '').lower()
        
        # Lista de issues de cppcheck que normalmente son falsos positivos o no útiles
        cppcheck_noise = [
            'checkersreport',
            'missingincludesystem',
            'missinginclude',
            'unusedfunction',
            'unreadvariable',
            'unusedvariable',
            'variablehidesvariable',
            'functionstatic',
            'funcioneshouldbestatic',
            'stylistic'
        ]
        
        for noise in cppcheck_noise:
            if noise in rule_id or noise in message:
                return False
        
        # Mantener solo issues de seguridad reales
        security_keywords = [
            'buffer',
            'overflow',
            'injection',
            'format',
            'string',
            'race',
            'deadlock',
            'memory',
            'leak',
            'use after free',
            'double free',
            'null pointer',
            'dereference',
            'insecure',
            'vulnerability'
        ]
        
        # Si el issue NO tiene palabras clave de seguridad, puede ser ruido
        has_security_keyword = any(keyword in message for keyword in security_keywords)
        
        # Si es INFO y no tiene keywords de seguridad, excluirlo
        if issue.get('severity') == 'INFO' and not has_security_keyword:
            return False
        
        return True

    def _filter_bandit_issue(self, issue: Dict[str, Any]) -> bool:
        """Filtra issues específicos de bandit"""
        
        rule_id = issue.get('rule_id', '').lower()
        message = issue.get('message', '').lower()
        
        # Bandit issues a mantener (todos son de seguridad)
        return True  # Bandit ya filtra por seguridad

    def _filter_semgrep_issue(self, issue: Dict[str, Any]) -> bool:
        """Filtra issues específicos de semgrep"""
        
        rule_id = issue.get('rule_id', '').lower()
        message = issue.get('message', '').lower()
        
        # Semgrep issues a mantener
        return True  # Semgrep ya filtra por seguridad

# Función de conveniencia para uso rápido
def run_sast_analysis(
    project_path: str = ".", config_path: str = None
) -> Dict[str, Any]:
    """
    Función de conveniencia para ejecutar análisis SAST.

    Args:
        project_path: Ruta al proyecto a analizar
        config_path: Ruta base para configuraciones

    Returns:
        Resultados del análisis
    """
    orchestrator = SASTOrchestrator(project_path, config_path)
    return orchestrator.analyze_directory()
