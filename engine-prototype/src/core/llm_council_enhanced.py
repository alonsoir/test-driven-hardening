# src/core/llm_council_enhanced.py
"""
Consejo de LLMs mejorado con máquinas de estados y orquestación completa.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

from .llm_state_machine import LLMStateMachine
from .llm_council import LLMCouncil
from .git_worktree_manager import GitWorktreeManager


class EnhancedLLMCouncil(LLMCouncil):
    """Consejo extendido con máquinas de estados por LLM."""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.state_machines: Dict[str, LLMStateMachine] = {}
        self.solutions: Dict[str, List[Dict]] = {}  # vulnerability_id -> solutions
        self.worktree_manager: Optional[GitWorktreeManager] = None
        
    async def initialize_with_state_machines(self, worktree_manager: GitWorktreeManager):
        """Inicializa consejo con máquinas de estados para cada LLM."""
        print("🏗️  Inicializando consejo con máquinas de estados...")
        
        # Inicializar consejo base
        await self.initialize_council()
        
        if not self.llms:
            print("⚠️  No se pudieron inicializar LLMs, usando configuración de respaldo")
            return None
        
        self.worktree_manager = worktree_manager
        
        print(f"🏗️  Creando máquinas de estados para {len(self.llms)} LLMs...")
        
        # Crear máquina de estados para cada LLM disponible
        for llm in self.llms:
            try:
                state_machine = LLMStateMachine(
                    llm=llm,
                    llm_name=llm.name,
                    worktree_manager=worktree_manager,
                    council=self
                )
                self.state_machines[llm.name] = state_machine
                print(f"   ✅ Máquina creada para {llm.name}")
            except Exception as e:
                print(f"   ❌ Error creando máquina para {llm.name}: {e}")
        
        print(f"✅ {len(self.state_machines)} máquinas de estados creadas")
        return self.state_machines
    
    async def orchestrate_vulnerability_fix(self, 
                                           repo_url: str,
                                           vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orquesta el fix completo de una vulnerabilidad usando máquinas de estados.
        
        Args:
            repo_url: URL del repositorio
            vulnerability: Vulnerabilidad detectada por SAST
            
        Returns:
            Resultados de todos los LLMs
        """
        if not self.state_machines:
            raise ValueError("Máquinas de estados no inicializadas. Llama a initialize_with_state_machines primero.")
        
        vulnerability_id = vulnerability.get('rule_id', 'unknown')
        print(f"\n{'='*60}")
        print(f"🏛️  CONSEJO ORQUESTANDO FIX PARA VULNERABILIDAD: {vulnerability_id}")
        print(f"{'='*60}")
        print(f"📋 Descripción: {vulnerability.get('message', 'Sin descripción')}")
        print(f"📁 Archivo: {vulnerability.get('file', 'Desconocido')}")
        print(f"⚠️  Severidad: {vulnerability.get('severity', 'Desconocida')}")
        print(f"{'='*60}\n")
        
        # Configurar worktree manager si no está configurado
        if not self.worktree_manager.is_initialized():
            await self.worktree_manager.initialize(repo_url)
        
        # Crear worktrees y branches para cada LLM
        llm_tasks = {}
        results = {}
        
        # Limitar a 3 LLMs para pruebas (impar para votación)
        available_machines = list(self.state_machines.items())[:3]
        
        if len(available_machines) < 1:
            raise ValueError("Se necesitan al menos 1 máquina de estados disponible")
        
        print(f"🚀 Preparando {len(available_machines)} LLMs para trabajo paralelo...")
        
        for llm_name, state_machine in available_machines:
            try:
                print(f"\n📋 Preparando {llm_name}...")
                
                # Crear worktree para este LLM
                worktree_info = self.worktree_manager.create_worktree_for_llm(
                    llm_name=llm_name,
                    issue_id=vulnerability_id
                )
                
                if not worktree_info:
                    raise ValueError(f"No se pudo crear worktree para {llm_name}")
                
                worktree_dir, branch_name = worktree_info
                
                print(f"   📁 Worktree: {worktree_dir}")
                print(f"   🌿 Branch: {branch_name}")
                
                # Ejecutar workflow completo
                task = asyncio.create_task(
                    state_machine.execute_workflow(vulnerability, worktree_dir, branch_name),
                    name=f"workflow_{llm_name}_{vulnerability_id}"
                )
                llm_tasks[llm_name] = (task, worktree_dir, branch_name)
                
                print(f"   ✅ {llm_name} listo para ejecución")
                
            except Exception as e:
                print(f"❌ Error preparando {llm_name}: {e}")
                results[llm_name] = {
                    'success': False, 
                    'error': str(e),
                    'artifacts': None
                }
        
        # Ejecutar workflows en paralelo
        if llm_tasks:
            print(f"\n🚀 Ejecutando {len(llm_tasks)} workflows en paralelo...")
            print("⏳ Esto puede tomar varios minutos...\n")
            
            # Recolectar tareas
            tasks = [task for task, _, _ in llm_tasks.values()]
            
            # Ejecutar en paralelo con timeout
            try:
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.TimeoutError:
                print("⏰ Timeout en ejecución paralela")
                task_results = [TimeoutError("Timeout") for _ in tasks]
            
            # Procesar resultados
            for (llm_name, (_, worktree_dir, branch_name)), result in zip(llm_tasks.items(), task_results):
                print(f"\n📊 Procesando resultados de {llm_name}...")
                
                if isinstance(result, Exception):
                    error_msg = f"Excepción en workflow: {str(result)}"
                    print(f"   ❌ {error_msg}")
                    results[llm_name] = {
                        'success': False,
                        'error': error_msg,
                        'artifacts': None,
                        'worktree_dir': worktree_dir,
                        'branch': branch_name
                    }
                else:
                    print(f"   ✅ Workflow completado exitosamente")
                    results[llm_name] = {
                        'success': True,
                        'error': None,
                        'artifacts': result,
                        'worktree_dir': worktree_dir,
                        'branch': branch_name
                    }
                    
                    # Aplicar fix al worktree si existe
                    if result.get('artifacts', {}).get('fix_code'):
                        try:
                            print(f"   🔧 Aplicando fix de {llm_name} al repositorio...")
                            
                            fixed_files = result['artifacts']['fix_code'].get('fixed_files', {})
                            if fixed_files:
                                # Aplicar cada archivo fijo
                                for file_path, fixed_code in fixed_files.items():
                                    full_path = Path(worktree_dir) / file_path
                                    
                                    # Asegurar directorio existe
                                    full_path.parent.mkdir(parents=True, exist_ok=True)
                                    
                                    # Escribir código fijo
                                    with open(full_path, 'w', encoding='utf-8') as f:
                                        f.write(fixed_code)
                                    
                                    print(f"   📝 Archivo actualizado: {file_path}")
                                
                                # Hacer commit
                                commit_message = self._generate_commit_message(
                                    llm_name=llm_name,
                                    vulnerability=vulnerability,
                                    artifacts=result['artifacts']
                                )
                                
                                commit_hash = self.worktree_manager.commit_changes(
                                    branch_name=branch_name,
                                    message=commit_message
                                )
                                
                                if commit_hash:
                                    print(f"   ✅ Commit realizado: {commit_hash[:8]}")
                                    results[llm_name]['commit'] = commit_hash[:8]
                                    
                                    # Hacer push a GitHub
                                    print(f"   📤 Haciendo push de {branch_name}...")
                                    success, push_url = self.worktree_manager.push_to_github(branch_name)
                                    
                                    if success and push_url:
                                        print(f"   ✅ Push exitoso")
                                        
                                        # Crear PR
                                        pr_title = f"Fix de seguridad por {llm_name}: {vulnerability.get('rule_id', 'Vulnerabilidad')}"
                                        pr_body = self._generate_pr_body(
                                            llm_name=llm_name,
                                            vulnerability=vulnerability,
                                            artifacts=result['artifacts']
                                        )
                                        
                                        pr_url = self.worktree_manager.create_pull_request(
                                            branch_name=branch_name,
                                            title=pr_title,
                                            body=pr_body
                                        )
                                        
                                        if pr_url:
                                            results[llm_name]['pr_url'] = pr_url
                                            print(f"   🔗 PR creado: {pr_url}")
                                        else:
                                            print(f"   ⚠️  No se pudo crear PR")
                                    else:
                                        print(f"   ⚠️  No se pudo hacer push")
                                else:
                                    print(f"   ⚠️  No se pudo hacer commit")
                            else:
                                print(f"   ⚠️  No hay archivos fijos para aplicar")
                                
                        except Exception as e:
                            error_msg = f"Error aplicando fix: {str(e)}"
                            print(f"   ❌ {error_msg}")
                            results[llm_name]['error'] = error_msg
        
        # Guardar soluciones para análisis posterior
        self.solutions[vulnerability_id] = results
        
        # Realizar sesión de consejo
        await self._council_session(vulnerability_id)
        
        # Generar reporte comparativo
        report = self._generate_comparative_report(vulnerability_id, results)
        
        print(f"\n{'='*60}")
        print(f"🎯 ORQUESTACIÓN COMPLETADA PARA {vulnerability_id}")
        print(f"{'='*60}")
        
        return report
    
    async def present_solution(self, llm_name: str, solution: Dict, 
                               vulnerability: Dict[str, Any]) -> List[str]:
        """
        Presenta una solución al consejo para discusión.
        
        Args:
            llm_name: Nombre del LLM que presenta
            solution: Solución completa con artefactos
            vulnerability: Vulnerabilidad original
            
        Returns:
            Lista de feedback/comentarios del consejo
        """
        print(f"\n💬 {llm_name} presenta solución al consejo...")
        
        # Por ahora, simular feedback
        # En el futuro, esto involucrará discusión real entre LLMs
        
        feedback = [
            f"Solución presentada por {llm_name}",
            f"Vulnerabilidad: {vulnerability.get('rule_id', 'unknown')}",
            f"Archivo: {vulnerability.get('file', 'unknown')}",
            f"Estado: Revisión pendiente"
        ]
        
        return feedback
    
    async def _council_session(self, vulnerability_id: str):
        """Sesión de consejo donde los LLMs discuten soluciones."""
        print(f"\n{'='*60}")
        print(f"🏛️  SESIÓN DE CONSEJO PARA {vulnerability_id}")
        print(f"{'='*60}")
        
        if vulnerability_id not in self.solutions:
            print("⚠️  No hay soluciones para discutir")
            return
        
        solutions = self.solutions[vulnerability_id]
        successful_solutions = {k: v for k, v in solutions.items() 
                              if v.get('success') and v.get('artifacts')}
        
        if len(successful_solutions) < 1:
            print("⚠️  No hay soluciones exitosas para discusión")
            return
        
        print(f"📊 Soluciones exitosas: {len(successful_solutions)}/{len(solutions)}")
        
        # Mostrar resumen comparativo
        print("\n📋 RESUMEN COMPARATIVO:")
        print("-" * 40)
        
        for llm_name, solution in successful_solutions.items():
            artifacts = solution.get('artifacts', {})
            
            print(f"\n👤 **{llm_name}**:")
            
            # Resumen de análisis
            analysis = artifacts.get('analysis', {}).get('analysis', {})
            if analysis:
                print(f"   🔍 Análisis: {analysis.get('what', 'N/A')[:80]}...")
                print(f"   ⚠️  Impacto: {analysis.get('potential_impact', 'N/A')}")
            
            # Resumen de test
            test = artifacts.get('test_design', {}).get('test_design', {})
            if test:
                print(f"   🧪 Test: {test.get('test_concept', 'N/A')[:80]}...")
            
            # Resumen de fix
            fix = artifacts.get('fix_code', {})
            if fix.get('fixed_files'):
                file_count = len(fix['fixed_files'])
                print(f"   🔧 Fix: {file_count} archivo(s) modificado(s)")
            
            # PR si existe
            if solution.get('pr_url'):
                print(f"   🔗 PR: {solution['pr_url']}")
        
        print(f"\n{'='*60}")
        print("💡 **RECOMENDACIONES DEL CONSEJO:**")
        print("-" * 40)
        
        # Análisis simple de las soluciones
        if len(successful_solutions) > 1:
            print("1. **Revisar todas las PRs generadas** para comparar enfoques")
            print("2. **Combinar lo mejor** de cada solución si es posible")
            print("3. **Validar tests** en entorno de staging antes de merge")
        else:
            print("1. **Revisar la PR generada** y validar el fix")
            print("2. **Ejecutar tests de seguridad** adicionales")
            print("3. **Considerar revisión manual** por experto en seguridad")
        
        print(f"{'='*60}")
    
    def _generate_commit_message(self, llm_name: str, vulnerability: Dict, 
                                artifacts: Dict) -> str:
        """Genera mensaje de commit informativo."""
        rule_id = vulnerability.get('rule_id', 'Vulnerabilidad')
        severity = vulnerability.get('severity', 'Desconocida')
        file = vulnerability.get('file', 'Desconocido')
        
        summary = artifacts.get('documentation', {}).get('documentation', {}).get('summary', 
                    f"Fix de seguridad para {rule_id}")
        
        commit_msg = f"""Fix de seguridad por {llm_name}

{summary}

Detalles:
- Vulnerabilidad: {rule_id} ({severity})
- Archivo: {file}
- CWE: {vulnerability.get('cwe', 'N/A')}
- OWASP: {vulnerability.get('owasp', 'N/A')}

Cambios:
{self._summarize_fix_changes(artifacts.get('fix_code', {}))}

Validación:
{self._summarize_test(artifacts.get('test_design', {}))}

Referencias: {vulnerability.get('more_info', 'N/A')}"""
        
        return commit_msg
    
    def _generate_pr_body(self, llm_name: str, vulnerability: Dict, 
                         artifacts: Dict) -> str:
        """Genera cuerpo de PR detallado."""
        
        # Extraer información
        analysis = artifacts.get('analysis', {}).get('analysis', {})
        test_design = artifacts.get('test_design', {}).get('test_design', {})
        documentation = artifacts.get('documentation', {}).get('documentation', {})
        
        pr_body = f"""# Fix de Seguridad por {llm_name}

## Vulnerabilidad
- **ID**: {vulnerability.get('rule_id', 'N/A')}
- **Severidad**: {vulnerability.get('severity', 'N/A')} 
- **Confianza**: {vulnerability.get('confidence', 'N/A')}
- **Archivo**: `{vulnerability.get('file', 'N/A')}:{vulnerability.get('line', 'N/A')}`
- **CWE**: {vulnerability.get('cwe', 'N/A')}
- **OWASP**: {vulnerability.get('owasp', 'N/A')}

## Análisis
{analysis.get('what', 'N/A')}

**Impacto**: {analysis.get('potential_impact', 'N/A')} - {analysis.get('impact_justification', 'N/A')}

**Escenario de explotación**: {analysis.get('exploitation_scenario', 'N/A')}

## Solución Propuesta
{documentation.get('fix_explanation', {}).get('approach', 'N/A') if documentation else 'N/A'}

### Cambios Realizados
{self._summarize_fix_changes(artifacts.get('fix_code', {}))}

## Validación
### Test Conceptual
{test_design.get('test_concept', 'N/A') if test_design else 'N/A'}

### Pasos para Verificar
{documentation.get('validation_instructions', {}).get('test_steps', ['N/A']) if documentation else ['N/A']}

## Consideraciones
- **Impacto en rendimiento**: {documentation.get('considerations', {}).get('performance_impact', 'N/A') if documentation else 'N/A'}
- **Compatibilidad**: {documentation.get('considerations', {}).get('backward_compatibility', 'N/A') if documentation else 'N/A'}

## Referencias
{vulnerability.get('more_info', 'N/A')}

---

*Este PR fue generado automáticamente por el TDH Engine*"""
        
        return pr_body
    
    def _summarize_fix_changes(self, fix_code: Dict) -> str:
        """Resume los cambios en el fix."""
        if not fix_code or 'fixed_files' not in fix_code:
            return "- No se especificaron cambios"
        
        changes = []
        for file_path, _ in fix_code['fixed_files'].items():
            changes.append(f"- `{file_path}`")
        
        return '\n'.join(changes) if changes else "- Cambios no especificados"
    
    def _summarize_test(self, test_design: Dict) -> str:
        """Resume el test conceptual."""
        if not test_design or 'test_design' not in test_design:
            return "Test no especificado"
        
        test_info = test_design['test_design']
        return f"{test_info.get('test_concept', 'Test no especificado')}\nTipo: {test_info.get('test_type', 'N/A')}"
    
    def _generate_comparative_report(self, vulnerability_id: str, 
                                    results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera reporte comparativo de todas las soluciones."""
        
        successful = {k: v for k, v in results.items() if v.get('success')}
        failed = {k: v for k, v in results.items() if not v.get('success')}
        
        report = {
            'vulnerability_id': vulnerability_id,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_llms': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': f"{(len(successful)/len(results)*100):.1f}%" if results else "0%"
            },
            'solutions': {},
            'comparative_analysis': {},
            'recommendations': []
        }
        
        # Agregar detalles de cada solución exitosa
        for llm_name, solution in successful.items():
            report['solutions'][llm_name] = {
                'status': 'success',
                'branch': solution.get('branch'),
                'worktree_dir': solution.get('worktree_dir'),
                'pr_url': solution.get('pr_url'),
                'commit': solution.get('commit'),
                'duration_seconds': solution.get('artifacts', {}).get('duration_seconds'),
                'has_test': bool(solution.get('artifacts', {}).get('test_design')),
                'has_fix': bool(solution.get('artifacts', {}).get('fix_code')),
                'has_documentation': bool(solution.get('artifacts', {}).get('documentation'))
            }
        
        # Agregar fallos
        for llm_name, solution in failed.items():
            report['solutions'][llm_name] = {
                'status': 'failed',
                'error': solution.get('error'),
                'worktree_dir': solution.get('worktree_dir')
            }
        
        # Análisis comparativo básico
        if len(successful) > 1:
            report['comparative_analysis'] = {
                'multiple_solutions': True,
                'recommended_approach': 'Revisar todas las PRs y combinar lo mejor de cada una',
                'note': f'{len(successful)} soluciones diferentes generadas. Comparar enfoques.'
            }
        elif len(successful) == 1:
            llm_name = list(successful.keys())[0]
            report['comparative_analysis'] = {
                'multiple_solutions': False,
                'single_solution_by': llm_name,
                'recommended_approach': f'Revisar PR de {llm_name} y validar con tests'
            }
        else:
            report['comparative_analysis'] = {
                'multiple_solutions': False,
                'all_failed': True,
                'recommended_approach': 'Revisión manual necesaria. Ningún LLM pudo generar solución.'
            }
        
        # Recomendaciones
        if len(successful) >= 2:
            report['recommendations'] = [
                "1. Revisar todas las PRs generadas para comparar diferentes enfoques",
                "2. Considerar combinar elementos de múltiples soluciones",
                "3. Ejecutar tests de seguridad en cada branch antes de merge",
                "4. Realizar revisión de código por humano experto en seguridad"
            ]
        elif len(successful) == 1:
            report['recommendations'] = [
                "1. Revisar la PR generada y validar el fix",
                "2. Ejecutar tests de seguridad específicos para esta vulnerabilidad",
                "3. Considerar revisión por otro experto antes de merge"
            ]
        else:
            report['recommendations'] = [
                "1. Revisión manual necesaria - los LLMs no pudieron generar solución",
                "2. Analizar manualmente la vulnerabilidad y diseñar fix",
                "3. Considerar si la vulnerabilidad es un falso positivo"
            ]
        
        return report
    
    def get_council_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del consejo."""
        status = {
            'initialized': len(self.state_machines) > 0,
            'llm_count': len(self.state_machines),
            'llm_names': list(self.state_machines.keys()),
            'solutions_count': len(self.solutions),
            'worktree_manager_ready': self.worktree_manager and self.worktree_manager.is_initialized()
        }
        
        # Estado de cada máquina
        status['machines'] = {}
        for name, machine in self.state_machines.items():
            status['machines'][name] = machine.get_status()
        
        return status