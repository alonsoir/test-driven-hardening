# src/integration/unified_analyzer.py
"""
Módulo principal de análisis unificado TDH
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class UnifiedAnalyzer:
    """Analizador unificado que combina SAST y AST"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.results = {
            'metadata': {},
            'sast': {},
            'ast': {},
            'combined_issues': []
        }
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Carga configuración desde archivo o usa valores por defecto"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Configuración por defecto
        return {
            'analysis': {
                'sast_enabled': True,
                'ast_enabled': True,
                'min_severity': 'MEDIUM'
            },
            'reporting': {
                'formats': ['json', 'html'],
                'output_dir': 'reports'
            }
        }
    
    def analyze_repository(self, repo_url: str, **kwargs) -> Dict[str, Any]:
        """
        Analiza un repositorio completo
        
        Args:
            repo_url: URL del repositorio o ruta local
            **kwargs: Opciones adicionales
            
        Returns:
            Resultados del análisis
        """
        print(f"🔍 Iniciando análisis unificado para: {repo_url}")
        
        # Preparar metadata
        self.results['metadata'] = {
            'repository': repo_url,
            'analysis_date': datetime.now().isoformat(),
            'tdh_version': '0.2.0'
        }
        
        # Aquí se integraría la lógica de clonación y análisis
        # Por ahora es un esqueleto
        
        return self.results
    
    def combine_results(self, sast_results: Dict, ast_results: Dict) -> Dict[str, Any]:
        """Combina resultados de SAST y AST"""
        
        combined = {
            'metadata': {
                'combined_date': datetime.now().isoformat(),
                'sast_issues': len(sast_results.get('issues', [])),
                'ast_issues': len(ast_results.get('issues', []))
            },
            'sast': sast_results,
            'ast': ast_results,
            'combined_issues': []
        }
        
        # Combinar y clasificar issues
        all_issues = []
        
        # Añadir issues de SAST
        for issue in sast_results.get('issues', []):
            issue['source'] = 'sast'
            all_issues.append(issue)
        
        # Añadir issues de AST
        for issue in ast_results.get('issues', []):
            issue['source'] = 'ast'
            all_issues.append(issue)
        
        # Ordenar por severidad (CRITICAL primero)
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        all_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 99))
        
        combined['combined_issues'] = all_issues
        
        return combined