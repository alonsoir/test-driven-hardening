#!/usr/bin/env python3
"""
TDH Engine - Test-Driven Hardening Engine
CLI principal con comandos para SAST, consejo de LLMs y máquinas de estados.
"""

import asyncio
import sys
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

# Importaciones internas
try:
    from src.core.sast_orchestrator import SASTOrchestrator
    from src.core.git_worktree_manager import GitWorktreeManager
    from src.core.llm_council import LLMCouncil
    from src.core.llm_council_enhanced import EnhancedLLMCouncil
    from src.core.llm_state_machine import LLMStateMachine, LLMState
    from src.adapters.openrouter_adapter import OpenRouterAdapter
    print("✅ Módulos principales cargados")
except ImportError as e:
    print(f"⚠️  Algunos módulos no pudieron cargarse: {e}")
    print("⚠️  Algunas funcionalidades pueden estar limitadas")
    
    # Mock classes para permitir que el CLI funcione
    class SASTOrchestrator:
        def __init__(self, config_path=None):
            pass
        
        async def analyze_repository(self, repo_path, output_dir=None):
            return {"issues": [], "summary": {"total": 0}}
    
    class GitWorktreeManager:
        def __init__(self, base_worktree_dir, github_token=None):
            self.base_worktree_dir = base_worktree_dir
            
        async def initialize(self, repo_url):
            pass
        
        def is_initialized(self):
            return False
    
    class LLMCouncil:
        def __init__(self, config_path=None):
            pass
        
        async def initialize_council(self):
            return []
    
    class EnhancedLLMCouncil:
        def __init__(self, config_path=None):
            pass
        
        async def initialize_with_state_machines(self, worktree_manager):
            return {}


def load_config(config_name: str) -> Dict[str, Any]:
    """Carga archivos de configuración YAML."""
    config_dir = Path("config")
    config_file = config_dir / f"{config_name}.yaml"
    
    if not config_file.exists():
        # Crear configuración por defecto si no existe
        if config_name == "sast_tools":
            default_config = {
                "tools": {
                    "cppcheck": {"enabled": True, "args": "--enable=all"},
                    "bandit": {"enabled": True, "args": "-r . -f json"},
                    "semgrep": {"enabled": True, "args": "--config=auto"},
                    "flawfinder": {"enabled": True, "args": "--quiet"},
                    "safety": {"enabled": True, "args": "check"}
                }
            }
            config_dir.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f)
            return default_config
        elif config_name == "llm_council":
            default_config = {
                "llm_configs": {
                    "claude-3-5-sonnet": {
                        "provider": "openrouter",
                        "model": "claude-3.5-sonnet",
                        "max_tokens": 4000,
                        "temperature": 0.1,
                        "priority": 1
                    },
                    "gpt-4-turbo": {
                        "provider": "openrouter",
                        "model": "gpt-4-turbo",
                        "max_tokens": 4000,
                        "temperature": 0.1,
                        "priority": 2
                    },
                    "deepseek-coder": {
                        "provider": "openrouter",
                        "model": "deepseek-coder",
                        "max_tokens": 4000,
                        "temperature": 0.1,
                        "priority": 3
                    }
                },
                "council_settings": {
                    "min_llms": 3,
                    "max_llms": 5,
                    "preferred_count": 3,
                    "timeout_seconds": 300
                }
            }
            config_dir.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f)
            return default_config
        else:
            return {}
    
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


async def handle_sast_analysis(args):
    """Manejador del comando de análisis SAST."""
    print("\n" + "="*60)
    print("🔍 TDH ENGINE - ANÁLISIS SAST")
    print("="*60)
    print(f"📦 Repositorio: {args.repo_url}")
    print(f"📁 Directorio: {args.workdir}")
    print(f"📊 Output: {args.output}")
    print("="*60)
    
    try:
        # Inicializar SAST orchestrator
        sast_config = load_config("sast_tools")
        orchestrator = SASTOrchestrator(config_path=args.config)
        
        # Ejecutar análisis
        results = await orchestrator.analyze_repository(
            repo_path=args.workdir if args.workdir else args.repo_url,
            output_dir=args.output
        )
        
        # Mostrar resultados
        print(f"\n📊 RESULTADOS DEL ANÁLISIS SAST:")
        print(f"   Total de issues: {results.get('summary', {}).get('total', 0)}")
        
        # Agrupar por severidad
        severities = {}
        for issue in results.get('issues', []):
            sev = issue.get('severity', 'UNKNOWN')
            severities[sev] = severities.get(sev, 0) + 1
        
        for sev, count in severities.items():
            print(f"   {sev}: {count}")
        
        # Guardar resultados si se especificó output
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)  # ¡CREAR DIRECTORIO!
            output_file = output_dir / "sast_results.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Resultados guardados en: {output_file}")
        
        # Mostrar issues críticos si existen
        critical_issues = [i for i in results.get('issues', []) 
                          if i.get('severity') == 'CRITICAL']
        
        if critical_issues:
            print(f"\n⚠️  VULNERABILIDADES CRÍTICAS ENCONTRADAS ({len(critical_issues)}):")
            for idx, issue in enumerate(critical_issues[:5], 1):  # Mostrar solo 5
                print(f"\n   {idx}. {issue.get('rule_id', 'Unknown')}")
                print(f"      📄 {issue.get('file', 'Unknown')}:{issue.get('line', 'Unknown')}")
                print(f"      📝 {issue.get('message', 'No description')[:100]}...")
        
        print("\n✅ Análisis SAST completado")
        
    except Exception as e:
        print(f"\n❌ Error en análisis SAST: {e}")
        import traceback
        traceback.print_exc()


async def handle_council_analysis(args):
    """Manejador del comando de consejo de LLMs."""
    print("\n" + "="*60)
    print("🏛️  TDH ENGINE - CONSEJO DE LLMs")
    print("="*60)
    print(f"📦 Repositorio: {args.repo_url}")
    print(f"🧠 LLMs: {args.llm_count}")
    print(f"📁 Worktrees: {args.worktree_base}")
    print("="*60)
    
    try:
        # Cargar configuración
        council_config = load_config("llm_council")
        
        # Inicializar gestor de worktrees
        worktree_manager = GitWorktreeManager(
            base_worktree_dir=Path(args.worktree_base),
            github_token=args.github_token
        )
        
        await worktree_manager.initialize(args.repo_url)
        
        # Inicializar consejo
        council = LLMCouncil(config_path=args.config)
        llms = await council.initialize_council()
        
        print(f"\n✅ Consejo inicializado con {len(llms)} LLMs")
        
        # Preparar contexto para LLMs
        print("\n📋 Preparando contexto para LLMs...")
        
        # Buscar vulnerabilidades (usar SAST o mock)
        sast_config = load_config("sast_tools")
        orchestrator = SASTOrchestrator(config_path=args.config)
        
        # Analizar repositorio
        results = await orchestrator.analyze_repository(
            repo_path=worktree_manager.repo_dir if hasattr(worktree_manager, 'repo_dir') else args.repo_url
        )
        
        # Filtrar vulnerabilidades críticas
        critical_issues = [i for i in results.get('issues', []) 
                          if i.get('severity') == 'CRITICAL']
        
        if not critical_issues:
            print("⚠️  No se encontraron vulnerabilidades críticas, usando ejemplo...")
            # Usar vulnerabilidad de ejemplo
            critical_issues = [{
                'rule_id': 'CWE-78',
                'severity': 'CRITICAL',
                'confidence': 'HIGH',
                'message': 'Possible command injection',
                'file': 'src/vulnerable.c',
                'line': 42,
                'cwe': 'CWE-78',
                'owasp': 'A1:2017-Injection',
                'more_info': 'https://cwe.mitre.org/data/definitions/78.html'
            }]
        
        # Seleccionar primera vulnerabilidad
        target_vuln = critical_issues[0]
        
        print(f"\n🎯 Vulnerabilidad objetivo:")
        print(f"   ID: {target_vuln.get('rule_id')}")
        print(f"   Desc: {target_vuln.get('message')}")
        print(f"   Archivo: {target_vuln.get('file')}")
        
        # Crear worktrees para cada LLM
        print(f"\n📁 Creando worktrees para LLMs...")
        
        worktree_info = {}
        for llm in llms[:args.llm_count]:  # Limitar al número solicitado
            try:
                info = worktree_manager.create_worktree_for_llm(
                    llm_name=llm.name,
                    issue_id=target_vuln.get('rule_id', 'test')
                )
                if info:
                    worktree_dir, branch_name = info
                    worktree_info[llm.name] = {
                        'dir': worktree_dir,
                        'branch': branch_name
                    }
                    print(f"   ✅ {llm.name}: {branch_name}")
            except Exception as e:
                print(f"   ❌ Error creando worktree para {llm.name}: {e}")
        
        # Preparar y enviar contexto a cada LLM
        print(f"\n📤 Enviando contexto a LLMs...")
        
        llm_results = {}
        for llm_name, info in list(worktree_info.items())[:args.llm_count]:
            try:
                # Preparar contexto enriquecido
                context = await worktree_manager.prepare_llm_context(
                    issue_id=target_vuln.get('rule_id'),
                    sast_issue=target_vuln,
                    include_related=True
                )
                
                # Encontrar el LLM correspondiente
                llm_obj = next((l for l in llms if l.name == llm_name), None)
                if llm_obj:
                    # Solicitar fix al LLM
                    response = await llm_obj.generate_fix({
                        'vulnerability': target_vuln,
                        'context': context,
                        'worktree_dir': info['dir'],
                        'branch_name': info['branch']
                    })
                    
                    llm_results[llm_name] = {
                        'success': True,
                        'response': response,
                        'worktree': info
                    }
                    
                    print(f"   ✅ {llm_name}: Fix generado")
                    
                    # Intentar aplicar el fix
                    try:
                        if 'fixed_code' in response:
                            # Aplicar fix
                            commit_hash = worktree_manager.apply_llm_fix(
                                branch_name=info['branch'],
                                fixed_files=response['fixed_code'],
                                llm_name=llm_name
                            )
                            
                            if commit_hash:
                                # Hacer push
                                success, push_url = worktree_manager.push_to_github(info['branch'])
                                
                                if success:
                                    # Crear PR
                                    pr_url = worktree_manager.create_pull_request(info['branch'])
                                    llm_results[llm_name]['pr_url'] = pr_url
                                    print(f"   🔗 {llm_name}: PR creada - {pr_url}")
                    except Exception as e:
                        print(f"   ⚠️  Error aplicando fix de {llm_name}: {e}")
                
            except Exception as e:
                llm_results[llm_name] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"   ❌ Error con {llm_name}: {e}")
        
        # Guardar resultados
        output_dir = Path(args.output) if args.output else Path(".")
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / "council_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                'vulnerability': target_vuln,
                'llm_results': llm_results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n💾 Resultados guardados en: {results_file}")
        print("✅ Consejo de LLMs completado")
        
    except Exception as e:
        print(f"\n❌ Error en consejo de LLMs: {e}")
        import traceback
        traceback.print_exc()


async def handle_council_fix_with_states(args):
    """Manejador del comando council-fix-with-states."""
    print("\n" + "="*70)
    print("🤖 TDH ENGINE - FIX CON MÁQUINAS DE ESTADOS")
    print("="*70)
    print(f"📦 Repositorio: {args.repo_url}")
    print(f"🧠 LLMs: {args.llm_count} (con máquinas de estados)")
    print(f"⚠️  Severidad mínima: {args.severity}")
    print(f"📁 Worktrees: {args.worktree_base}")
    print("="*70 + "\n")
    
    try:
        # Paso 1: Ejecutar SAST para encontrar vulnerabilidades reales
        print("🔍 Paso 1: Ejecutando análisis SAST...")
        sast_config = load_config("sast_tools")
        orchestrator = SASTOrchestrator(config_path=args.config)
        
        sast_results = await orchestrator.analyze_repository(
            repo_path=args.repo_url,
            output_dir=None
        )
        
        if not sast_results or 'issues' not in sast_results:
            print("❌ No se encontraron vulnerabilidades o error en SAST")
            return
        
        # Filtrar por severidad
        critical_issues = [
            issue for issue in sast_results['issues']
            if issue.get('severity', '').upper() == args.severity.upper()
        ]
        
        if not critical_issues:
            print(f"⚠️  No hay vulnerabilidades con severidad {args.severity}")
            # Mostrar disponibles
            severities = {}
            for issue in sast_results['issues']:
                sev = issue.get('severity', 'UNKNOWN')
                severities[sev] = severities.get(sev, 0) + 1
            
            print("📊 Vulnerabilidades encontradas:")
            for sev, count in severities.items():
                print(f"   {sev}: {count}")
            return
        
        print(f"✅ Encontradas {len(critical_issues)} vulnerabilidades {args.severity}")
        
        # Seleccionar la primera vulnerabilidad para demostración
        target_vulnerability = critical_issues[0]
        print(f"\n🎯 Target: {target_vulnerability.get('rule_id', 'unknown')}")
        print(f"   Desc: {target_vulnerability.get('message', 'No description')}")
        print(f"   Archivo: {target_vulnerability.get('file', 'unknown')}")
        
        # Paso 2: Inicializar gestor de worktrees
        print("\n📁 Paso 2: Inicializando gestor de worktrees...")
        
        worktree_manager = GitWorktreeManager(
            base_worktree_dir=Path(args.worktree_base),
            github_token=args.github_token if hasattr(args, 'github_token') else None
        )
        
        await worktree_manager.initialize(args.repo_url)
        print(f"✅ Worktree manager inicializado")
        
        # Paso 3: Crear consejo con máquinas de estados
        print("\n🏛️  Paso 3: Creando consejo con máquinas de estados...")
        council = EnhancedLLMCouncil(config_path=args.config)
        
        state_machines = await council.initialize_with_state_machines(worktree_manager)
        
        if not state_machines:
            print("❌ No se pudieron crear máquinas de estados")
            return
        
        print(f"✅ Consejo inicializado con {len(state_machines)} máquinas de estados")
        
        # Paso 4: Orquestar fix de la vulnerabilidad
        print("\n🚀 Paso 4: Orquestando fix con máquinas de estados...")
        print("   Cada LLM ejecutará su workflow completo:")
        print("   1. 🔍 Analizar vulnerabilidad")
        print("   2. 🧪 Diseñar test conceptual")
        print("   3. 🔧 Diseñar fix")
        print("   4. 📝 Documentar solución")
        print("   5. 🏛️  Participar en consejo")
        print("   6. 🔗 Crear PR\n")
        
        results = await council.orchestrate_vulnerability_fix(
            repo_url=args.repo_url,
            vulnerability=target_vulnerability
        )
        
        # Paso 5: Guardar resultados
        print("\n💾 Paso 5: Guardando resultados...")
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Guardar reporte completo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"tdh_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Reporte guardado en: {report_file}")
        
        # Generar resumen en markdown
        summary_file = output_dir / f"tdh_summary_{timestamp}.md"
        await generate_summary_markdown(results, summary_file, target_vulnerability)
        
        print(f"✅ Resumen guardado en: {summary_file}")
        
        # Mostrar resultados finales
        print("\n" + "="*70)
        print("🎉 FIX CON MÁQUINAS DE ESTADOS COMPLETADO")
        print("="*70)
        
        successful = results.get('summary', {}).get('successful', 0)
        total = results.get('summary', {}).get('total_llms', 0)
        
        print(f"📊 Resultados: {successful}/{total} LLMs exitosos")
        
        # Mostrar PRs generadas
        prs = []
        for llm_name, solution in results.get('solutions', {}).items():
            if solution.get('pr_url'):
                prs.append(f"   • {llm_name}: {solution['pr_url']}")
        
        if prs:
            print("\n🔗 PRs Generadas:")
            for pr in prs:
                print(pr)
        
        print(f"\n📋 Ver reporte completo en: {report_file}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error en fix con máquinas de estados: {e}")
        import traceback
        traceback.print_exc()


async def generate_summary_markdown(results: Dict, output_file: Path, vulnerability: Dict):
    """Genera resumen markdown de los resultados."""
    
    summary = f"""# TDH Engine - Reporte de Ejecución

## 📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Vulnerabilidad Objetivo
- **ID**: {vulnerability.get('rule_id', 'N/A')}
- **Severidad**: {vulnerability.get('severity', 'N/A')}
- **Archivo**: `{vulnerability.get('file', 'N/A')}`
- **Línea**: {vulnerability.get('line', 'N/A')}
- **Descripción**: {vulnerability.get('message', 'N/A')}

## 📊 Resultados Generales
- **Total LLMs**: {results.get('summary', {}).get('total_llms', 0)}
- **Exitosos**: {results.get('summary', {}).get('successful', 0)}
- **Fallidos**: {results.get('summary', {}).get('failed', 0)}
- **Tasa de éxito**: {results.get('summary', {}).get('success_rate', '0%')}

## 🤖 Soluciones por LLM

"""
    
    for llm_name, solution in results.get('solutions', {}).items():
        status = "✅ ÉXITO" if solution.get('status') == 'success' else "❌ FALLO"
        
        summary += f"### {llm_name} - {status}\n\n"
        
        if solution.get('status') == 'success':
            summary += f"- **Rama**: `{solution.get('branch', 'N/A')}`\n"
            if solution.get('pr_url'):
                summary += f"- **PR**: [{solution.get('pr_url')}]({solution.get('pr_url')})\n"
            if solution.get('commit'):
                summary += f"- **Commit**: `{solution.get('commit')}`\n"
            
            summary += f"- **Test diseñado**: {'Sí' if solution.get('has_test') else 'No'}\n"
            summary += f"- **Fix generado**: {'Sí' if solution.get('has_fix') else 'No'}\n"
            summary += f"- **Documentación**: {'Sí' if solution.get('has_documentation') else 'No'}\n"
        else:
            summary += f"- **Error**: {solution.get('error', 'Desconocido')}\n"
        
        summary += "\n---\n\n"
    
    # Recomendaciones
    summary += "## 💡 Recomendaciones del Consejo\n\n"
    for rec in results.get('recommendations', []):
        summary += f"- {rec}\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)


async def handle_state_machine_test(args):
    """Manejador para probar máquinas de estados."""
    print("\n" + "="*70)
    print("🧪 TDH ENGINE - PRUEBA DE MÁQUINAS DE ESTADOS")
    print("="*70)
    
    try:
        # Importar módulo de prueba
        from tests.test_state_machines import test_state_machine_workflow, test_enhanced_council
        
        if args.test_type == "workflow":
            print("🧪 Probando workflow de máquina de estados...")
            await test_state_machine_workflow()
        elif args.test_type == "council":
            print("🏛️  Probando consejo mejorado...")
            await test_enhanced_council()
        else:
            print("🔧 Ejecutando todas las pruebas...")
            await test_state_machine_workflow()
            await test_enhanced_council()
        
        print("\n✅ Pruebas completadas exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()


async def handle_worktree_manager(args):
    """Manejador para operaciones con worktrees."""
    print("\n" + "="*60)
    print("📁 TDH ENGINE - GESTOR DE WORKTREES")
    print("="*60)
    
    try:
        worktree_manager = GitWorktreeManager(
            base_worktree_dir=Path(args.worktree_base),
            github_token=args.github_token
        )
        
        if args.action == "init":
            print(f"📦 Inicializando con repositorio: {args.repo_url}")
            await worktree_manager.initialize(args.repo_url)
            print("✅ Worktree manager inicializado")
            
        elif args.action == "create":
            print(f"🏗️  Creando worktree para LLM: {args.llm_name}")
            worktree_info = worktree_manager.create_worktree_for_llm(
                llm_name=args.llm_name,
                issue_id=args.issue_id or "test"
            )
            
            if worktree_info:
                worktree_dir, branch_name = worktree_info
                print(f"✅ Worktree creado:")
                print(f"   📁 Directorio: {worktree_dir}")
                print(f"   🌿 Rama: {branch_name}")
            else:
                print("❌ No se pudo crear worktree")
                
        elif args.action == "list":
            print("📋 Worktrees activos:")
            worktrees = worktree_manager.list_worktrees()
            for wt in worktrees:
                print(f"   • {wt}")
                
        elif args.action == "cleanup":
            print("🧹 Limpiando worktrees...")
            cleaned = worktree_manager.cleanup_worktrees()
            print(f"✅ Worktrees eliminados: {cleaned}")
        
        print("\n✅ Operación completada")
        
    except Exception as e:
        print(f"\n❌ Error en gestor de worktrees: {e}")


def main():
    """Función principal del CLI."""
    parser = argparse.ArgumentParser(
        description="TDH Engine - Test-Driven Hardening Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Análisis SAST de un repositorio
  python tdh_unified.py sast https://github.com/user/repo.git --output ./results
  
  # Consejo de LLMs tradicional
  python tdh_unified.py council https://github.com/user/repo.git --llm-count 3
  
  # Fix con máquinas de estados (recomendado)
  python tdh_unified.py council-fix-with-states https://github.com/user/repo.git
  
  # Probar máquinas de estados
  python tdh_unified.py test-states --test-type workflow
  
  # Gestionar worktrees
  python tdh_unified.py worktree init https://github.com/user/repo.git
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando: sast
    sast_parser = subparsers.add_parser('sast', help='Ejecutar análisis SAST')
    sast_parser.add_argument('repo_url', help='URL del repositorio')
    sast_parser.add_argument('--workdir', help='Directorio de trabajo (si ya está clonado)')
    sast_parser.add_argument('--output', '-o', help='Directorio para resultados')
    sast_parser.add_argument('--config', '-c', help='Archivo de configuración')
    sast_parser.set_defaults(func=handle_sast_analysis)
    
    # Comando: council
    council_parser = subparsers.add_parser('council', help='Consejo tradicional de LLMs')
    council_parser.add_argument('repo_url', help='URL del repositorio')
    council_parser.add_argument('--llm-count', '-n', type=int, default=3, help='Número de LLMs')
    council_parser.add_argument('--worktree-base', default='/tmp/tdh_worktrees', help='Directorio base para worktrees')
    council_parser.add_argument('--github-token', help='Token de GitHub (para PRs)')
    council_parser.add_argument('--output', '-o', help='Directorio para resultados')
    council_parser.add_argument('--config', '-c', help='Archivo de configuración')
    council_parser.set_defaults(func=handle_council_analysis)
    
    # Comando: council-fix-with-states
    council_fix_parser = subparsers.add_parser(
        'council-fix-with-states', 
        help='Fix completo con máquinas de estados (NUEVO)'
    )
    council_fix_parser.add_argument('repo_url', help='URL del repositorio')
    council_fix_parser.add_argument('--llm-count', '-n', type=int, default=3, 
                                   help='Número de LLMs (default: 3)')
    council_fix_parser.add_argument('--severity', default='CRITICAL',
                                   help='Severidad mínima (default: CRITICAL)')
    council_fix_parser.add_argument('--worktree-base', default='/tmp/tdh_worktrees',
                                   help='Directorio base para worktrees')
    council_fix_parser.add_argument('--github-token', help='Token de GitHub')
    council_fix_parser.add_argument('--output-dir', default='./tdh_results',
                                   help='Directorio para resultados')
    council_fix_parser.add_argument('--config', '-c', help='Archivo de configuración')
    council_fix_parser.set_defaults(func=handle_council_fix_with_states)
    
    # Comando: test-states
    test_parser = subparsers.add_parser('test-states', help='Probar máquinas de estados')
    test_parser.add_argument('--test-type', choices=['workflow', 'council', 'all'], 
                            default='all', help='Tipo de prueba')
    test_parser.add_argument('--config', '-c', help='Archivo de configuración')
    test_parser.set_defaults(func=handle_state_machine_test)
    
    # Comando: worktree
    worktree_parser = subparsers.add_parser('worktree', help='Gestionar worktrees')
    worktree_parser.add_argument('action', choices=['init', 'create', 'list', 'cleanup'],
                                help='Acción a realizar')
    worktree_parser.add_argument('repo_url', nargs='?', help='URL del repositorio (para init)')
    worktree_parser.add_argument('--llm-name', help='Nombre del LLM (para create)')
    worktree_parser.add_argument('--issue-id', help='ID de issue (para create)')
    worktree_parser.add_argument('--worktree-base', default='/tmp/tdh_worktrees',
                                help='Directorio base para worktrees')
    worktree_parser.add_argument('--github-token', help='Token de GitHub')
    worktree_parser.set_defaults(func=handle_worktree_manager)
    
    # Parsear argumentos
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Ejecutar comando
    try:
        asyncio.run(args.func(args))
    except AttributeError:
        parser.print_help()
    except KeyboardInterrupt:
        print("\n\n⏹️  Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Banner
    print("""
    ╔══════════════════════════════════════════════════╗
    ║      🤖 TDH ENGINE - Test-Driven Hardening       ║
    ║         Version 2.0 - Máquinas de Estados        ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Verificar configuración
    config_dir = Path("config")
    if not config_dir.exists():
        print("⚠️  Config directory not found. Creating with defaults...")
        config_dir.mkdir(exist_ok=True)
    
    # Verificar API key para OpenRouter
    if 'OPENROUTER_API_KEY' not in os.environ:
        print("⚠️  OPENROUTER_API_KEY no encontrada en variables de entorno")
        print("💡 Para usar LLMs, exporta tu API key:")
        print("   export OPENROUTER_API_KEY='tu-clave-aqui'")
        print("   O usa --github-token para operaciones básicas de Git\n")
    
    main()