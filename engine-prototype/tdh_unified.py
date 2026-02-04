#!/usr/bin/env python3
"""
TDH Unified Analyzer - Punto de entrada unificado para análisis de seguridad
Combina análisis AST (github_analyzer.py) y SAST (SASTOrchestrator)
"""

import os
import sys
import json
import click
import tempfile
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Añadir src al path
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from core.sast_orchestrator import SASTOrchestrator
    # Nota: unified_analyzer.py no existe aún, así que lo comentamos
    # from integration.unified_analyzer import UnifiedAnalyzer
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("🔧 Asegúrate de que la estructura del proyecto es correcta")
    sys.exit(1)

# Serializador JSON personalizado para manejar tipos no estándar
class TDHJSONEncoder(json.JSONEncoder):
    """Encoder personalizado para serializar objetos datetime y otros tipos especiales"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

@click.group()
def cli():
    """TDH Unified Analyzer - Herramienta unificada de análisis de seguridad"""
    pass

@cli.command()
@click.argument('target', required=True)
@click.option('--sast', is_flag=True, help='Ejecutar análisis SAST')
@click.option('--ast', is_flag=True, help='Ejecutar análisis AST (github_analyzer.py)')
@click.option('--all', is_flag=True, help='Ejecutar todos los análisis')
@click.option('--output-dir', default='reports', help='Directorio de salida para reportes')
@click.option('--format', default='json', type=click.Choice(['json', 'html', 'both']), 
              help='Formato del reporte')
@click.option('--severity', default='MEDIUM', 
              type=click.Choice(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']),
              help='Severidad mínima a reportar')
@click.option('--critical-only', is_flag=True, help='Mostrar solo issues CRITICAL')
@click.option('--no-info', is_flag=True, default=True, help='Excluir issues INFO (por defecto: True)')
@click.option('--filter-noise', is_flag=True, default=True, help='Filtrar ruido común (por defecto: True)')
@click.option('--max-issues', default=100, type=int, help='Máximo número de issues a mostrar')
@click.option('--no-cleanup', is_flag=True, help='No eliminar directorios temporales')
@click.option('--exclude-venv', is_flag=True, default=True, help='Excluir entorno virtual del análisis')
def analyze(target, sast, ast, all, output_dir, format, severity, critical_only, 
            no_info, filter_noise, max_issues, no_cleanup, exclude_venv):    
    """
    Analiza un repositorio o directorio local
    
    TARGET puede ser:
      - URL de GitHub: alonsoir/test-zeromq-c-
      - Ruta local: ./mi_proyecto
      - URL completa: https://github.com/alonsoir/test-zeromq-c-
    """
    print("=" * 60)
    print("🔍 TDH Unified Analyzer v0.2.0 - Filtrado Avanzado")
    print("=" * 60)
    
    # Determinar qué análisis ejecutar
    if all:
        sast = True
        ast = True
    
    if not sast and not ast:
        click.echo("⚠️  Debes especificar al menos un tipo de análisis (--sast, --ast, o --all)")
        click.echo("💡 Usa --help para ver todas las opciones")
        return
    
    # Ajustar filtros basados en opciones
    if critical_only:
        severity = 'CRITICAL'
        print("🔴 Modo CRITICAL-ONLY: Solo se mostrarán issues CRITICAL")
    
    if no_info and severity != 'INFO':
        print("📊 Excluyendo issues INFO (--no-info activado)")
    
    if filter_noise:
        print("🧹 Filtrando ruido común (missing includes, checkers report, etc.)")
    
    print(f"📏 Máximo issues a mostrar: {max_issues}")
    
    # Procesar target
    target_type, target_path = _process_target(target, no_cleanup)
    
    if not target_path:
        click.echo(f"❌ No se pudo procesar el target: {target}")
        return
    
    print(f"📦 Target: {target}")
    print(f"📁 Tipo: {target_type}")
    print(f"📍 Ruta: {target_path}")
    print(f"⚙️  Análisis: AST={ast}, SAST={sast}")
    print(f"📊 Severidad mínima: {severity}")
    print(f"📁 Salida: {output_dir}")
    print(f"🚫 Excluir venv: {exclude_venv}")
    
    resultados = {}
    
    # Ejecutar análisis SAST
    if sast:
        print("\n" + "-" * 40)
        print("🔧 EJECUTANDO ANÁLISIS SAST")
        print("-" * 40)
        
        try:
            # Configurar SAST con severidad personalizada
            sast_results = _run_sast_analysis(target_path, severity, exclude_venv, 
                                            no_info, filter_noise, max_issues)
            
            # Serializar resultados SAST para JSON
            sast_results_serializable = _serialize_for_json(sast_results)
            resultados['sast'] = sast_results_serializable
            
            if 'issues' in sast_results:
                print(f"✅ SAST completado: {len(sast_results.get('issues', []))} issues encontrados")
            else:
                print(f"⚠️  SAST completado pero sin resultados de issues")
        except Exception as e:
            print(f"❌ Error en análisis SAST: {e}")
            import traceback
            traceback.print_exc()
            resultados['sast'] = {'error': str(e)}
    
    # Ejecutar análisis AST
    if ast:
        print("\n" + "-" * 40)
        print("🧬 EJECUTANDO ANÁLISIS AST")
        print("-" * 40)
        
        try:
            ast_results = _run_ast_analysis(target_path, output_dir)
            # Serializar resultados AST para JSON
            ast_results_serializable = _serialize_for_json(ast_results)
            resultados['ast'] = ast_results_serializable
            
            if ast_results.get('success'):
                print(f"✅ AST completado: Reporte generado en {ast_results.get('report_path', 'N/A')}")
            else:
                print(f"⚠️  AST falló: {ast_results.get('error', 'Error desconocido')}")
        except Exception as e:
            print(f"❌ Error en análisis AST: {e}")
            import traceback
            traceback.print_exc()
            resultados['ast'] = {'error': str(e)}
    
    # Generar reporte combinado
    print("\n" + "-" * 40)
    print("📊 GENERANDO REPORTES COMBINADOS")
    print("-" * 40)
    
    reportes_generados = _generate_combined_reports(
        resultados, 
        target, 
        output_dir, 
        format
    )
    
    # Mostrar resumen
    _print_summary(resultados, reportes_generados)
    
    # Limpieza (si se solicita)
    if not no_cleanup and target_type == 'github':
        try:
            # Verificar que es un directorio temporal (contiene 'tmp' en la ruta)
            if 'tmp' in target_path or 'temp' in target_path:
                shutil.rmtree(target_path, ignore_errors=True)
                print(f"🧹 Directorio temporal eliminado: {target_path}")
            else:
                print(f"⚠️  No se elimina directorio (no parece temporal): {target_path}")
        except Exception as e:
            print(f"⚠️  No se pudo eliminar directorio: {e}")

def _serialize_for_json(obj):
    """Convierte objetos no serializables (datetime, Path) a strings para JSON"""
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Path):
        return str(obj)
    elif hasattr(obj, '__dict__'):
        # Para objetos con atributos, convertimos a dict
        return _serialize_for_json(obj.__dict__)
    else:
        return obj

def _process_target(target, no_cleanup):
    """
    Procesa el target: determina si es URL de GitHub o ruta local
    Retorna: (tipo, ruta_local)
    """
    # Si ya es una ruta local
    if os.path.exists(target):
        return 'local', os.path.abspath(target)
    
    # Si es una URL de GitHub
    github_url = None
    if target.startswith('https://github.com/') or target.startswith('http://github.com/'):
        github_url = target
        if not github_url.endswith('.git'):
            github_url += '.git'
    elif '/' in target and ' ' not in target and not os.path.exists(target):
        # Formato usuario/repo o usuario/repo-
        if target.endswith('.git'):
            target = target[:-4]
        github_url = f"https://github.com/{target}.git"
    
    if github_url:
        # Clonar el repositorio
        try:
            # Extraer nombre del repo de la URL
            if github_url.endswith('.git'):
                repo_name = github_url.split('/')[-1][:-4]  # Quitar .git
            else:
                repo_name = github_url.split('/')[-1]
            
            if no_cleanup:
                # Usar directorio fijo
                clone_dir = Path.cwd() / 'cloned_repos' / repo_name
                clone_dir.mkdir(parents=True, exist_ok=True)
            else:
                # Usar directorio temporal
                temp_dir = tempfile.mkdtemp(prefix=f"tdh_clone_{repo_name}_")
                clone_dir = Path(temp_dir) / repo_name
            
            print(f"📥 Clonando repositorio: {github_url}")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', github_url, str(clone_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Error clonando repositorio: {result.stderr}")
                print(f"   URL intentada: {github_url}")
                return None, None
            
            print(f"✅ Repositorio clonado exitosamente en: {clone_dir}")
            return 'github', str(clone_dir)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error clonando repositorio: {e}")
            return None, None
        except Exception as e:
            print(f"❌ Error procesando repositorio: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    # Si no es reconocible
    print(f"⚠️  Target no reconocido: {target}")
    print("💡 Formatos soportados:")
    print("   - URL de GitHub: https://github.com/usuario/repo")
    print("   - Formato corto: usuario/repo (ej: alonsoir/test-zeromq-c-)")
    print("   - Ruta local: ./ruta/al/proyecto")
    return None, None

def _run_sast_analysis(target_path, severity, exclude_venv, no_info=True, 
                      filter_noise=True, max_issues=100):
    """Ejecuta análisis SAST en el directorio target"""
    
    try:
        # Configurar entorno para evitar análisis de venv
        if exclude_venv:
            config_path = _create_exclusion_config(target_path, severity)
        
        # Usar SASTOrchestrator
        orchestrator = SASTOrchestrator(target_path)
        
        # Actualizar severidad mínima si es necesario
        if 'global' in orchestrator.sast_config:
            orchestrator.sast_config['global']['min_severity'] = severity
        
        # Ejecutar análisis
        results = orchestrator.analyze_directory(target_path)
        
        # Filtrar resultados según opciones
        if 'issues' in results:
            # Aplicar filtros
            filtered_issues = []
            
            for issue in results['issues']:
                issue_severity = issue.get('severity', 'UNKNOWN')
                
                # 1. Filtrar por severidad mínima
                severity_order = {
                    'CRITICAL': 0,
                    'HIGH': 1,
                    'MEDIUM': 2,
                    'LOW': 3,
                    'INFO': 4,
                    'UNKNOWN': 5
                }
                
                issue_level = severity_order.get(issue_severity, 99)
                min_level = severity_order.get(severity, 99)
                
                if issue_level > min_level:
                    continue
                
                # 2. Excluir INFO si no_info está activado
                if no_info and issue_severity == 'INFO':
                    continue
                
                # 3. Filtrar ruido común
                if filter_noise:
                    tool = issue.get('tool', '')
                    message = issue.get('message', '').lower()
                    rule_id = issue.get('rule_id', '').lower()
                    
                    # Filtros específicos para cppcheck
                    if tool == 'cppcheck':
                        noise_patterns = [
                            'missingincludesystem',
                            'missinginclude',
                            'checkersreport',
                            'unusedfunction',
                            'unreadvariable',
                            'unusedvariable',
                            'variablehidesvariable',
                            'functionstatic',
                            'funcioneshouldbestatic',
                            'stylistic'
                        ]
                        
                        is_noise = any(pattern in rule_id or pattern in message 
                                     for pattern in noise_patterns)
                        if is_noise:
                            continue
                    
                    # Filtros generales
                    general_noise = [
                        'style suggestion',
                        'code style',
                        'whitespace',
                        'indentation',
                        'line too long',
                        'trailing whitespace',
                        'missing docstring'
                    ]
                    
                    if any(noise in message for noise in general_noise):
                        continue
                
                filtered_issues.append(issue)
            
            # 4. Aplicar límite máximo de issues
            if max_issues and len(filtered_issues) > max_issues:
                print(f"📏 Limitando a {max_issues} issues (de {len(filtered_issues)})")
                filtered_issues = filtered_issues[:max_issues]
            
            # Actualizar resultados
            results['issues'] = filtered_issues
            results['stats']['total_issues'] = len(filtered_issues)
            
            # Recalcular estadísticas por severidad
            severity_counts = {}
            for issue in filtered_issues:
                sev = issue.get('severity', 'UNKNOWN')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            results['stats']['issues_by_severity'] = severity_counts
        
        return results
        
    except Exception as e:
        print(f"❌ Error en análisis SAST: {e}")
        import traceback
        traceback.print_exc()
        raise

def _create_exclusion_config(target_path, severity):
    """Crea configuración temporal para excluir venv y directorios no deseados"""
    import yaml
    
    config_dir = Path(target_path) / '.tdh_temp'
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / 'sast_tools_exclude.yaml'
    
    # Configuración con exclusiones
    config = {
        'global': {
            'min_severity': severity,
            'timeout_per_tool': 120
        },
        'exclusions': {
            'global': {
                'directories': [
                    '**/venv/**',
                    '**/.venv/**',
                    '**/env/**',
                    '**/.env/**',
                    '**/__pycache__/**',
                    '**/node_modules/**',
                    '**/.git/**',
                    '**/dist/**',
                    '**/build/**',
                    '**/target/**',
                    '**/.tdh_temp/**'  # Excluir nuestra propia carpeta temporal
                ],
                'files': [
                    '**/*.min.js',
                    '**/*.min.css',
                    '**/*.bundle.js',
                    '**/*.log'
                ]
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    return config_path

def _run_ast_analysis(target_path, output_dir):
    """Ejecuta análisis AST usando github_analyzer.py"""
    
    # Primero verificar si github_analyzer.py existe
    analyzer_path = Path(__file__).parent / 'github_analyzer.py'
    
    if not analyzer_path.exists():
        print("⚠️  github_analyzer.py no encontrado, omitiendo análisis AST")
        return {'warning': 'github_analyzer.py no encontrado', 'success': False}
    
    # Crear directorio para reportes AST
    ast_output_dir = Path(output_dir) / 'ast'
    ast_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Comando para ejecutar github_analyzer.py
    cmd = [
        sys.executable, str(analyzer_path),
        'analyze',
        target_path,
        '--output', 'json',
        '--save-dir', str(ast_output_dir)
    ]
    
    print(f"🔧 Ejecutando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            # Buscar el archivo JSON generado
            json_files = list(ast_output_dir.glob('*.json'))
            if json_files:
                # Ordenar por fecha de modificación (más reciente primero)
                json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                latest_json = json_files[0]
                with open(latest_json, 'r') as f:
                    ast_data = json.load(f)
                
                return {
                    'success': True,
                    'report_path': str(latest_json),
                    'data': ast_data
                }
            else:
                return {
                    'success': False,
                    'error': 'No se generó archivo JSON',
                    'stdout': result.stdout[:500] if result.stdout else '',
                    'stderr': result.stderr[:500] if result.stderr else ''
                }
        else:
            return {
                'success': False,
                'error': f'Exit code {result.returncode}',
                'stderr': result.stderr[:500] if result.stderr else '',
                'stdout': result.stdout[:500] if result.stdout else ''
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Timeout (5 minutos) excedido'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def _generate_combined_reports(resultados, target_name, output_dir, format):
    """Genera reportes combinados en diferentes formatos"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Crear nombre de archivo seguro
    target_slug = "".join(c for c in target_name if c.isalnum() or c in ('-', '_')).rstrip()
    if not target_slug:
        target_slug = "unknown_target"
    
    reportes = []
    
    # 1. Reporte JSON combinado
    if format in ['json', 'both']:
        json_path = output_path / f"tdh_combined_{target_slug}_{timestamp}.json"
        
        combined_data = {
            'metadata': {
                'target': target_name,
                'timestamp': timestamp,
                'analysis_date': datetime.now().isoformat(),
                'tdh_version': '0.2.0',
                'filters_applied': {
                    'min_severity': 'CRITICAL' if 'CRITICAL' in target_name else 'MEDIUM',
                    'max_issues': 100,
                    'filter_noise': True
                }
            },
            'results': resultados
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False, cls=TDHJSONEncoder)
        
        reportes.append(('JSON', str(json_path)))
        print(f"📄 Reporte JSON generado: {json_path}")
    
    # 2. Reporte HTML básico (simplificado)
    if format in ['html', 'both']:
        html_path = output_path / f"tdh_report_{target_slug}_{timestamp}.html"
        
        html_content = _generate_html_report(resultados, target_name, timestamp)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        reportes.append(('HTML', str(html_path)))
        print(f"🌐 Reporte HTML generado: {html_path}")
    
    # 3. Reporte de consola (siempre se genera)
    console_path = output_path / f"tdh_summary_{target_slug}_{timestamp}.txt"
    summary = _generate_text_summary(resultados)
    
    with open(console_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    reportes.append(('TXT', str(console_path)))
    
    return reportes

def _generate_html_report(resultados, target_name, timestamp):
    """Genera un reporte HTML básico"""
    
    # Contar issues por severidad
    sast_issues = resultados.get('sast', {}).get('issues', [])
    ast_data = resultados.get('ast', {})
    ast_issues = ast_data.get('data', {}).get('issues', []) if ast_data.get('success') else []
    
    # Estadísticas simples
    stats = {
        'sast_total': len(sast_issues),
        'ast_total': len(ast_issues),
        'total': len(sast_issues) + len(ast_issues),
        'sast_by_severity': {},
        'tools_used': set()
    }
    
    for issue in sast_issues:
        severity = issue.get('severity', 'UNKNOWN')
        stats['sast_by_severity'][severity] = stats['sast_by_severity'].get(severity, 0) + 1
        stats['tools_used'].add(issue.get('tool', 'unknown'))
    
    # Construir HTML
    html_parts = []
    
    html_parts.append(f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TDH Security Report - {target_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-box {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; flex: 1; min-width: 200px; }}
        .severity-critical {{ color: #dc3545; font-weight: bold; }}
        .severity-high {{ color: #fd7e14; font-weight: bold; }}
        .severity-medium {{ color: #ffc107; font-weight: bold; }}
        .severity-low {{ color: #28a745; font-weight: bold; }}
        .issues-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .issues-table th, .issues-table td {{ border: 1px solid #dee2e6; padding: 10px; text-align: left; }}
        .issues-table th {{ background: #f8f9fa; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; background: #6c757d; color: white; }}
        .badge-sast {{ background: #007bff; }}
        .badge-ast {{ background: #17a2b8; }}
        .filter-info {{ background: #e9ecef; padding: 10px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 TDH Security Analysis Report</h1>
        <p><strong>Target:</strong> {target_name}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Filters:</strong> CRITICAL/HIGH only, noise filtered</p>
    </div>''')
    
    html_parts.append('''    
    <div class="filter-info">
        <p><strong>⚠️ Filtered Analysis:</strong> This report shows only CRITICAL and HIGH severity issues with common noise (missing includes, style suggestions, etc.) filtered out.</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <h3>📊 Resumen</h3>
            <p><strong>Total Issues:</strong> {total}</p>
            <p><strong>SAST Issues:</strong> {sast_total}</p>
            <p><strong>AST Issues:</strong> {ast_total}</p>
        </div>'''.format(**stats))
    
    if stats['sast_by_severity']:
        html_parts.append('''
        <div class="stat-box">
            <h3>⚠️ SAST por Severidad</h3>''')
        
        for severity, count in stats['sast_by_severity'].items():
            html_parts.append(f'            <p><span class="severity-{severity.lower()}">{severity}:</span> {count}</p>')
        
        html_parts.append('''        </div>''')
    
    if stats['tools_used']:
        html_parts.append('''
        <div class="stat-box">
            <h3>🛠️ Herramientas Usadas</h3>''')
        
        for tool in sorted(stats['tools_used']):
            html_parts.append(f'            <p>{tool}</p>')
        
        html_parts.append('''        </div>''')
    
    html_parts.append('''    </div>''')
    
    # Sección SAST
    html_parts.append(f'''    
    <h2>🔧 Issues de SAST ({len(sast_issues)})</h2>''')
    
    if sast_issues:
        html_parts.append('''    <table class="issues-table">
        <thead>
            <tr>
                <th>Tool</th>
                <th>Severity</th>
                <th>File</th>
                <th>Line</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>''')
        
        for issue in sast_issues[:50]:  # Limitar a 50 issues en el HTML
            severity_class = f"severity-{issue.get('severity', '').lower()}"
            filename = issue.get('file', 'N/A')
            if isinstance(filename, str) and '/' in filename:
                filename = filename.split('/')[-1]
            
            html_parts.append(f'''            <tr>
                <td><span class="badge badge-sast">{issue.get('tool', 'N/A')}</span></td>
                <td><span class="{severity_class}">{issue.get('severity', 'N/A')}</span></td>
                <td>{filename}</td>
                <td>{issue.get('line', 'N/A')}</td>
                <td>{str(issue.get('message', 'N/A'))[:100]}...</td>
            </tr>''')
        
        html_parts.append('''        </tbody>
    </table>''')
        
        if len(sast_issues) > 50:
            html_parts.append(f'    <p>... y {len(sast_issues) - 50} issues más (ver reporte JSON completo)</p>')
    else:
        html_parts.append('    <p>✅ No se encontraron issues de SAST críticos/altos (¡Buen trabajo!)</p>')
    
    # Sección AST
    html_parts.append(f'''
    <h2>🧬 Issues de AST ({len(ast_issues)})</h2>''')
    
    if ast_issues:
        html_parts.append('''    <table class="issues-table">
        <thead>
            <tr>
                <th>Type</th>
                <th>File</th>
                <th>Line</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>''')
        
        for issue in ast_issues[:50]:
            filename = issue.get('file', 'N/A')
            if isinstance(filename, str) and '/' in filename:
                filename = filename.split('/')[-1]
            
            html_parts.append(f'''            <tr>
                <td><span class="badge badge-ast">{issue.get('type', 'N/A')}</span></td>
                <td>{filename}</td>
                <td>{issue.get('line', 'N/A')}</td>
                <td>{str(issue.get('description', 'N/A'))[:100]}...</td>
            </tr>''')
        
        html_parts.append('''        </tbody>
    </table>''')
        
        if len(ast_issues) > 50:
            html_parts.append(f'    <p>... y {len(ast_issues) - 50} issues más (ver reporte JSON completo)</p>')
    else:
        html_parts.append('    <p>✅ No se encontraron issues de AST</p>')
    
    html_parts.append(f'''
    <hr>
    <footer>
        <p>Generated by TDH Engine v0.2.0 • {timestamp}</p>
        <p><em>Note: This is a filtered report showing only high-priority security issues.</em></p>
    </footer>
</body>
</html>''')
    
    return '\n'.join(html_parts)

def _generate_text_summary(resultados):
    """Genera un resumen en texto para consola/archivo"""
    
    summary_lines = [
        "=" * 60,
        "TDH SECURITY ANALYSIS SUMMARY (FILTERED)",
        "=" * 60,
        "Showing only CRITICAL/HIGH severity issues with noise filtered",
        ""
    ]
    
    # SAST Summary
    sast_data = resultados.get('sast', {})
    sast_issues = sast_data.get('issues', [])
    
    summary_lines.append("🔧 SAST ANALYSIS:")
    summary_lines.append(f"  Total Issues: {len(sast_issues)}")
    
    if sast_issues:
        # Contar por severidad
        by_severity = {}
        for issue in sast_issues:
            severity = issue.get('severity', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        if by_severity:
            summary_lines.append("  By Severity:")
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO', 'UNKNOWN']:
                if severity in by_severity:
                    summary_lines.append(f"    {severity}: {by_severity[severity]}")
        
        # Mostrar issues críticos
        critical_high_issues = [
            issue for issue in sast_issues 
            if issue.get('severity') in ['CRITICAL', 'HIGH']
        ]
        
        if critical_high_issues:
            summary_lines.append("")
            summary_lines.append("⛔ CRITICAL/HIGH PRIORITY ISSUES:")
            for i, issue in enumerate(critical_high_issues[:20], 1):
                tool = issue.get('tool', 'unknown')
                message = str(issue.get('message', ''))
                filename = issue.get('file', '')
                line = issue.get('line', '')
                
                # Acortar nombres de archivo largos
                if len(filename) > 50:
                    filename = "..." + filename[-47:]
                
                summary_lines.append(f"  {i:2d}. [{tool:10}] {message[:60]}...")
                summary_lines.append(f"      📍 {filename}:{line}")
    else:
        summary_lines.append("  ✅ No critical/high severity issues found (good job!)")
    
    # AST Summary
    ast_data = resultados.get('ast', {})
    ast_issues = ast_data.get('data', {}).get('issues', []) if ast_data.get('success') else []
    
    summary_lines.append("")
    summary_lines.append("🧬 AST ANALYSIS:")
    summary_lines.append(f"  Total Issues: {len(ast_issues)}")
    
    if ast_issues:
        # Contar por tipo
        by_type = {}
        for issue in ast_issues:
            issue_type = issue.get('type', 'UNKNOWN')
            by_type[issue_type] = by_type.get(issue_type, 0) + 1
        
        if by_type:
            summary_lines.append("  By Type:")
            for issue_type, count in sorted(by_type.items()):
                summary_lines.append(f"    {issue_type}: {count}")
    else:
        summary_lines.append("  (AST analysis not run or no issues found)")
    
    summary_lines.append("")
    summary_lines.append("=" * 60)
    summary_lines.append("✅ Filtered analysis complete")
    summary_lines.append("=" * 60)
    
    return "\n".join(summary_lines)

def _print_summary(resultados, reportes_generados):
    """Imprime resumen en consola"""
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL ANÁLISIS (FILTRADO)")
    print("=" * 60)
    print("Mostrando solo issues CRITICAL/HIGH con ruido filtrado")
    
    # SAST
    sast_issues = resultados.get('sast', {}).get('issues', [])
    print(f"\n🔧 SAST Issues (filtrados): {len(sast_issues)}")
    
    if sast_issues:
        by_severity = {}
        for issue in sast_issues:
            severity = issue.get('severity', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            if by_severity.get(severity):
                print(f"  {severity}: {by_severity[severity]}")
        
        # Mostrar algunos issues críticos
        critical_issues = [i for i in sast_issues if i.get('severity') == 'CRITICAL']
        high_issues = [i for i in sast_issues if i.get('severity') == 'HIGH']
        
        if critical_issues:
            print(f"\n🔴 CRITICAL Issues ({len(critical_issues)}):")
            for i, issue in enumerate(critical_issues[:5], 1):
                print(f"  {i}. [{issue.get('tool')}] {issue.get('message', '')[:60]}...")
        
        if high_issues:
            print(f"\n🟠 HIGH Issues ({len(high_issues)}):")
            for i, issue in enumerate(high_issues[:5], 1):
                print(f"  {i}. [{issue.get('tool')}] {issue.get('message', '')[:60]}...")
    
    # AST
    ast_data = resultados.get('ast', {})
    if ast_data.get('success'):
        ast_issues = ast_data.get('data', {}).get('issues', [])
        print(f"\n🧬 AST Issues: {len(ast_issues)}")
    else:
        error_msg = ast_data.get('error', 'No ejecutado')
        if error_msg != 'No ejecutado':
            print(f"\n🧬 AST: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}")
        else:
            print("\n🧬 AST: No ejecutado")
    
    # Reportes
    if reportes_generados:
        print("\n📁 REPORTES GENERADOS:")
        for formato, ruta in reportes_generados:
            print(f"  {formato}: {ruta}")
    else:
        print("\n📁 No se generaron reportes (posible error en el análisis)")
    
    print("\n" + "=" * 60)
    print("✅ ANÁLISIS FILTRADO COMPLETADO")
    print("=" * 60)

@cli.command()
def version():
    """Muestra la versión de TDH Unified Analyzer"""
    print("TDH Unified Analyzer v0.2.0")
    print("Test-Driven Hardening Engine")

if __name__ == '__main__':
    cli()