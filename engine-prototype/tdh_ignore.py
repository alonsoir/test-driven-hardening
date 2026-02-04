# tdh_ignore.py
import fnmatch
from pathlib import Path

class TDHIgnore:
    """Manejador de exclusiones tipo .gitignore para TDH"""
    
    DEFAULT_PATTERNS = [
        # Entornos virtuales Python
        'venv/',
        '.venv/',
        'env/',
        '.env/',
        '*/__pycache__/*',
        
        # Node.js
        'node_modules/',
        
        # Build artifacts
        'dist/',
        'build/',
        'target/',
        
        # Version control
        '.git/',
        '.svn/',
        
        # IDEs
        '.idea/',
        '.vscode/',
        
        # Archivos generados
        '*.min.js',
        '*.min.css',
        '*.bundle.js',
        '*.log',
    ]
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.patterns = self._load_patterns()
    
    def _load_patterns(self):
        """Carga patrones de .tdhignore o usa los por defecto"""
        patterns = list(self.DEFAULT_PATTERNS)
        
        # Intentar cargar .tdhignore
        tdhignore_file = self.base_dir / '.tdhignore'
        if tdhignore_file.exists():
            with open(tdhignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        
        # Cargar también de configuración
        try:
            import yaml
            config_file = self.base_dir / 'config' / 'sast_tools.yaml'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    exclusions = config.get('exclusions', {}).get('global', {})
                    patterns.extend(exclusions.get('directories', []))
                    patterns.extend(exclusions.get('files', []))
        except:
            pass
        
        return patterns
    
    def should_ignore(self, path: Path) -> bool:
        """Determina si un path debe ser ignorado"""
        try:
            rel_path = path.relative_to(self.base_dir)
        except ValueError:
            # Si no es relativo, usar absoluto
            rel_path = path
        
        rel_str = str(rel_path).replace('\\', '/')
        
        for pattern in self.patterns:
            pattern = pattern.rstrip('/')
            if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(str(path), pattern):
                return True
            # Para directorios: si el patrón termina con /, también ignorar contenido
            if pattern.endswith('/') and rel_str.startswith(pattern):
                return True
        
        return False