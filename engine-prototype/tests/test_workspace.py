# tests/test_workspace.py
"""
Tests para el módulo de gestión de workspaces
"""

import pytest
from pathlib import Path
import tempfile
import sys
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.workspace import WorkspaceManager, Workspace, create_test_workspace
from datetime import datetime


def test_workspace_creation():
    """Test creación básica de workspace"""
    workspace = Workspace(
        id="test123",
        path=Path("/tmp/test"),
        source_url="https://github.com/test/repo"
    )
    
    assert workspace.id == "test123"
    assert workspace.path == Path("/tmp/test")
    assert workspace.source_url == "https://github.com/test/repo"
    assert workspace.created_at is not None
    assert workspace.last_used is not None


def test_manager_initialization():
    """Test inicialización del gestor"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorkspaceManager(base_dir=tmpdir)
        
        assert manager.base_dir == Path(tmpdir)
        assert manager.base_dir.exists()
        assert isinstance(manager.workspaces, dict)


def test_create_empty_workspace():
    """Test creación de workspace vacío"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorkspaceManager(base_dir=tmpdir)
        
        workspace = manager.create_empty("test")
        
        assert workspace.id.startswith("test_")
        assert workspace.path.exists()
        assert workspace.path.is_dir()
        
        # Verificar que se guardó en el manager
        assert workspace.id in manager.workspaces
        
        # Limpiar
        manager.delete_workspace(workspace.id)


def test_create_from_local():
    """Test creación copiando directorio local"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crear directorio fuente con contenido
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        
        test_file = source_dir / "test.txt"
        test_file.write_text("Hello World")
        
        # Crear manager y workspace
        manager = WorkspaceManager(base_dir=Path(tmpdir) / "workspaces")
        workspace = manager.create_from_local(str(source_dir))
        
        # Verificar que se copió el contenido
        copied_file = workspace.path / "test.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "Hello World"
        
        # Limpiar
        manager.delete_workspace(workspace.id)


def test_execute_in_workspace():
    """Test ejecución de comandos en workspace"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorkspaceManager(base_dir=tmpdir)
        workspace = manager.create_empty("test")
        
        # Escribir script simple
        script_file = workspace.path / "test_script.sh"
        script_file.write_text("echo 'TDH Engine Test'")
        script_file.chmod(0o755)  # Hacer ejecutable
        
        # Ejecutar comando
        result = manager.execute_in_workspace(
            workspace.id,
            ["./test_script.sh"]
        )
        
        assert result['success'] is True
        assert 'TDH Engine Test' in result['stdout']
        
        # Limpiar
        manager.delete_workspace(workspace.id)


def test_apply_patch():
    """Test aplicación de parches"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorkspaceManager(base_dir=tmpdir)
        workspace = manager.create_empty("test")
        
        # Crear archivo original
        original_file = workspace.path / "file.txt"
        original_file.write_text("Line 1\nLine 2\nLine 3\n")
        
        # Crear parche
        patch_content = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,4 @@
 Line 1
 Line 2
+New line added
 Line 3
"""
        
        # Aplicar parche
        success = manager.apply_patch(workspace.id, patch_content)
        
        assert success is True
        assert "New line added" in original_file.read_text()
        
        # Limpiar
        manager.delete_workspace(workspace.id)


def test_list_files():
    """Test listado de archivos en workspace"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorkspaceManager(base_dir=tmpdir)
        workspace = manager.create_empty("test")
        
        # Crear varios archivos
        (workspace.path / "file1.txt").write_text("test1")
        (workspace.path / "subdir" / "file2.txt").mkdir(parents=True)
        (workspace.path / "subdir" / "file2.txt").write_text("test2")
        
        # Listar archivos
        files = manager.list_files(workspace.id)
        
        assert len(files) == 2
        assert any("file1.txt" in str(f) for f in files)
        assert any("file2.txt" in str(f) for f in files)
        
        # Limpiar
        manager.delete_workspace(workspace.id)


def test_create_test_workspace():
    """Test función de utilidad create_test_workspace"""
    code_content = """
def vulnerable_function(input_data):
    buffer = [0] * 64
    for i in range(len(input_data)):
        buffer[i] = input_data[i]  # Potential buffer overflow
    return buffer
"""
    
    workspace = create_test_workspace(code_content, "python")
    
    # Verificar que se creó el archivo
    files = list(workspace.path.glob("*.py"))
    assert len(files) == 1
    
    # Verificar contenido
    assert "vulnerable_function" in files[0].read_text()
    
    # Limpiar (el workspace usa su propio manager interno)
    import shutil
    if workspace.path.exists():
        shutil.rmtree(workspace.path, ignore_errors=True)


if __name__ == "__main__":
    print("🧪 Running workspace tests...")
    
    test_workspace_creation()
    print("✅ test_workspace_creation passed")
    
    test_manager_initialization()
    print("✅ test_manager_initialization passed")
    
    test_create_empty_workspace()
    print("✅ test_create_empty_workspace passed")
    
    test_create_from_local()
    print("✅ test_create_from_local passed")
    
    test_execute_in_workspace()
    print("✅ test_execute_in_workspace passed")
    
    test_apply_patch()
    print("✅ test_apply_patch passed")
    
    test_list_files()
    print("✅ test_list_files passed")
    
    test_create_test_workspace()
    print("✅ test_create_test_workspace passed")
    
    print("\n🎉 All workspace tests passed!")