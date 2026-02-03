# engine-prototype/src/core/config_validator.py
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

class SASTConfigValidator:
    """Validador de configuración para herramientas SAST"""
    
    def __init__(self, sast_config: Dict[str, Any], project_root: Path = None):
        self.sast_config = sast_config
        self.project_root = project_root or Path.cwd()
        self.warnings = []
        self.errors = []
    
    def validate(self) -> bool:
        """Valida la configuración SAST completa"""
        self.warnings.clear()
        self.errors.clear()
        
        # Validar estructura básica
        self._validate_structure()
        
        # Validar configuración global
        self._validate_global_config()
        
        # Validar herramientas
        self._validate_tools()
        
        # Validar toolchains de lenguaje
        self._validate_language_toolchains()
        
        # Validar exclusiones
        self._validate_exclusions()
        
        # Validar configuración de reportes
        self._validate_reporting()
        
        # Si hay errores, no es válida
        return len(self.errors) == 0
    
    def _validate_structure(self):
        """Valida la estructura básica del archivo de configuración"""
        if not isinstance(self.sast_config, dict):
            self.errors.append("La configuración SAST debe ser un diccionario")
            return
        
        # Secciones esperadas
        expected_sections = ['global', 'tools', 'exclusions', 'reporting']
        
        for section in expected_sections:
            if section not in self.sast_config:
                self.warnings.append(f"Sección '{section}' no encontrada en configuración SAST")
    
    def _validate_global_config(self):
        """Valida la configuración global"""
        global_config = self.sast_config.get('global', {})
        
        # min_severity
        min_severity = global_config.get('min_severity', 'MEDIUM')
        valid_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        if min_severity not in valid_severities:
            self.warnings.append(f"min_severity '{min_severity}' no válido. Usar: {valid_severities}")
        
        # timeout_per_tool
        timeout = global_config.get('timeout_per_tool', 60)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            self.warnings.append(f"timeout_per_tool debe ser un número positivo, no '{timeout}'")
        
        # max_issues_per_file
        max_issues = global_config.get('max_issues_per_file', 50)
        if not isinstance(max_issues, int) or max_issues <= 0:
            self.warnings.append(f"max_issues_per_file debe ser un entero positivo, no '{max_issues}'")
    
    def _validate_tools(self):
        """Valida la configuración de herramientas individuales"""
        tools = self.sast_config.get('tools', {})
        
        if not tools:
            self.warnings.append("No se han configurado herramientas SAST")
            return
        
        required_fields = ['enabled', 'command']
        
        for tool_name, tool_config in tools.items():
            if not isinstance(tool_config, dict):
                self.errors.append(f"Configuración de herramienta '{tool_name}' debe ser un diccionario")
                continue
            
            # Verificar campos requeridos
            for field in required_fields:
                if field not in tool_config:
                    self.warnings.append(f"Herramienta '{tool_name}' no tiene campo '{field}'")
            
            # Validar campo 'enabled'
            enabled = tool_config.get('enabled', False)
            if not isinstance(enabled, bool):
                self.warnings.append(f"Campo 'enabled' de '{tool_name}' debe ser booleano")
            
            # Validar campo 'command'
            command = tool_config.get('command', '')
            if not command:
                self.warnings.append(f"Herramienta '{tool_name}' no tiene comando configurado")
            
            # Validar 'file_extensions'
            extensions = tool_config.get('file_extensions', [])
            if not isinstance(extensions, list):
                self.warnings.append(f"'file_extensions' de '{tool_name}' debe ser una lista")
            elif not extensions:
                self.warnings.append(f"Herramienta '{tool_name}' no tiene extensiones de archivo configuradas")
            
            # Validar 'args'
            args_config = tool_config.get('args', {})
            if not isinstance(args_config, dict):
                self.warnings.append(f"'args' de '{tool_name}' debe ser un diccionario")
            elif 'base' not in args_config:
                self.warnings.append(f"Herramienta '{tool_name}' no tiene argumentos base configurados")
    
    def _validate_language_toolchains(self):
        """Valida las toolchains por lenguaje"""
        language_toolchains = self.sast_config.get('language_toolchains', {})
        
        if not language_toolchains:
            self.warnings.append("No se han configurado toolchains por lenguaje")
            return
        
        valid_languages = ['python', 'c_cpp', 'java', 'javascript', 'go', 'ruby']
        
        for lang, toolchain in language_toolchains.items():
            if not isinstance(toolchain, dict):
                self.errors.append(f"Toolchain de '{lang}' debe ser un diccionario")
                continue
            
            # Verificar que el lenguaje sea conocido
            if lang not in valid_languages:
                self.warnings.append(f"Lenguaje '{lang}' no está en la lista de lenguajes soportados")
            
            # Verificar herramientas primarias
            primary = toolchain.get('primary', [])
            if not isinstance(primary, list):
                self.warnings.append(f"'primary' en toolchain de '{lang}' debe ser una lista")
            elif not primary:
                self.warnings.append(f"Toolchain de '{lang}' no tiene herramientas primarias")
            
            # Verificar que las herramientas existan en la configuración
            all_tools = list(self.sast_config.get('tools', {}).keys())
            for tool in primary:
                if tool not in all_tools:
                    self.warnings.append(f"Herramienta '{tool}' en toolchain de '{lang}' no está definida")
            
            # Verificar herramientas secundarias
            secondary = toolchain.get('secondary', [])
            if secondary and not isinstance(secondary, list):
                self.warnings.append(f"'secondary' en toolchain de '{lang}' debe ser una lista")
    
    def _validate_exclusions(self):
        """Valida la configuración de exclusiones"""
        exclusions = self.sast_config.get('exclusions', {})
        
        if not exclusions:
            return
        
        # Validar exclusiones globales
        global_exclusions = exclusions.get('global', {})
        
        if 'directories' in global_exclusions:
            dirs = global_exclusions['directories']
            if not isinstance(dirs, list):
                self.warnings.append("'exclusions.global.directories' debe ser una lista")
        
        if 'files' in global_exclusions:
            files = global_exclusions['files']
            if not isinstance(files, list):
                self.warnings.append("'exclusions.global.files' debe ser una lista")
    
    def _validate_reporting(self):
        """Valida la configuración de reportes"""
        reporting = self.sast_config.get('reporting', {})
        
        if not reporting:
            self.warnings.append("No se ha configurado la sección 'reporting'")
            return
        
        # Validar formatos
        formats = reporting.get('formats', ['json'])
        if not isinstance(formats, list):
            self.warnings.append("'reporting.formats' debe ser una lista")
        elif not formats:
            self.warnings.append("No se han configurado formatos de reporte")
        
        # Validar directorio de salida
        output_dir = reporting.get('output_dir', '')
        if output_dir:
            try:
                output_path = self.project_root / output_dir
                # Solo verificar que sea una ruta válida
                output_path.resolve()
            except Exception as e:
                self.warnings.append(f"Directorio de salida no válido: {output_dir}")
    
    def get_summary(self) -> Dict[str, List[str]]:
        """Devuelve un resumen de validaciones"""
        return {
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def print_summary(self):
        """Imprime un resumen de validaciones"""
        if self.errors:
            print("❌ Errores de configuración:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("⚠️  Advertencias de configuración:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Configuración SAST válida")


# Funciones de utilidad
def validate_config_file(config_path: str, project_root: str = None) -> Tuple[bool, SASTConfigValidator]:
    """
    Valida un archivo de configuración SAST.
    
    Args:
        config_path: Ruta al archivo de configuración
        project_root: Ruta raíz del proyecto
    
    Returns:
        Tupla (es_válida, validador)
    """
    config_path = Path(config_path)
    project_root = Path(project_root) if project_root else config_path.parent.parent
    
    if not config_path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            sast_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Error parseando YAML: {e}")
        return False, None
    
    validator = SASTConfigValidator(sast_config, project_root)
    is_valid = validator.validate()
    
    return is_valid, validator


def check_required_tools(config_path: str) -> Dict[str, bool]:
    """
    Verifica qué herramientas requeridas están instaladas.
    
    Args:
        config_path: Ruta al archivo de configuración SAST
    
    Returns:
        Diccionario con estado de instalación de herramientas
    """
    try:
        is_valid, validator = validate_config_file(config_path)
        if not is_valid:
            print("❌ Configuración no válida")
            return {}
        
        sast_config = validator.sast_config
        tools_config = sast_config.get('tools', {})
        
        installed = {}
        for tool_name, tool_config in tools_config.items():
            if tool_config.get('enabled', False):
                command = tool_config.get('command', tool_name)
                # Verificar si el comando existe
                try:
                    import subprocess
                    result = subprocess.run([command, '--version'], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=2)
                    installed[tool_name] = result.returncode == 0
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    installed[tool_name] = False
        
        return installed
        
    except Exception as e:
        print(f"❌ Error verificando herramientas: {e}")
        return {}


if __name__ == "__main__":
    # Ejemplo de uso como script independiente
    import sys
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        # Buscar en ubicaciones comunes
        possible_locations = [
            'config/sast_tools.yaml',
            '../config/sast_tools.yaml',
            'sast_tools.yaml'
        ]
        
        for location in possible_locations:
            if Path(location).exists():
                config_file = location
                break
        else:
            print("❌ No se encontró archivo de configuración SAST")
            sys.exit(1)
    
    print(f"🔍 Validando configuración: {config_file}")
    
    is_valid, validator = validate_config_file(config_file)
    
    if validator:
        validator.print_summary()
    
    if is_valid:
        # Verificar herramientas instaladas
        print("\n🔧 Verificando herramientas instaladas:")
        installed_tools = check_required_tools(config_file)
        
        for tool, is_installed in installed_tools.items():
            status = "✅" if is_installed else "❌"
            print(f"  {status} {tool}")
    else:
        sys.exit(1)