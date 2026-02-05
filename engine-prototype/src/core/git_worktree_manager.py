# src/core/git_worktree_manager.py (versión completa)
import os
import tempfile
import shutil
import json
from pathlib import Path
import subprocess
from typing import Dict, Optional, Tuple, List, Any
import requests
from datetime import datetime


class GitWorktreeManager:
    """
    Gestor completo de worktrees para múltiples LLMs.
    Responsabilidades:
    - Autenticación GitHub (token)
    - Clone único + worktrees aislados
    - Creación de branches y PRs
    - Limpieza automática
    """
    
    def __init__(self, repo_url: str, github_token: Optional[str] = None, 
             base_dir: Optional[str] = None):
        """
        Args:
            repo_url: URL completa del repo (https://github.com/owner/repo.git)
            github_token: Token de GitHub con permisos repo
            base_dir: Directorio para clone principal (None = temporal)
        """
        self.repo_url = repo_url
        self.github_token = github_token
        
        # Manejar directorio base
        if base_dir is None:
            self.base_dir = tempfile.mkdtemp(prefix="tdh_main_repo_")
            print(f"📁 Directorio temporal creado: {self.base_dir}")
        else:
            self.base_dir = os.path.abspath(base_dir)
            # Crear directorios si no existen
            os.makedirs(self.base_dir, exist_ok=True)
            print(f"📁 Usando directorio: {self.base_dir}")
        
        # Extraer owner y repo del URL
        parts = repo_url.rstrip('/').split('/')
        self.repo_name = parts[-1].replace('.git', '')
        self.repo_owner = parts[-2]
        
        self.worktrees: Dict[str, Dict] = {}
        self._authenticated_repo_url = self._add_auth_to_url()

    def _is_valid_git_repo(self, path: str) -> bool:
        """Verifica si un directorio es un repositorio git válido."""
        git_dir = os.path.join(path, ".git")
        if not os.path.exists(git_dir):
            return False
        
        # Verificar configuraciones básicas
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and "true" in result.stdout.strip().lower()
        except:
            return False

        
    def _add_auth_to_url(self) -> str:
        """Añade autenticación al URL del repo si hay token."""
        if not self.github_token:
            return self.repo_url
        
        # Los PATs de GitHub vienen como "github_pat_XXXXXXXX..."
        # Para URLs HTTPS, necesitamos extraer solo el token
        token = self.github_token
        
        # Si el token comienza con "github_pat_", lo mantenemos tal cual
        # GitHub acepta ambos formatos en URLs HTTPS
        
        if self.repo_url.startswith('https://'):
            # Formato: https://TOKEN@github.com/owner/repo.git
            # Reemplazar el inicio de la URL
            if '@github.com' not in self.repo_url:
                # Si no hay credenciales en la URL, añadirlas
                return self.repo_url.replace(
                    'https://', 
                    f'https://{token}@'
                )
        
        return self.repo_url
    
    def setup_main_repo(self) -> str:
        """Clona el repositorio principal con autenticación."""
        # Verificar si ya es un repo git válido
        if self._is_valid_git_repo(self.base_dir):
            print(f"📁 Repositorio git válido ya existe: {self.base_dir}")
            # Verificar si es el repo correcto
            try:
                current_remote = self._run_git(["config", "--get", "remote.origin.url"], 
                                             cwd=self.base_dir, timeout=10)
                print(f"   Remote actual: {current_remote}")
                
                # Solo hacer fetch si el remote es correcto
                if self.repo_url in current_remote or current_remote in self.repo_url:
                    print("   🔄 Actualizando repositorio...")
                    self._run_git(["fetch", "origin"], cwd=self.base_dir, timeout=60)
                else:
                    print(f"   ⚠️  Remote diferente, recreando repo...")
                    shutil.rmtree(self.base_dir)
                    os.makedirs(self.base_dir, exist_ok=True)
                    self._clone_repo()
            except:
                # Si hay error, recrear
                print("   ⚠️  Error verificando repo, recreando...")
                shutil.rmtree(self.base_dir, ignore_errors=True)
                os.makedirs(self.base_dir, exist_ok=True)
                self._clone_repo()
        else:
            # No es un repo válido, crear nuevo
            print(f"🔧 Creando nuevo repositorio en: {self.base_dir}")
            if os.path.exists(self.base_dir):
                # Limpiar directorio si existe pero no es repo git
                print(f"   🧹 Limpiando directorio existente...")
                shutil.rmtree(self.base_dir, ignore_errors=True)
            
            os.makedirs(self.base_dir, exist_ok=True)
            self._clone_repo()
        
        return self.base_dir
    
    def _clone_repo(self):
        """Clona el repositorio con manejo de errores mejorado."""
        print(f"   📥 Clonando: {self.repo_name}")
        
        # Usar URL con autenticación si hay token
        clone_url = self._authenticated_repo_url
        
        # DEBUG: Mostrar URL segura
        safe_url = clone_url
        if '@' in safe_url:
            parts = safe_url.split('@')
            token_part = parts[0]
            if len(token_part) > 20:
                safe_url = f"{token_part[:15]}...@{parts[1]}"
        
        print(f"   📍 URL: {safe_url}")
        
        try:
            # Clonar con timeout extendido (3 minutos)
            self._run_git_with_timeout(
                ["clone", "--no-checkout", clone_url, self.base_dir],
                timeout=180
            )
        except Exception as e:
            print(f"   ❌ Error con autenticación: {e}")
            
            # Intentar sin autenticación
            print(f"   🔄 Intentando sin autenticación...")
            clean_url = self.repo_url
            
            # Remover cualquier token de la URL
            if '@' in clean_url:
                clean_url = "https://" + clean_url.split('@')[1]
            
            self._run_git_with_timeout(
                ["clone", "--no-checkout", clean_url, self.base_dir],
                timeout=180
            )
        
        # Configurar usuario para commits
        self._run_git(["config", "user.email", "engine@tdh.ai"], cwd=self.base_dir)
        self._run_git(["config", "user.name", "TDH Engine"], cwd=self.base_dir)
    
    def _run_git_with_timeout(self, args: List[str], cwd: Optional[str] = None, 
                         timeout: int = 60) -> str:
        """Versión de _run_git con timeout personalizado."""
        cmd = ["git"] + args
        
        try:
            print(f"   ⚙️  Ejecutando: git {args[0]}...")
            result = subprocess.run(
                cmd,
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )
            
            # Log exitoso
            if result.stdout:
                print(f"   ✅ Completado")
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout después de {timeout} segundos")
            raise Exception(f"Git command timeout: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            print(f"   ❌ Error: {error_msg[:200]}")
            raise

    def create_worktree_for_llm(
        self,
        llm_name: str,
        issue_id: str,
        base_branch: str = "main"
    ) -> Tuple[str, str]:
        """
        Crea un worktree aislado para un LLM específico.
        
        Returns:
            Tuple (worktree_dir, branch_name)
        """
        # Nombre de rama único y limpio
        safe_issue_id = "".join(c for c in issue_id if c.isalnum() or c in '-_')
        branch_name = f"tdh-fix/{safe_issue_id}-by-{llm_name}"
        
        # Directorio para el worktree
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        worktree_dir = tempfile.mkdtemp(prefix=f"tdh_{llm_name}_{timestamp}_")
        
        print(f"\n🌿 Creando worktree para LLM: {llm_name}")
        print(f"   Issue: {issue_id}")
        print(f"   Rama: {branch_name}")
        print(f"   Directorio: {worktree_dir}")
        
        try:
            os.chdir(self.base_dir)
            
            # Asegurar que tenemos la última versión de la rama base
            self._run_git(["fetch", "origin", base_branch], cwd=self.base_dir)
            
            # Crear la rama (si no existe)
            branches = self._run_git(["branch", "-a"], cwd=self.base_dir)
            if branch_name not in branches:
                self._run_git(["branch", branch_name, f"origin/{base_branch}"], cwd=self.base_dir)
            
            # Crear worktree
            self._run_git(["worktree", "add", worktree_dir, branch_name], cwd=self.base_dir)
            
            # Configurar el worktree para push
            self._run_git(["remote", "set-url", "origin", self._authenticated_repo_url], cwd=worktree_dir)
            
            # Guardar metadata
            self.worktrees[branch_name] = {
                "dir": worktree_dir,
                "llm_name": llm_name,
                "issue_id": issue_id,
                "base_branch": base_branch,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            print(f"✅ Worktree creado exitosamente")
            return worktree_dir, branch_name
            
        except Exception as e:
            print(f"❌ Error creando worktree: {e}")
            if os.path.exists(worktree_dir):
                shutil.rmtree(worktree_dir, ignore_errors=True)
            raise
    
    def prepare_llm_context(
        self,
        branch_name: str,
        sast_issue: Dict[str, Any],
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Prepara contexto enriquecido para el LLM basado en el issue SAST.
        
        Incluye:
        - Código vulnerable y contexto circundante
        - Metadatos de la vulnerabilidad
        - Archivos relacionados
        - Sugerencias de remediación
        """
        if branch_name not in self.worktrees:
            raise ValueError(f"Worktree no encontrado: {branch_name}")
        
        worktree_dir = self.worktrees[branch_name]["dir"]
        file_path = sast_issue.get("file", "")
        
        # Leer archivo vulnerable
        full_path = Path(worktree_dir) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado en worktree: {file_path}")
        
        with open(full_path, 'r') as f:
            file_content = f.read()
        
        # Extraer contexto alrededor de la línea problemática
        line_num = sast_issue.get("line", 0)
        lines = file_content.split('\n')
        
        # Contexto: 5 líneas antes y después
        start_line = max(0, line_num - 6)  # -6 porque es 1-indexed
        end_line = min(len(lines), line_num + 4)  # +4 para incluir 5 líneas después
        
        context_lines = lines[start_line:end_line] if lines else []
        
        # Marcar línea problemática
        if 0 <= line_num - 1 < len(lines):
            context_lines_with_marker = []
            for i, line in enumerate(context_lines, start=start_line + 1):
                if i == line_num:
                    context_lines_with_marker.append(f"👉 {line}  <-- VULNERABLE")
                else:
                    context_lines_with_marker.append(f"   {line}")
            context = '\n'.join(context_lines_with_marker)
        else:
            context = '\n'.join(context_lines)
        
        # Buscar archivos relacionados (mismo directorio, includes, etc.)
        related_files = []
        if include_related:
            file_dir = Path(file_path).parent
            for f in (Path(worktree_dir) / file_dir).glob("*"):
                if f.is_file() and f.suffix in ['.c', '.cpp', '.h', '.hpp', '.py', '.js']:
                    rel_path = str(f.relative_to(worktree_dir))
                    related_files.append(rel_path)
        
        # Construir contexto para LLM
        llm_context = {
            "vulnerability": {
                "id": sast_issue.get("rule_id", ""),
                "severity": sast_issue.get("severity", ""),
                "description": sast_issue.get("message", ""),
                "file": file_path,
                "line": line_num,
                "tool": sast_issue.get("tool", "")
            },
            "code": {
                "full_file": file_content,
                "vulnerable_section": context,
                "line_numbers": f"{start_line + 1}-{end_line}",
                "language": self._detect_language(file_path)
            },
            "repository": {
                "url": self.repo_url,
                "branch": branch_name,
                "worktree": worktree_dir
            },
            "related_files": related_files[:10],  # Limitar a 10
            "instructions": {
                "task": "Fix the security vulnerability while maintaining functionality.",
                "requirements": [
                    "Fix ONLY the security issue",
                    "Don't break existing functionality",
                    "Add comments explaining the security fix",
                    "Follow the existing code style"
                ]
            }
        }
        
        return llm_context
    
    def apply_llm_fix(
        self,
        branch_name: str,
        fixed_files: Dict[str, str],  # {ruta_relativa: contenido_fixed}
        llm_name: str
    ) -> str:
        """
        Aplica los fixes del LLM al worktree y hace commit.
        
        Args:
            fixed_files: Diccionario con archivos modificados
            llm_name: Nombre del LLM (para metadata de commit)
            
        Returns:
            Hash del commit
        """
        if branch_name not in self.worktrees:
            raise ValueError(f"Worktree no encontrado: {branch_name}")
        
        worktree_info = self.worktrees[branch_name]
        worktree_dir = worktree_info["dir"]
        
        print(f"\n💾 Aplicando fix de {llm_name} en {branch_name}")
        
        # Aplicar cambios a cada archivo
        for file_path, new_content in fixed_files.items():
            full_path = Path(worktree_dir) / file_path
            
            # Crear directorios si no existen
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir nuevo contenido
            with open(full_path, 'w') as f:
                f.write(new_content)
            
            print(f"   📝 Modificado: {file_path}")
        
        # Hacer commit
        os.chdir(worktree_dir)
        
        # Add todos los cambios
        self._run_git(["add", "."], cwd=worktree_dir)
        
        # Verificar si hay cambios
        status = self._run_git(["status", "--porcelain"], cwd=worktree_dir).strip()
        if not status:
            print("   ⚠️  No hay cambios para commit")
            return ""
        
        # Commit con autor específico
        commit_message = f"Fix {worktree_info['issue_id']} by {llm_name}\n\n"
        commit_message += f"Security fix generated by {llm_name} via TDH Engine\n"
        commit_message += f"Issue: {worktree_info['issue_id']}\n"
        commit_message += f"LLM: {llm_name}\n"
        commit_message += f"Timestamp: {datetime.now().isoformat()}"
        
        author_email = f"{llm_name.lower().replace(' ', '_')}@tdh.ai"
        author_name = f"TDH {llm_name}"
        
        self._run_git([
            "commit", 
            "-m", commit_message,
            "--author", f"{author_name} <{author_email}>"
        ], cwd=worktree_dir)
        
        # Obtener hash del commit
        commit_hash = self._run_git(["rev-parse", "HEAD"], cwd=worktree_dir).strip()
        
        print(f"✅ Commit realizado: {commit_hash[:8]}")
        worktree_info["status"] = "committed"
        worktree_info["commit_hash"] = commit_hash
        
        return commit_hash
    
    def push_to_github(self, branch_name: str) -> Tuple[bool, str]:
        """
        Hace push de la rama al repositorio remoto.
        
        Returns:
            (success, url_or_error_message)
        """
        if branch_name not in self.worktrees:
            return False, f"Worktree no encontrado: {branch_name}"
        
        worktree_dir = self.worktrees[branch_name]["dir"]
        
        print(f"\n🚀 Haciendo push de {branch_name}...")
        
        try:
            # Force push para sobrescribir si existe (en desarrollo)
            self._run_git(["push", "-f", "origin", branch_name], cwd=worktree_dir)
            
            url = f"https://github.com/{self.repo_owner}/{self.repo_name}/tree/{branch_name}"
            
            print(f"✅ Push exitoso: {url}")
            self.worktrees[branch_name]["status"] = "pushed"
            self.worktrees[branch_name]["remote_url"] = url
            
            return True, url
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error en push: {e.stderr if hasattr(e, 'stderr') else str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def create_pull_request(
        self,
        branch_name: str,
        title: Optional[str] = None,
        body: Optional[str] = None
    ) -> Optional[str]:
        """
        Crea un Pull Request via GitHub API.
        
        Requires: GITHUB_TOKEN con permisos repo
        """
        if not self.github_token:
            print("⚠️  No hay token de GitHub, no se puede crear PR")
            return None
        
        if branch_name not in self.worktrees:
            print(f"⚠️  Worktree no encontrado: {branch_name}")
            return None
        
        worktree_info = self.worktrees[branch_name]
        
        # Configurar título y cuerpo por defecto
        if not title:
            title = f"Security fix: {worktree_info['issue_id']} by {worktree_info['llm_name']}"
        
        if not body:
            body = f"""## Security Fix Generated by TDH Engine

**Vulnerability**: {worktree_info['issue_id']}
**Fixed by**: {worktree_info['llm_name']}
**Branch**: {branch_name}
**Status**: Automated security fix

### Changes:
- Security vulnerability fix
- Generated by TDH Engine LLM Council
- Code reviewed by {worktree_info['llm_name']}

### Notes:
This is an automated security fix. Please review carefully.
"""
        
        # Crear PR via GitHub API
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls"
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body,
            "head": branch_name,
            "base": worktree_info["base_branch"],
            "maintainer_can_modify": True
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            pr_data = response.json()
            pr_url = pr_data.get("html_url")
            
            print(f"✅ Pull Request creado: {pr_url}")
            self.worktrees[branch_name]["pr_url"] = pr_url
            self.worktrees[branch_name]["status"] = "pr_created"
            
            return pr_url
            
        except requests.RequestException as e:
            print(f"❌ Error creando PR: {e}")
            return None
    
    def cleanup_worktree(self, branch_name: str, keep_remote: bool = False):
        """
        Elimina worktree local y rama.
        
        Args:
            keep_remote: Si True, no elimina la rama remota
        """
        if branch_name not in self.worktrees:
            return
        
        worktree_info = self.worktrees[branch_name]
        
        print(f"\n🧹 Limpiando worktree de {worktree_info['llm_name']}")
        
        # 1. Eliminar worktree
        worktree_dir = worktree_info["dir"]
        if os.path.exists(worktree_dir):
            try:
                os.chdir(self.base_dir)
                self._run_git(["worktree", "remove", "-f", worktree_dir], cwd=self.base_dir)
                print(f"   ✅ Worktree eliminado: {worktree_dir}")
            except:
                # Fallback: eliminar manualmente
                shutil.rmtree(worktree_dir, ignore_errors=True)
                print(f"   ⚠️  Worktree eliminado manualmente")
        
        # 2. Eliminar rama local
        try:
            self._run_git(["branch", "-D", branch_name], cwd=self.base_dir)
            print(f"   ✅ Rama local eliminada: {branch_name}")
        except:
            print(f"   ⚠️  No se pudo eliminar rama local: {branch_name}")
        
        # 3. Eliminar rama remota (opcional)
        if not keep_remote and self.github_token:
            try:
                self._run_git(["push", "origin", "--delete", branch_name], cwd=self.base_dir)
                print(f"   ✅ Rama remota eliminada: {branch_name}")
            except:
                print(f"   ⚠️  No se pudo eliminar rama remota: {branch_name}")
        
        # 4. Eliminar del registro
        del self.worktrees[branch_name]
    
    def cleanup_all(self, keep_remote: bool = True):
        """Limpia todos los worktrees."""
        print(f"\n🧹 Limpiando todos los worktrees (keep_remote={keep_remote})")
        
        for branch_name in list(self.worktrees.keys()):
            self.cleanup_worktree(branch_name, keep_remote=keep_remote)
    
    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> str:
        """Ejecuta comando git de forma segura."""
        cmd = ["git"] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git command failed: {' '.join(cmd)}\nError: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception(f"Git command timeout: {' '.join(cmd)}")
    
    def _detect_language(self, file_path: str) -> str:
        """Detecta lenguaje de programación basado en extensión."""
        ext_map = {
            '.c': 'C', '.h': 'C',
            '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++', '.hpp': 'C++',
            '.py': 'Python',
            '.js': 'JavaScript', '.jsx': 'JavaScript',
            '.ts': 'TypeScript', '.tsx': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, 'Unknown')
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de todos los worktrees."""
        return {
            "repo": self.repo_url,
            "base_dir": self.base_dir,
            "worktrees": self.worktrees,
            "total_worktrees": len(self.worktrees)
        }