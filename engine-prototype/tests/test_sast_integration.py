# tests/test_sast_integration.py
"""
Tests para el módulo de integración SAST
"""

import pytest
from pathlib import Path
import tempfile
import sys

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.sast_integration import SASTScanner, Vulnerability


def test_vulnerability_dataclass():
    """Test que la clase Vulnerability se crea correctamente"""
    vuln = Vulnerability(
        check_id="test-id",
        severity="HIGH",
        message="Test vulnerability",
        path="/test/path.py",
        line=42,
        end_line=45,
        cwe="CWE-120",
        confidence="HIGH",
        fix="Add bounds check",
        language="python"
    )
    
    assert vuln.check_id == "test-id"
    assert vuln.severity == "HIGH"
    assert vuln.line == 42
    assert vuln.cwe == "CWE-120"


def test_scanner_initialization():
    """Test que el scanner se inicializa correctamente"""
    scanner = SASTScanner()
    
    # Debería detectar herramientas disponibles
    assert hasattr(scanner, 'available_tools')
    assert isinstance(scanner.available_tools, dict)
    
    # Configuración por defecto debería existir
    assert 'semgrep' in scanner.config
    assert 'bandit' in scanner.config


def test_is_python_project():
    """Test detección de proyectos Python"""
    scanner = SASTScanner()
    
    # Crear directorio temporal con archivo Python
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Sin archivos Python
        assert not scanner._is_python_project(tmpdir_path)
        
        # Con archivo Python
        py_file = tmpdir_path / "test.py"
        py_file.write_text("print('test')")
        assert scanner._is_python_project(tmpdir_path)


def test_is_cpp_project():
    """Test detección de proyectos C/C++"""
    scanner = SASTScanner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Sin archivos C/C++
        assert not scanner._is_cpp_project(tmpdir_path)
        
        # Con archivo C
        c_file = tmpdir_path / "test.c"
        c_file.write_text("int main() { return 0; }")
        assert scanner._is_cpp_project(tmpdir_path)
        
        # Con archivo .h
        h_file = tmpdir_path / "test.h"
        h_file.write_text("#pragma once")
        assert scanner._is_cpp_project(tmpdir_path)


def test_stats_calculation():
    """Test cálculo de estadísticas de vulnerabilidades"""
    scanner = SASTScanner()
    
    vulns = [
        Vulnerability(
            check_id="test1",
            severity="CRITICAL",
            message="Test 1",
            path="test1.py",
            line=1,
            end_line=None,
            cwe="CWE-120",
            confidence="HIGH",
            fix="",
            language="python"
        ),
        Vulnerability(
            check_id="test2",
            severity="HIGH",
            message="Test 2",
            path="test2.c",
            line=10,
            end_line=None,
            cwe="CWE-89",
            confidence="MEDIUM",
            fix="",
            language="c"
        ),
        Vulnerability(
            check_id="test3",
            severity="CRITICAL",
            message="Test 3",
            path="test3.py",
            line=20,
            end_line=None,
            cwe="CWE-79",
            confidence="HIGH",
            fix="",
            language="python"
        )
    ]
    
    stats = scanner.get_stats(vulns)
    
    assert stats['total'] == 3
    assert stats['by_severity']['CRITICAL'] == 2
    assert stats['by_severity']['HIGH'] == 1
    assert stats['by_language']['python'] == 2
    assert stats['by_language']['c'] == 1


if __name__ == "__main__":
    # Ejecutar tests básicos
    test_vulnerability_dataclass()
    test_scanner_initialization()
    test_is_python_project()
    test_is_cpp_project()
    test_stats_calculation()
    
    print("✅ All SAST integration tests passed!")