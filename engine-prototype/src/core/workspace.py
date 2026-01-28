"""
Workspace Management Module
Gestión de espacios de trabajo aislados para análisis de código
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Workspace:
    """Representa un espacio de trabajo aislado"""
    id: str
    path: Path
    source_url: Optional[str] = None
    created_at: datetime = None
    last_used: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_used is None:
            self.last_used = self.created_at
        if self.metadata is None:
            self.metadata = {}


class WorkspaceManager:
    """Gestor de espacios de trabajo para análisis de código"""
    
    def __init__(self, base_dir: Optional[str] = None, max_workspaces: int = 10):
        """
        Inicializar el gestor de workspaces
        
        Args:
            base_dir: Directorio base para workspaces (opcional)
            max_workspaces: Número máximo de workspaces a mantener
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Usar directorio temporal por defecto
            self.base_dir = Path(tempfile.gettempdir()) / "tdh_workspaces"
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.max_workspaces = max_workspaces
        self.workspaces: Dict[str, Workspace] = {}
        self._load_workspaces()
    
    def _load_workspaces(self):
        """Cargar workspaces existentes desde disco"""
        state_file = self.base_dir / "workspaces.json"
        
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                
                for ws_id, ws_data in data.items():
                    # Convertir strings a Path y datetime
                    ws_data['path'] = Path(ws_data['path'])
                    ws_data['created_at'] = datetime.fromisoformat(ws_data['created_at'])
                    ws_data['last_used'] = datetime.fromisoformat(ws_data['last_used'])
                    
                    self.workspaces[ws_id] = Workspace(**ws_data)
            except Exception as e:
                print(f"⚠️  Error loading workspaces: {e}")
    
    def _save_workspaces(self):
        """Guardar estado de workspaces a disco"""
        state_file = self.base_dir / "workspaces.json"
        
        data = {}
        for ws_id, workspace in self.workspaces.items():
            # Convertir Path y datetime a strings serializables
            ws_dict = asdict(workspace)
            ws_dict['path'] = str(ws_dict['path'])
            ws_dict['created_at'] = ws_dict['created_at'].isoformat()
            ws_dict['last_used'] = ws_dict['last_used'].isoformat()
            data[ws_id] = ws_dict
        
        with open(state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_from_url(self, repo_url: str, branch: Optional[str] = None) -> Workspace:
        """
        Crear workspace clonando un repositorio Git
        
        Args:
            repo_url: URL del repositorio Git
            branch: Rama específica (opcional)
            
        Returns:
            Workspace creado
        """
        # Generar ID único basado en la URL
        ws_id = hashlib.md5(f"{repo_url}:{branch}".encode()).hexdigest()[:8]
        
        # Si ya existe, reutilizar
        if ws_id in self.workspaces:
            print(f"📁 Reusing existing workspace: {ws_id}")
            self.workspaces[ws_id].last_used = datetime.now()
            self._save_workspaces()
            return self.workspaces[ws_id]
        
        # Crear nuevo workspace
        ws_path = self.base_dir / ws_id
        ws_path.mkdir(exist_ok=True)
        
        print(f"📥 Cloning {repo_url} to {ws_path}...")
        
        # Comando git clone
        cmd = ['git', 'clone']
        
        if branch:
            cmd.extend(['-b', branch])
        
        cmd.extend([repo_url, str(ws_path)])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            workspace = Workspace(
                id=ws_id,
                path=ws_path,
                source_url=repo_url,
                metadata={
                    'branch': branch,
                    'clone_success': True,
                    'clone_output': result.stdout[:500]  # Guardar primeros 500 chars
                }
            )
            
            self.workspaces[ws_id] = workspace
            self._cleanup_old_workspaces()
            self._save_workspaces()
            
            return workspace
            
        except subprocess.CalledProcessError as e:
            # Limpiar en caso de error
            if ws_path.exists():
                shutil.rmtree(ws_path, ignore_errors=True)
            raise RuntimeError(f"Git clone failed: {e.stderr}")
    
    def create_from_local(self, local_path: str) -> Workspace:
        """
        Crear workspace copiando un directorio local
        
        Args:
            local_path: Ruta al directorio local
            
        Returns:
            Workspace creado
        """
        source_path = Path(local_path).resolve()
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source path not found: {source_path}")
        
        # Generar ID único basado en la ruta y timestamp
        timestamp = int(datetime.now().timestamp())
        ws_id = hashlib.md5(f"{source_path}:{timestamp}".encode()).hexdigest()[:8]
        
        ws_path = self.base_dir / ws_id
        ws_path.mkdir(exist_ok=True)
        
        print(f"📁 Copying {source_path} to {ws_path}...")
        
        try:
            # Copiar contenido (excluir .git y otros)
            def ignore_patterns(path, names):
                ignored = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'venv'}
                return [n for n in names if n in ignored]
            
            shutil.copytree(source_path, ws_path, dirs_exist_ok=True, 
                          ignore=ignore_patterns)
            
            workspace = Workspace(
                id=ws_id,
                path=ws_path,
                source_url=None,
                metadata={
                    'source_path': str(source_path),
                    'copy_success': True
                }
            )
            
            self.workspaces[ws_id] = workspace
            self._cleanup_old_workspaces()
            self._save_workspaces()
            
            return workspace
            
        except Exception as e:
            # Limpiar en caso de error
            if ws_path.exists():
                shutil.rmtree(ws_path, ignore_errors=True)
            raise RuntimeError(f"Copy failed: {e}")
    
    def create_empty(self, prefix: str = "empty") -> Workspace:
        """
        Crear workspace vacío
        
        Args:
            prefix: Prefijo para el ID
            
        Returns:
            Workspace vacío
        """
        timestamp = int(datetime.now().timestamp())
        ws_id = f"{prefix}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:6]}"
        
        ws_path = self.base_dir / ws_id
        ws_path.mkdir(exist_ok=True)
        
        workspace = Workspace(
            id=ws_id,
            path=ws_path,
            metadata={'type': 'empty', 'created_for': prefix}
        )
        
        self.workspaces[ws_id] = workspace
        self._cleanup_old_workspaces()
        self._save_workspaces()
        
        return workspace
    
    def get_workspace(self, ws_id: str) -> Optional[Workspace]:
        """Obtener workspace por ID"""
        workspace = self.workspaces.get(ws_id)
        
        if workspace and workspace.path.exists():
            workspace.last_used = datetime.now()
            self._save_workspaces()
            return workspace
        
        return None
    
    def delete_workspace(self, ws_id: str, force: bool = False) -> bool:
        """
        Eliminar workspace
        
        Args:
            ws_id: ID del workspace
            force: Forzar eliminación incluso si hay errores
            
        Returns:
            True si se eliminó correctamente
        """
        if ws_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[ws_id]
        
        try:
            if workspace.path.exists():
                shutil.rmtree(workspace.path, ignore_errors=force)
            
            del self.workspaces[ws_id]
            self._save_workspaces()
            
            return True
            
        except Exception as e:
            if not force:
                raise RuntimeError(f"Failed to delete workspace: {e}")
            return False
    
    def cleanup_all(self):
        """Eliminar todos los workspaces"""
        for ws_id in list(self.workspaces.keys()):
            self.delete_workspace(ws_id, force=True)
    
    def _cleanup_old_workspaces(self):
        """Eliminar workspaces antiguos si excedemos el límite"""
        if len(self.workspaces) <= self.max_workspaces:
            return
        
        # Ordenar por last_used (más antiguos primero)
        sorted_workspaces = sorted(
            self.workspaces.items(),
            key=lambda x: x[1].last_used
        )
        
        # Eliminar los más antiguos hasta estar bajo el límite
        to_delete = len(self.workspaces) - self.max_workspaces
        for i in range(to_delete):
            ws_id, _ = sorted_workspaces[i]
            self.delete_workspace(ws_id, force=True)
    
    def execute_in_workspace(self, ws_id: str, command: List[str], 
                           timeout: int = 30) -> Dict[str, Any]:
        """
        Ejecutar comando en un workspace
        
        Args:
            ws_id: ID del workspace
            command: Comando a ejecutar (lista de strings)
            timeout: Timeout en segundos
            
        Returns:
            Diccionario con resultados de la ejecución
        """
        workspace = self.get_workspace(ws_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {ws_id}")
        
        print(f"🚀 Executing in workspace {ws_id}: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=str(workspace.path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timed_out': False
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'timed_out': True
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'timed_out': False
            }
    
    def apply_patch(self, ws_id: str, patch_content: str) -> bool:
        """
        Aplicar un parche (diff) al workspace
        
        Args:
            ws_id: ID del workspace
            patch_content: Contenido del parche en formato diff
            
        Returns:
            True si se aplicó correctamente
        """
        workspace = self.get_workspace(ws_id)
        if not workspace:
            return False
        
        # Crear archivo temporal con el parche
        patch_file = workspace.path / "tdh_patch.diff"
        
        try:
            with open(patch_file, 'w') as f:
                f.write(patch_content)
            
            # Aplicar parche
            result = subprocess.run(
                ['patch', '-p1', '-i', str(patch_file)],
                cwd=str(workspace.path),
                capture_output=True,
                text=True
            )
            
            # Limpiar archivo de parche
            patch_file.unlink(missing_ok=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"⚠️  Patch application failed: {e}")
            return False
    
    def list_files(self, ws_id: str, pattern: str = "**/*") -> List[Path]:
        """
        Listar archivos en el workspace
        
        Args:
            ws_id: ID del workspace
            pattern: Patrón glob para filtrar
            
        Returns:
            Lista de rutas a archivos
        """
        workspace = self.get_workspace(ws_id)
        if not workspace:
            return []
        
        files = list(workspace.path.rglob(pattern))
        # Filtrar solo archivos (no directorios)
        return [f for f in files if f.is_file()]
    
    def get_info(self, ws_id: str) -> Dict[str, Any]:
        """Obtener información detallada del workspace"""
        workspace = self.get_workspace(ws_id)
        if not workspace:
            return {}
        
        # Calcular tamaño
        total_size = 0
        file_count = 0
        
        for file_path in workspace.path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            'id': workspace.id,
            'path': str(workspace.path),
            'source_url': workspace.source_url,
            'created_at': workspace.created_at.isoformat(),
            'last_used': workspace.last_used.isoformat(),
            'size_bytes': total_size,
            'file_count': file_count,
            'exists': workspace.path.exists(),
            'metadata': workspace.metadata
        }


# Funciones de utilidad
def create_test_workspace(code_content: str, language: str = "python") -> Workspace:
    """
    Crear workspace de prueba con código específico
    
    Args:
        code_content: Contenido del código
        language: Lenguaje del código (para extensión de archivo)
        
    Returns:
        Workspace creado
    """
    manager = WorkspaceManager()
    workspace = manager.create_empty("test")
    
    # Determinar extensión
    ext_map = {
        'python': '.py',
        'c': '.c',
        'cpp': '.cpp',
        'java': '.java',
        'javascript': '.js',
        'go': '.go',
        'rust': '.rs'
    }
    
    ext = ext_map.get(language, '.txt')
    
    # Crear archivo con el código
    test_file = workspace.path / f"test_code{ext}"
    test_file.write_text(code_content)
    
    return workspace


if __name__ == "__main__":
    # Ejemplo de uso
    print("🧪 Testing Workspace Manager")
    
    manager = WorkspaceManager()
    
    # Crear workspace vacío
    ws = manager.create_empty("demo")
    print(f"Created workspace: {ws.id}")
    print(f"Path: {ws.path}")
    
    # Escribir archivo de prueba
    test_file = ws.path / "hello.py"
    test_file.write_text("print('Hello from TDH Engine!')")
    
    # Ejecutar comando
    result = manager.execute_in_workspace(ws.id, ["python", "hello.py"])
    print(f"Execution result: {result['success']}")
    print(f"Output: {result['stdout']}")
    
    # Obtener info
    info = manager.get_info(ws.id)
    print(f"Workspace info: {json.dumps(info, indent=2, default=str)}")
    
    # Limpiar
    manager.delete_workspace(ws.id)
    print("✅ Test completed")