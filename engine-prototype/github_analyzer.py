#!/usr/bin/env python3
"""
🌐 GITHUB REPOSITORY ANALYZER - VERSIÓN MEJORADA
Analiza repositorios remotos de GitHub usando AST y SAST tools
"""

import os
import sys
import tempfile
import subprocess
import json
import requests
from pathlib import Path
from datetime import datetime
import click
import git
from git import Repo, GitCommandError
import ast as python_ast
import webbrowser  # Nuevo: para abrir en navegador

class GitHubRepositoryAnalyzer:
    """Analizador de repositorios GitHub con AST"""
    
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "tdh_github_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.results = {
            "repository": "",
            "analysis_date": "",
            "languages": [],
            "files_analyzed": 0,
            "vulnerabilities": [],
            "metrics": {}
        }
    
    def clone_repository(self, repo_url, branch=None):
        """Clona un repositorio de GitHub"""
        print(f"📥 Clonando repositorio: {repo_url}")
        
        # Extraer nombre del repo de la URL
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        clone_path = os.path.join(self.cache_dir, repo_name)
        
        # Si ya existe, hacer pull
        if os.path.exists(os.path.join(clone_path, '.git')):
            print(f"📁 Repositorio ya clonado, actualizando...")
            try:
                repo = Repo(clone_path)
                origin = repo.remote('origin')
                origin.pull()
                print("✅ Repositorio actualizado")
            except Exception as e:
                print(f"⚠️  Error actualizando: {e}")
        else:
            # Clonar nuevo
            try:
                # Si se especifica una rama, usarla
                if branch:
                    repo = Repo.clone_from(repo_url, clone_path, branch=branch)
                else:
                    # Si no se especifica, intentar con la rama por defecto
                    # Git automáticamente usará la rama por defecto del repositorio
                    repo = Repo.clone_from(repo_url, clone_path)
                print(f"✅ Repositorio clonado en: {clone_path}")
            except GitCommandError as e:
                print(f"❌ Error clonando: {e}")
                return None
        
        return clone_path
    
    def get_repo_info(self, repo_path):
        """Obtiene información del repositorio"""
        try:
            repo = Repo(repo_path)
            
            # Detectar lenguajes usados
            languages = self.detect_languages(repo_path)
            
            return {
                "name": os.path.basename(repo_path),
                "commit_count": len(list(repo.iter_commits())),
                "branches": [branch.name for branch in repo.branches],
                "active_branch": repo.active_branch.name,
                "languages": languages,
                "last_commit": str(repo.head.commit.committed_datetime),
                "author": str(repo.head.commit.author)
            }
        except Exception as e:
            print(f"⚠️  Error obteniendo info del repo: {e}")
            return {}
    
    def detect_languages(self, repo_path):
        """Detecta lenguajes de programación usados"""
        extensions = {
            '.py': 'Python',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.java': 'Java',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.cs': 'C#',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS'
        }
        
        languages = {}
        for root, dirs, files in os.walk(repo_path):
            # Ignorar directorios comunes
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'vendor']]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    lang = extensions[ext]
                    languages[lang] = languages.get(lang, 0) + 1
        
        # Ordenar por frecuencia
        sorted_langs = dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))
        return sorted_langs
    
    def analyze_python_file(self, filepath):
        """Analiza un archivo Python usando AST"""
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parsear AST
            tree = python_ast.parse(content)
            
            # Analizar imports peligrosos
            for node in python_ast.walk(tree):
                # Detectar imports peligrosos
                if isinstance(node, python_ast.Import):
                    for alias in node.names:
                        if alias.name in ['pickle', 'marshal', 'subprocess', 'os', 'sys']:
                            issues.append({
                                'type': 'CWE-96',
                                'file': filepath,
                                'line': node.lineno if hasattr(node, 'lineno') else 0,
                                'severity': 'MEDIUM',
                                'message': f'Import of potentially dangerous module: {alias.name}',
                                'code': python_ast.unparse(node) if hasattr(python_ast, 'unparse') else str(node)
                            })
                
                # Detectar eval/exec
                if isinstance(node, python_ast.Call):
                    if isinstance(node.func, python_ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile']:
                            issues.append({
                                'type': 'CWE-95',
                                'file': filepath,
                                'line': node.lineno if hasattr(node, 'lineno') else 0,
                                'severity': 'HIGH',
                                'message': f'Use of dangerous function: {node.func.id}',
                                'code': python_ast.unparse(node) if hasattr(python_ast, 'unparse') else str(node)
                            })
                
                # Detectar hardcoded credentials
                if isinstance(node, python_ast.Assign):
                    for target in node.targets:
                        if isinstance(target, python_ast.Name):
                            if target.id.lower() in ['password', 'secret', 'key', 'token', 'credential']:
                                issues.append({
                                    'type': 'CWE-798',
                                    'file': filepath,
                                    'line': node.lineno if hasattr(node, 'lineno') else 0,
                                    'severity': 'HIGH',
                                    'message': f'Potential hardcoded credential: {target.id}',
                                    'code': python_ast.unparse(node) if hasattr(python_ast, 'unparse') else str(node)
                                })
        
        except SyntaxError as e:
            issues.append({
                'type': 'SYNTAX_ERROR',
                'file': filepath,
                'line': e.lineno,
                'severity': 'LOW',
                'message': f'Syntax error: {e.msg}',
                'code': ''
            })
        except Exception as e:
            print(f"⚠️  Error analizando {filepath}: {e}")
        
        return issues
    
    def analyze_cpp_file(self, filepath):
        """Analiza un archivo C/C++ buscando patrones de vulnerabilidad"""
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Patrones comunes de vulnerabilidades en C/C++
            patterns = [
                (r'\bstrcpy\s*\(', 'CWE-120', 'HIGH', 'Use of strcpy() without bounds checking'),
                (r'\bgets\s*\(', 'CWE-120', 'CRITICAL', 'Use of gets() - always vulnerable'),
                (r'\bsprintf\s*\(', 'CWE-120', 'MEDIUM', 'Use of sprintf() without bounds checking'),
                (r'\bstrcat\s*\(', 'CWE-120', 'MEDIUM', 'Use of strcat() without bounds checking'),
                (r'\bsystem\s*\(', 'CWE-78', 'HIGH', 'Use of system() with potential command injection'),
                (r'\bpopen\s*\(', 'CWE-78', 'HIGH', 'Use of popen() with potential command injection'),
                (r'\bfopen\s*\(.*\.\./', 'CWE-22', 'MEDIUM', 'Potential path traversal with ../'),
                (r'\.\./config', 'CWE-22', 'MEDIUM', 'Hardcoded relative path to config'),
                (r'malloc\s*\(.*\)\s*[^;]*(?!free\()', 'CWE-401', 'MEDIUM', 'Potential memory leak'),
                (r'free\s*\([^)]+\)\s*;\s*[^;]*=\s*[^;]+;', 'CWE-416', 'HIGH', 'Potential use after free'),
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, cwe, severity, message in patterns:
                    import re
                    if re.search(pattern, line) and not line.strip().startswith('//'):
                        issues.append({
                            'type': cwe,
                            'file': filepath,
                            'line': i,
                            'severity': severity,
                            'message': message,
                            'code': line.strip()[:100]
                        })
            
            # Buscar buffer allocations sin verificación
            buffer_patterns = [
                r'char\s+\w+\s*\[\s*\d+\s*\]',
                r'malloc\s*\(\s*\d+\s*\)',
                r'new\s+char\s*\[\s*\d+\s*\]'
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern in buffer_patterns:
                    if re.search(pattern, line):
                        # Verificar si hay bounds checking en líneas siguientes
                        bounds_check = False
                        for j in range(i, min(i+5, len(lines))):
                            if any(check in lines[j] for check in ['strncpy', 'snprintf', 'fgets', 'memcpy_s']):
                                bounds_check = True
                                break
                        
                        if not bounds_check and 'strcpy' in line or 'sprintf' in line:
                            issues.append({
                                'type': 'CWE-120',
                                'file': filepath,
                                'line': i,
                                'severity': 'HIGH',
                                'message': 'Buffer allocation without apparent bounds checking',
                                'code': line.strip()[:100]
                            })
        
        except Exception as e:
            print(f"⚠️  Error analizando {filepath}: {e}")
        
        return issues
    
    def analyze_repository(self, repo_path, max_files=1000):
        """Analiza todo el repositorio"""
        print(f"🔍 Analizando repositorio: {repo_path}")
        
        all_issues = []
        file_count = 0
        
        # Analizar por tipo de archivo
        for root, dirs, files in os.walk(repo_path):
            # Ignorar directorios comunes
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'vendor', 'build', 'dist']]
            
            for file in files:
                if file_count >= max_files:
                    print(f"⚠️  Límite de {max_files} archivos alcanzado")
                    break
                
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # Analizar según extensión
                if ext == '.py':
                    issues = self.analyze_python_file(filepath)
                    all_issues.extend(issues)
                    file_count += 1
                elif ext in ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp']:
                    issues = self.analyze_cpp_file(filepath)
                    all_issues.extend(issues)
                    file_count += 1
                elif ext == '.java':
                    # TODO: Analizador Java
                    pass
                elif ext == '.js':
                    # TODO: Analizador JavaScript
                    pass
        
        # Estadísticas
        self.results = {
            "repository": os.path.basename(repo_path),
            "analysis_date": datetime.now().isoformat(),
            "files_analyzed": file_count,
            "vulnerabilities": all_issues,
            "metrics": {
                "total_issues": len(all_issues),
                "by_severity": {
                    "CRITICAL": len([i for i in all_issues if i['severity'] == 'CRITICAL']),
                    "HIGH": len([i for i in all_issues if i['severity'] == 'HIGH']),
                    "MEDIUM": len([i for i in all_issues if i['severity'] == 'MEDIUM']),
                    "LOW": len([i for i in all_issues if i['severity'] == 'LOW'])
                },
                "by_type": {}
            }
        }
        
        # Agrupar por tipo de CWE
        for issue in all_issues:
            cwe = issue['type']
            self.results['metrics']['by_type'][cwe] = self.results['metrics']['by_type'].get(cwe, 0) + 1
        
        return self.results
    
    def generate_report(self, output_format='text'):
        """Genera reporte del análisis"""
        if output_format == 'json':
            return json.dumps(self.results, indent=2)
        
        # Reporte en texto
        report = []
        report.append(f"📊 REPORTE DE ANÁLISIS")
        report.append(f"Repositorio: {self.results['repository']}")
        report.append(f"Fecha: {self.results['analysis_date']}")
        report.append(f"Archivos analizados: {self.results['files_analyzed']}")
        report.append(f"Vulnerabilidades encontradas: {self.results['metrics']['total_issues']}")
        report.append("")
        
        # Distribución por severidad
        report.append("📈 DISTRIBUCIÓN POR SEVERIDAD:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = self.results['metrics']['by_severity'].get(severity, 0)
            if count > 0:
                report.append(f"  {severity}: {count}")
        
        # Distribución por tipo
        report.append("\n🔧 DISTRIBUCIÓN POR TIPO DE CWE:")
        for cwe, count in sorted(self.results['metrics']['by_type'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {cwe}: {count}")
        
        # Top 10 vulnerabilidades
        report.append("\n🚨 TOP 10 VULNERABILIDADES:")
        sorted_issues = sorted(self.results['vulnerabilities'], 
                              key=lambda x: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].index(x['severity']))
        
        for i, issue in enumerate(sorted_issues[:10], 1):
            report.append(f"{i}. [{issue['severity']}] {issue['type']}")
            report.append(f"   Archivo: {issue['file']}")
            report.append(f"   Línea: {issue['line']}")
            report.append(f"   Descripción: {issue['message']}")
            if issue.get('code'):
                report.append(f"   Código: {issue['code'][:80]}...")
            report.append("")
        
        return "\n".join(report)
    
    def analyze_github_url(self, github_url, branch=None, max_files=1000):
        """Analiza un repositorio desde URL de GitHub"""
        print(f"🌐 Analizando repositorio GitHub: {github_url}")
        
        # Asegurar que es URL de GitHub
        if not github_url.startswith(('https://github.com/', 'git@github.com:')):
            if 'github.com' in github_url:
                github_url = f"https://github.com/{github_url.split('github.com/')[-1]}"
            else:
                github_url = f"https://github.com/{github_url}"
        
        # Añadir .git si no está
        if not github_url.endswith('.git'):
            github_url += '.git'
        
        # Clonar repositorio
        repo_path = self.clone_repository(github_url, branch)
        if not repo_path:
            return None
        
        # Obtener información
        repo_info = self.get_repo_info(repo_path)
        print(f"📁 Repositorio: {repo_info.get('name', 'N/A')}")
        print(f"📊 Lenguajes: {', '.join(repo_info.get('languages', {}).keys())}")
        
        # Analizar
        results = self.analyze_repository(repo_path, max_files)
        
        # Añadir info del repo
        results['repo_info'] = repo_info
        
        return results

@click.group()
def cli():
    """GitHub Repository Analyzer - AST-based vulnerability detection"""
    pass

@cli.command()
@click.argument('github_url')
@click.option('--branch', default=None, help='Branch to analyze (default: repository default branch)')
@click.option('--max-files', default=1000, help='Maximum files to analyze')
@click.option('--output', type=click.Choice(['text', 'json', 'html', 'both']), default='text', 
              help='Output format: text, json, html, or both (json+html)')
@click.option('--open-browser', is_flag=True, help='Open HTML report in browser automatically')
@click.option('--save-dir', default='.', help='Directory to save reports (default: current)')
def analyze(github_url, branch, max_files, output, open_browser, save_dir):
    """Analyze a GitHub repository for vulnerabilities"""
    
    analyzer = GitHubRepositoryAnalyzer()
    results = analyzer.analyze_github_url(github_url, branch, max_files)
    
    if not results:
        click.echo("❌ Error analizando el repositorio")
        return
    
    # Crear directorio para guardar reportes si no existe
    os.makedirs(save_dir, exist_ok=True)
    
    # Generar timestamp y nombres base
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_name = results['repository'].replace('/', '_')
    base_filename = f"tdh_report_{repo_name}_{timestamp}"
    
    # Manejar diferentes formatos de salida
    if output in ['text', 'both']:
        # Mostrar reporte en texto
        report_text = analyzer.generate_report('text')
        click.echo(report_text)
    
    if output in ['json', 'both']:
        # Guardar JSON
        json_filename = os.path.join(save_dir, f"{base_filename}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        click.echo(f"📄 Reporte JSON guardado en: {json_filename}")
    
    if output in ['html', 'both']:
        # Generar y guardar HTML
        html_report = generate_html_report(results)
        html_filename = os.path.join(save_dir, f"{base_filename}.html")
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        click.echo(f"🌐 Reporte HTML guardado en: {html_filename}")
        
        # Abrir en navegador si se solicita
        if open_browser:
            try:
                webbrowser.open(f'file://{os.path.abspath(html_filename)}')
                click.echo(f"🔗 Abriendo reporte en navegador...")
            except Exception as e:
                click.echo(f"⚠️  No se pudo abrir el navegador: {e}")
                click.echo(f"💡 Abre manualmente: {html_filename}")
        else:
            # Preguntar si quiere abrir
            if click.confirm('¿Abrir el reporte HTML en el navegador?'):
                try:
                    webbrowser.open(f'file://{os.path.abspath(html_filename)}')
                except Exception as e:
                    click.echo(f"⚠️  No se pudo abrir el navegador: {e}")

@cli.command()
@click.argument('github_url')
def info(github_url):
    """Get information about a GitHub repository"""
    
    analyzer = GitHubRepositoryAnalyzer()
    
    # Asegurar URL
    if not github_url.startswith(('https://github.com/', 'git@github.com:')):
        if 'github.com' in github_url:
            github_url = f"https://github.com/{github_url.split('github.com/')[-1]}"
        else:
            github_url = f"https://github.com/{github_url}"
    
    if not github_url.endswith('.git'):
        github_url += '.git'
    
    repo_path = analyzer.clone_repository(github_url)
    if not repo_path:
        return
    
    repo_info = analyzer.get_repo_info(repo_path)
    
    click.echo("📊 INFORMACIÓN DEL REPOSITORIO")
    click.echo("=" * 50)
    click.echo(f"Nombre: {repo_info.get('name', 'N/A')}")
    click.echo(f"Rama activa: {repo_info.get('active_branch', 'N/A')}")
    click.echo(f"Commits totales: {repo_info.get('commit_count', 0)}")
    click.echo(f"Últltimo commit: {repo_info.get('last_commit', 'N/A')}")
    click.echo(f"Autor: {repo_info.get('author', 'N/A')}")
    click.echo(f"Ramas: {', '.join(repo_info.get('branches', []))}")
    
    click.echo("\n📈 LENGUAJES DETECTADOS:")
    languages = repo_info.get('languages', {})
    for lang, count in languages.items():
        click.echo(f"  {lang}: {count} archivos")

@cli.command()
def trending():
    """Show trending security-related repositories"""
    
    click.echo("🔥 REPOSITORIOS DE SEGURIDAD POPULARES EN GITHUB")
    click.echo("=" * 60)
    
    repos = [
        ("OWASP/CheatSheetSeries", "OWASP Cheat Sheet Series"),
        ("github/codeql", "GitHub's CodeQL engine for vulnerability detection"),
        ("shiftleftsecurity/sast-scan", "SAST Scan - Open source security tool"),
        ("secure-software-engineering/phasar", "PhASAR - Static Analysis Framework"),
        ("google/sanitizers", "AddressSanitizer, ThreadSanitizer, etc."),
        ("NationalSecurityAgency/ghidra", "Ghidra - NSA reverse engineering tool"),
        ("microsoft/MSRC-Security-Research", "Microsoft Security Research"),
        ("mandiant/commando-vm", "Mandiant Commando VM - security distro"),
        ("upx/upx", "UPX - Ultimate Packer for eXecutables"),
        ("radareorg/radare2", "Radare2 - Reverse engineering framework"),
    ]
    
    for i, (repo, desc) in enumerate(repos, 1):
        click.echo(f"{i}. {repo}")
        click.echo(f"   {desc}")
        click.echo(f"   https://github.com/{repo}")
        click.echo()

def generate_html_report(results):
    """Genera reporte HTML interactivo"""
    
    # Generar HTML para vulnerabilidades
    vulns_html = ""
    for vuln in results['vulnerabilities'][:20]:  # Mostrar solo primeras 20
        severity_class = f"severity-{vuln['severity'].lower()}"
        code_snippet = f'<div class="code-snippet">{vuln.get("code", "")}</div>' if vuln.get('code') else ''
        
        vulns_html += f"""
        <div class="vuln-card {severity_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0;">{vuln['type']}: {vuln['message']}</h3>
                <span class="severity-badge {severity_class}">{vuln['severity']}</span>
            </div>
            <p><strong>Archivo:</strong> {vuln['file']}</p>
            <p><strong>Línea:</strong> {vuln['line']}</p>
            {code_snippet}
        </div>
        """
    
    # Si no hay vulnerabilidades
    if not vulns_html:
        vulns_html = '<div class="vuln-card"><p>✅ No se encontraron vulnerabilidades</p></div>'
    
    # Template HTML completo
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TDH Security Report - {results['repository']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        h1 {{ margin: 0; font-size: 2.5em; }}
        .subtitle {{ opacity: 0.9; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #667eea; }}
        .stat-card.critical {{ border-left-color: #dc3545; }}
        .stat-card.high {{ border-left-color: #fd7e14; }}
        .stat-card.medium {{ border-left-color: #ffc107; }}
        .stat-card.low {{ border-left-color: #28a745; }}
        .stat-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .vulnerabilities {{ margin-top: 30px; }}
        .vuln-card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 15px; }}
        .vuln-card.critical {{ border-left: 5px solid #dc3545; }}
        .vuln-card.high {{ border-left: 5px solid #fd7e14; }}
        .vuln-card.medium {{ border-left: 5px solid #ffc107; }}
        .vuln-card.low {{ border-left: 5px solid #28a745; }}
        .severity-badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; color: white; }}
        .severity-critical {{ background: #dc3545; }}
        .severity-high {{ background: #fd7e14; }}
        .severity-medium {{ background: #ffc107; }}
        .severity-low {{ background: #28a745; }}
        .code-snippet {{ background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: 'Courier New', monospace; margin: 10px 0; font-size: 0.9em; }}
        .chart-container {{ height: 300px; margin: 30px 0; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 TDH Security Report</h1>
            <div class="subtitle">
                <h2>{results['repository']}</h2>
                <p>Análisis completado: {results['analysis_date']}</p>
                <p>Archivos analizados: {results['files_analyzed']}</p>
            </div>
        </div>
        
        <div class="summary">
            <h3>📈 Resumen Ejecutivo</h3>
            <p>Total de vulnerabilidades encontradas: <strong>{results['metrics']['total_issues']}</strong></p>
            <p>Análisis realizado con GitHub Repository Analyzer v1.0</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>📁 Archivos analizados</h3>
                <div class="stat-value">{results['files_analyzed']}</div>
            </div>
            <div class="stat-card critical">
                <h3>🚨 CRÍTICAS</h3>
                <div class="stat-value">{results['metrics']['by_severity'].get('CRITICAL', 0)}</div>
            </div>
            <div class="stat-card high">
                <h3>⚠️ ALTAS</h3>
                <div class="stat-value">{results['metrics']['by_severity'].get('HIGH', 0)}</div>
            </div>
            <div class="stat-card medium">
                <h3>🔧 MEDIAS</h3>
                <div class="stat-value">{results['metrics']['by_severity'].get('MEDIUM', 0)}</div>
            </div>
            <div class="stat-card low">
                <h3>📝 BAJAS</h3>
                <div class="stat-value">{results['metrics']['by_severity'].get('LOW', 0)}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="severityChart"></canvas>
        </div>
        
        <div class="vulnerabilities">
            <h2>🔍 Vulnerabilidades Detectadas ({len(results['vulnerabilities'])} total)</h2>
            {vulns_html}
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center;">
            <p>Reporte generado por <strong>GitHub Repository Analyzer</strong></p>
            <p>Test Driven Hardening Engine - University of Extremadura Alumni Research Project</p>
            <p style="font-size: 0.9em; color: #666;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <script>
        // Gráfico de distribución de severidad
        const ctx = document.getElementById('severityChart').getContext('2d');
        const severityChart = new Chart(ctx, {{
            type: 'pie',
            data: {{
                labels: ['CRÍTICAS', 'ALTAS', 'MEDIAS', 'BAJAS'],
                datasets: [{{
                    data: [
                        {results['metrics']['by_severity'].get('CRITICAL', 0)},
                        {results['metrics']['by_severity'].get('HIGH', 0)},
                        {results['metrics']['by_severity'].get('MEDIUM', 0)},
                        {results['metrics']['by_severity'].get('LOW', 0)}
                    ],
                    backgroundColor: [
                        '#dc3545',
                        '#fd7e14',
                        '#ffc107',
                        '#28a745'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Distribución de Vulnerabilidades por Severidad'
                    }},
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    return html

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--output', default='text')
@click.option('--open-browser', is_flag=True)
def local(repo_path, output, open_browser):
    """Analyze a local repository"""
    
    analyzer = GitHubRepositoryAnalyzer()
    results = analyzer.analyze_repository(repo_path)
    
    if output == 'json':
        click.echo(json.dumps(results, indent=2))
    elif output == 'html':
        html_report = generate_html_report(results)
        html_filename = f"tdh_report_{os.path.basename(repo_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        click.echo(f"🌐 Reporte HTML guardado en: {html_filename}")
        
        if open_browser:
            webbrowser.open(f'file://{os.path.abspath(html_filename)}')
    else:
        report = analyzer.generate_report('text')
        click.echo(report)

if __name__ == '__main__':
    cli()