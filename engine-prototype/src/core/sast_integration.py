"""
SAST Integration Module
Integración con herramientas SAST gratuitas: Semgrep, Bandit, Cppcheck
"""

import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import yaml


@dataclass
class Vulnerability:
    """Representa una vulnerabilidad encontrada por SAST"""
    check_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    path: str
    line: int
    end_line: Optional[int]
    cwe: Optional[str]
    confidence: str  # HIGH, MEDIUM, LOW
    fix: Optional[str]
    language: str


class SASTScanner:
    """Scanner integrado de múltiples herramientas SAST"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.available_tools = self._detect_tools()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Cargar configuración desde archivo"""
        default_config = {
            'semgrep': {
                'enabled': True,
                'configs': ['p/security-audit', 'p/ci'],
                'severity': ['CRITICAL', 'HIGH', 'MEDIUM']
            },
            'bandit': {
                'enabled': True,
                'severity': ['HIGH', 'MEDIUM'],
                'confidence': ['HIGH', 'MEDIUM']
            },
            'cppcheck': {
                'enabled': True,
                'checks': ['all'],
                'severity': ['error', 'warning']
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                # Merge configs
                default_config.update(user_config.get('sast', {}))
        
        return default_config
    
    def _detect_tools(self) -> Dict[str, bool]:
        """Detectar qué herramientas SAST están disponibles"""
        tools = {}
        
        # Check Semgrep
        try:
            subprocess.run(['semgrep', '--version'], 
                         capture_output=True, check=False)
            tools['semgrep'] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            tools['semgrep'] = False
            
        # Check Bandit
        try:
            subprocess.run(['bandit', '--version'], 
                         capture_output=True, check=False)
            tools['bandit'] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            tools['bandit'] = False
            
        # Check Cppcheck
        try:
            subprocess.run(['cppcheck', '--version'], 
                         capture_output=True, check=False)
            tools['cppcheck'] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            tools['cppcheck'] = False
            
        return tools
    
    def scan(self, target_path: str) -> List[Vulnerability]:
        """
        Escanear un directorio o archivo con todas las herramientas disponibles
        
        Args:
            target_path: Ruta al directorio o archivo a escanear
            
        Returns:
            Lista de vulnerabilidades encontradas
        """
        all_vulns = []
        
        # Expandir path
        target_path = Path(target_path).resolve()
        
        if not target_path.exists():
            raise FileNotFoundError(f"Target path not found: {target_path}")
            
        print(f"🔍 Scanning {target_path}...")
        
        # Ejecutar cada herramienta habilitada
        if self.available_tools.get('semgrep') and self.config['semgrep']['enabled']:
            all_vulns.extend(self._run_semgrep(target_path))
            
        if self.available_tools.get('bandit') and self.config['bandit']['enabled']:
            # Solo para Python
            if self._is_python_project(target_path):
                all_vulns.extend(self._run_bandit(target_path))
                
        if self.available_tools.get('cppcheck') and self.config['cppcheck']['enabled']:
            # Solo para C/C++
            if self._is_cpp_project(target_path):
                all_vulns.extend(self._run_cppcheck(target_path))
        
        # Filtrar por severidad
        min_severity = self.config.get('min_severity', 'MEDIUM')
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        min_index = severity_order.index(min_severity)
        
        filtered_vulns = [
            v for v in all_vulns 
            if severity_order.index(v.severity) <= min_index
        ]
        
        # Ordenar por severidad (CRITICAL primero)
        filtered_vulns.sort(key=lambda x: severity_order.index(x.severity))
        
        return filtered_vulns
    
    def _run_semgrep(self, target_path: Path) -> List[Vulnerability]:
        """Ejecutar Semgrep y parsear resultados"""
        vulns = []
        
        try:
            # Crear archivo temporal para output JSON
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Construir comando Semgrep
            cmd = [
                'semgrep', 'scan',
                '--config', 'auto',  # Usar configs automáticas
                '--json', '-o', tmp_path,
                '--quiet',  # Menos output
                str(target_path)
            ]
            
            # Agregar filtros de severidad
            if 'severity' in self.config['semgrep']:
                for sev in self.config['semgrep']['severity']:
                    cmd.extend(['--severity', sev])
            
            # Ejecutar
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(tmp_path).stat().st_size > 0:
                with open(tmp_path) as f:
                    data = json.load(f)
                
                # Parsear resultados
                for result in data.get('results', []):
                    vuln = Vulnerability(
                        check_id=result.get('check_id', 'unknown'),
                        severity=result.get('extra', {}).get('severity', 'MEDIUM').upper(),
                        message=result.get('extra', {}).get('message', 'No message'),
                        path=result.get('path', ''),
                        line=result.get('start', {}).get('line', 0),
                        end_line=result.get('end', {}).get('line'),
                        cwe=self._extract_cwe(result),
                        confidence=result.get('extra', {}).get('confidence', 'MEDIUM').upper(),
                        fix=result.get('extra', {}).get('fix', ''),
                        language=result.get('extra', {}).get('metadata', {}).get('language', 'unknown')
                    )
                    vulns.append(vuln)
            
            # Limpiar archivo temporal
            Path(tmp_path).unlink(missing_ok=True)
            
        except Exception as e:
            print(f"⚠️  Semgrep error: {e}")
            
        return vulns
    
    def _run_bandit(self, target_path: Path) -> List[Vulnerability]:
        """Ejecutar Bandit (solo Python)"""
        vulns = []
        
        try:
            # Archivo temporal para output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Construir comando Bandit
            cmd = [
                'bandit', '-r', str(target_path),
                '-f', 'json', '-o', tmp_path,
                '-q'  # Quiet mode
            ]
            
            # Filtros de severidad/confianza
            if 'severity' in self.config['bandit']:
                cmd.extend(['-l', ','.join(self.config['bandit']['severity'])])
            
            if 'confidence' in self.config['bandit']:
                cmd.extend(['-i', ','.join(self.config['bandit']['confidence'])])
            
            # Ejecutar
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if Path(tmp_path).stat().st_size > 0:
                with open(tmp_path) as f:
                    data = json.load(f)
                
                # Parsear resultados
                for result in data.get('results', []):
                    vuln = Vulnerability(
                        check_id=result.get('test_id', 'unknown'),
                        severity=result.get('issue_severity', 'MEDIUM').upper(),
                        message=result.get('issue_text', 'No message'),
                        path=result.get('filename', ''),
                        line=result.get('line_number', 0),
                        end_line=None,
                        cwe=result.get('issue_cwe', {}).get('id') if isinstance(result.get('issue_cwe'), dict) else None,
                        confidence=result.get('issue_confidence', 'MEDIUM').upper(),
                        fix='',  # Bandit no provee fixes
                        language='python'
                    )
                    vulns.append(vuln)
            
            # Limpiar
            Path(tmp_path).unlink(missing_ok=True)
            
        except Exception as e:
            print(f"⚠️  Bandit error: {e}")
            
        return vulns
    
    def _run_cppcheck(self, target_path: Path) -> List[Vulnerability]:
        """Ejecutar Cppcheck (solo C/C++)"""
        vulns = []
        
        try:
            # Cppcheck no tiene output JSON nativo, usamos XML
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Construir comando
            cmd = [
                'cppcheck', '--enable=all',
                '--xml', '--xml-version=2',
                '--output-file=' + tmp_path,
                '--quiet',
                str(target_path)
            ]
            
            # Ejecutar
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if Path(tmp_path).stat().st_size > 0:
                # Parsear XML (simplificado)
                import xml.etree.ElementTree as ET
                tree = ET.parse(tmp_path)
                root = tree.getroot()
                
                for error in root.findall('errors/error'):
                    severity = error.get('severity', 'warning').upper()
                    
                    # Mapear severidad de cppcheck a nuestro formato
                    severity_map = {
                        'error': 'HIGH',
                        'warning': 'MEDIUM',
                        'style': 'LOW',
                        'performance': 'LOW',
                        'portability': 'LOW'
                    }
                    
                    mapped_severity = severity_map.get(severity.lower(), 'MEDIUM')
                    
                    vuln = Vulnerability(
                        check_id=error.get('id', 'unknown'),
                        severity=mapped_severity,
                        message=error.get('msg', 'No message'),
                        path=error.get('file', ''),
                        line=int(error.get('line', 0)),
                        end_line=None,
                        cwe=None,  # cppcheck no provee CWE
                        confidence='MEDIUM',
                        fix='',
                        language='cpp'
                    )
                    vulns.append(vuln)
            
            # Limpiar
            Path(tmp_path).unlink(missing_ok=True)
            
        except Exception as e:
            print(f"⚠️  Cppcheck error: {e}")
            
        return vulns
    
    def _is_python_project(self, path: Path) -> bool:
        """Verificar si el proyecto contiene código Python"""
        python_files = list(path.rglob('*.py'))
        return len(python_files) > 0
    
    def _is_cpp_project(self, path: Path) -> bool:
        """Verificar si el proyecto contiene código C/C++"""
        cpp_exts = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']
        for ext in cpp_exts:
            if list(path.rglob(f'*{ext}')):
                return True
        return False
    
    def _extract_cwe(self, semgrep_result: Dict) -> Optional[str]:
        """Extraer CWE de los metadatos de Semgrep"""
        metadata = semgrep_result.get('extra', {}).get('metadata', {})
        
        # Intentar varios campos comunes
        cwe = metadata.get('cwe')
        if cwe:
            if isinstance(cwe, list):
                return cwe[0] if cwe else None
            return str(cwe)
        
        # Buscar en references
        references = metadata.get('references', [])
        for ref in references:
            if isinstance(ref, str) and 'CWE-' in ref:
                return ref.split('CWE-')[1].split(' ')[0].strip()
        
        return None
    
    def get_stats(self, vulns: List[Vulnerability]) -> Dict[str, Any]:
        """Obtener estadísticas de las vulnerabilidades encontradas"""
        stats = {
            'total': len(vulns),
            'by_severity': {},
            'by_language': {},
            'by_tool': {}
        }
        
        for vuln in vulns:
            # Por severidad
            stats['by_severity'][vuln.severity] = stats['by_severity'].get(vuln.severity, 0) + 1
            
            # Por lenguaje
            stats['by_language'][vuln.language] = stats['by_language'].get(vuln.language, 0) + 1
            
            # Por herramienta (inferido del check_id)
            tool = 'unknown'
            if 'semgrep' in vuln.check_id.lower():
                tool = 'semgrep'
            elif 'bandit' in vuln.check_id.lower():
                tool = 'bandit'
            elif 'cppcheck' in vuln.check_id.lower():
                tool = 'cppcheck'
            
            stats['by_tool'][tool] = stats['by_tool'].get(tool, 0) + 1
        
        return stats


if __name__ == '__main__':
    # Ejemplo de uso
    scanner = SASTScanner()
    
    # Escanear directorio actual
    vulns = scanner.scan('.')
    
    print(f"Found {len(vulns)} vulnerabilities")
    
    # Mostrar las CRÍTICAS
    critical_vulns = [v for v in vulns if v.severity == 'CRITICAL']
    for vuln in critical_vulns[:5]:  # Mostrar primeras 5
        print(f"  {vuln.severity}: {vuln.message} ({vuln.path}:{vuln.line})")