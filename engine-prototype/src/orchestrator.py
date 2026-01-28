"""
Orquestador principal del TDH Engine.
Coordina el flujo completo de los 7 pasos del Test Driven Hardening.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from .core.scorer import FixScorer
from .core.workspace import WorkspaceManager
from .council.interface import LLMProvider
from .council.mock_provider import MockLLMProvider
from .council.deepseek_local import DeepSeekLocalProvider


class Vulnerability:
    """Representa una vulnerabilidad identificada."""
    
    def __init__(self, vuln_id: str, description: str, severity: str,
                 location: str, code_snippet: str, cwe: Optional[str] = None):
        self.id = vuln_id
        self.description = description
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.location = location  # archivo:linea
        self.code_snippet = code_snippet
        self.cwe = cwe
        
        # Estado del proceso
        self.status = "PENDING"  # PENDING, ANALYZING, FIXING, VALIDATED, RESOLVED
        self.poc = None
        self.fix_proposals = []
        self.selected_fix = None
        self.validation_result = None
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la vulnerabilidad a diccionario para serialización."""
        return {
            'id': self.id,
            'description': self.description,
            'severity': self.severity,
            'location': self.location,
            'cwe': self.cwe,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class TDHEngine:
    """Motor principal de Test Driven Hardening."""
    
    def __init__(self, providers: List[LLMProvider] = None, 
                 config: Dict[str, Any] = None):
        """
        Inicializa el motor TDH.
        
        Args:
            providers: Lista de proveedores LLM para el consejo
            config: Configuración del motor
        """
        self.config = config or {
            'max_parallel_agents': 3,
            'scoring_weights': {
                'complexity': 0.25,
                'dependencies': 0.20,
                'loc_delta': 0.15,
                'test_coverage': 0.25,
                'beauty': 0.15
            },
            'acceptance_threshold': 70.0,
            'log_level': 'INFO'
        }
        
        # Inicializar componentes
        self.scorer = FixScorer(self.config['scoring_weights'])
        self.workspace_manager = WorkspaceManager()
        
        # Proveedores LLM (si no se proporcionan, usar mock y deepseek local)
        self.providers = providers or [
            MockLLMProvider(),
            DeepSeekLocalProvider()
        ]
        
        # Estado del motor
        self.vulnerabilities = []
        self.results = []
        self.current_session_id = None
        
        # Crear directorio de logs si no existe
        os.makedirs('tdh_logs', exist_ok=True)
    
    async def analyze_repository(self, repo_path: str, 
                                severity_filter: List[str] = None) -> List[Dict]:
        """
        Analiza un repositorio en busca de vulnerabilidades.
        
        Args:
            repo_path: Ruta al repositorio local o URL remota
            severity_filter: Lista de severidades a incluir
            
        Returns:
            Lista de vulnerabilidades encontradas
        """
        print(f"[TDH Engine] Analizando repositorio: {repo_path}")
        
        # 1. Clonar/actualizar repositorio en workspace
        workspace_path = await self.workspace_manager.setup_workspace(repo_path)
        
        # 2. Ejecutar herramientas SAST (simulado por ahora)
        # TODO: Integrar con Semgrep, Bandit, etc.
        vulnerabilities = await self._simulate_sast_scan(workspace_path)
        
        # 3. Filtrar por severidad
        severity_filter = severity_filter or ['CRITICAL', 'HIGH']
        filtered_vulns = [
            v for v in vulnerabilities 
            if v.severity in severity_filter
        ]
        
        print(f"[TDH Engine] Encontradas {len(filtered_vulns)} vulnerabilidades relevantes")
        
        self.vulnerabilities = filtered_vulns
        return [v.to_dict() for v in filtered_vulns]
    
    async def process_vulnerability(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """
        Procesa una vulnerabilidad siguiendo los 7 pasos del TDH.
        
        Args:
            vulnerability: Vulnerabilidad a procesar
            
        Returns:
            Resultado completo del procesamiento
        """
        print(f"[TDH Engine] Procesando vulnerabilidad: {vulnerability.id}")
        
        vulnerability.status = "ANALYZING"
        result = {
            'vulnerability': vulnerability.to_dict(),
            'steps': [],
            'start_time': datetime.now().isoformat()
        }
        
        try:
            # PASO 1: Crear PoC (Proof of Concept)
            print(f"  [Paso 1/7] Generando PoC para {vulnerability.id}")
            poc_result = await self._generate_poc(vulnerability)
            vulnerability.poc = poc_result
            result['steps'].append({
                'step': 1,
                'name': 'PoC Generation',
                'result': poc_result,
                'success': poc_result is not None
            })
            
            if not poc_result:
                print(f"  ⚠️ No se pudo generar PoC para {vulnerability.id}")
                vulnerability.status = "FAILED"
                result['error'] = "No se pudo generar PoC"
                return result
            
            # PASO 2: Evaluar criticidad
            print(f"  [Paso 2/7] Evaluando criticidad de {vulnerability.id}")
            exploitability_score = self._assess_exploitability(vulnerability, poc_result)
            result['steps'].append({
                'step': 2,
                'name': 'Criticality Assessment',
                'result': {'exploitability_score': exploitability_score},
                'success': True
            })
            
            # PASO 3: Formular hipótesis inicial
            print(f"  [Paso 3/7] Formulando hipótesis para {vulnerability.id}")
            master_provider = self.providers[0]  # Primer proveedor como "master"
            initial_hypothesis = await master_provider.analyze_vulnerability({
                'vulnerability': vulnerability.to_dict(),
                'poc': poc_result,
                'code_snippet': vulnerability.code_snippet
            })
            
            result['steps'].append({
                'step': 3,
                'name': 'Initial Hypothesis',
                'result': initial_hypothesis,
                'success': initial_hypothesis is not None
            })
            
            if not initial_hypothesis:
                print(f"  ⚠️ No se pudo generar hipótesis para {vulnerability.id}")
                vulnerability.status = "FAILED"
                result['error'] = "No se pudo generar hipótesis"
                return result
            
            # PASO 4: Validación por el consejo
            print(f"  [Paso 4/7] Validando con consejo de {len(self.providers)} agentes")
            council_validation = await self._validate_with_council(
                vulnerability, poc_result, initial_hypothesis
            )
            
            result['steps'].append({
                'step': 4,
                'name': 'Council Validation',
                'result': council_validation,
                'success': council_validation.get('unanimous', False)
            })
            
            if not council_validation.get('unanimous', False):
                print(f"  ⚠️ El consejo no valida unánimemente {vulnerability.id}")
                vulnerability.status = "REVIEW_NEEDED"
                result['warning'] = "Validación no unánime"
                # Podemos continuar de todos modos, pero con advertencia
            
            # PASO 5: Generación de propuestas de fix
            print(f"  [Paso 5/7] Generando propuestas de fix para {vulnerability.id}")
            fix_proposals = await self._generate_fix_proposals(
                vulnerability, initial_hypothesis
            )
            vulnerability.fix_proposals = fix_proposals
            
            result['steps'].append({
                'step': 5,
                'name': 'Fix Proposal Generation',
                'result': {
                    'proposal_count': len(fix_proposals),
                    'proposals': fix_proposals
                },
                'success': len(fix_proposals) > 0
            })
            
            if not fix_proposals:
                print(f"  ⚠️ No se generaron propuestas de fix para {vulnerability.id}")
                vulnerability.status = "FAILED"
                result['error'] = "No se generaron propuestas de fix"
                return result
            
            # PASO 6: Evaluación y selección del mejor fix
            print(f"  [Paso 6/7] Evaluando {len(fix_proposals)} propuestas de fix")
            best_fix = await self._select_best_fix(vulnerability, fix_proposals)
            vulnerability.selected_fix = best_fix
            
            result['steps'].append({
                'step': 6,
                'name': 'Fix Selection',
                'result': best_fix,
                'success': best_fix is not None
            })
            
            if not best_fix:
                print(f"  ⚠️ No se pudo seleccionar un fix para {vulnerability.id}")
                vulnerability.status = "FAILED"
                result['error'] = "No se pudo seleccionar un fix"
                return result
            
            # PASO 7: Validación del fix seleccionado
            print(f"  [Paso 7/7] Validando fix seleccionado para {vulnerability.id}")
            validation_result = await self._validate_fix(vulnerability, best_fix)
            vulnerability.validation_result = validation_result
            
            result['steps'].append({
                'step': 7,
                'name': 'Fix Validation',
                'result': validation_result,
                'success': validation_result.get('all_passing', False)
            })
            
            # Resultado final
            if validation_result.get('all_passing', False):
                vulnerability.status = "RESOLVED"
                print(f"  ✅ Vulnerabilidad {vulnerability.id} RESUELTA")
            else:
                vulnerability.status = "VALIDATION_FAILED"
                print(f"  ⚠️ Validación fallida para {vulnerability.id}")
            
            result['end_time'] = datetime.now().isoformat()
            result['final_status'] = vulnerability.status
            result['selected_fix'] = best_fix
            
            self.results.append(result)
            
            # Guardar resultado en log
            self._save_result(result)
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error procesando {vulnerability.id}: {str(e)}")
            vulnerability.status = "ERROR"
            result['error'] = str(e)
            result['end_time'] = datetime.now().isoformat()
            return result
    
    async def _generate_poc(self, vulnerability: Vulnerability) -> Optional[Dict]:
        """Genera un Proof of Concept para la vulnerabilidad."""
        # Usar el primer proveedor para generar el PoC
        provider = self.providers[0]
        
        try:
            poc = await provider.generate_poc({
                'vulnerability': vulnerability.to_dict(),
                'code': vulnerability.code_snippet,
                'language': self._detect_language(vulnerability.code_snippet)
            })
            
            if poc and 'code' in poc:
                return {
                    'code': poc['code'],
                    'description': poc.get('description', 'PoC generado automáticamente'),
                    'generated_by': provider.__class__.__name__,
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"    Error generando PoC: {e}")
        
        return None
    
    def _assess_exploitability(self, vulnerability: Vulnerability, poc: Dict) -> float:
        """Evalúa la explotabilidad de la vulnerabilidad."""
        # Factores simples de evaluación
        factors = {
            'severity': {
                'CRITICAL': 1.0,
                'HIGH': 0.8,
                'MEDIUM': 0.5,
                'LOW': 0.2
            }.get(vulnerability.severity, 0.5),
            
            'cwe_known': 1.0 if vulnerability.cwe else 0.7,
            'poc_exists': 1.0 if poc else 0.5
        }
        
        # Promedio ponderado
        score = sum(factors.values()) / len(factors) * 100
        return round(score, 2)
    
    async def _validate_with_council(self, vulnerability: Vulnerability, 
                                    poc: Dict, hypothesis: Dict) -> Dict:
        """Valida la vulnerabilidad con todos los miembros del consejo."""
        validation_tasks = []
        
        for provider in self.providers:
            task = provider.validate_vulnerability({
                'vulnerability': vulnerability.to_dict(),
                'poc': poc,
                'hypothesis': hypothesis,
                'code': vulnerability.code_snippet
            })
            validation_tasks.append(task)
        
        # Ejecutar validaciones en paralelo
        validation_results = await asyncio.gather(*validation_tasks, 
                                                 return_exceptions=True)
        
        # Procesar resultados
        validations = []
        valid_count = 0
        
        for i, result in enumerate(validation_results):
            provider_name = self.providers[i].__class__.__name__
            
            if isinstance(result, Exception):
                validations.append({
                    'provider': provider_name,
                    'valid': False,
                    'error': str(result)
                })
            elif result and result.get('valid', False):
                validations.append({
                    'provider': provider_name,
                    'valid': True,
                    'confidence': result.get('confidence', 0.5),
                    'notes': result.get('notes', '')
                })
                valid_count += 1
            else:
                validations.append({
                    'provider': provider_name,
                    'valid': False,
                    'notes': result.get('notes', 'Rechazado') if result else 'Sin respuesta'
                })
        
        return {
            'validations': validations,
            'total_agents': len(self.providers),
            'valid_count': valid_count,
            'unanimous': valid_count == len(self.providers),
            'consensus_percentage': (valid_count / len(self.providers)) * 100
        }
    
    async def _generate_fix_proposals(self, vulnerability: Vulnerability, 
                                     hypothesis: Dict) -> List[Dict]:
        """Genera múltiples propuestas de fix usando el consejo."""
        fix_tasks = []
        
        for provider in self.providers:
            task = provider.propose_fix({
                'vulnerability': vulnerability.to_dict(),
                'hypothesis': hypothesis,
                'code': vulnerability.code_snippet,
                'language': self._detect_language(vulnerability.code_snippet)
            })
            fix_tasks.append(task)
        
        # Ejecutar en paralelo
        proposals = await asyncio.gather(*fix_tasks, return_exceptions=True)
        
        # Filtrar resultados válidos
        valid_proposals = []
        
        for i, proposal in enumerate(proposals):
            provider_name = self.providers[i].__class__.__name__
            
            if isinstance(proposal, Exception):
                print(f"    ❌ Error con {provider_name}: {proposal}")
                continue
            
            if proposal and 'fixed_code' in proposal:
                valid_proposals.append({
                    'provider': provider_name,
                    'proposal': proposal,
                    'original_code': vulnerability.code_snippet,
                    'submitted_at': datetime.now().isoformat()
                })
        
        return valid_proposals
    
    async def _select_best_fix(self, vulnerability: Vulnerability, 
                              proposals: List[Dict]) -> Optional[Dict]:
        """Selecciona el mejor fix usando el motor de scoring."""
        if not proposals:
            return None
        
        scored_proposals = []
        
        for proposal in proposals:
            original_code = proposal['original_code']
            fixed_code = proposal['proposal']['fixed_code']
            language = self._detect_language(original_code)
            
            # Calcular puntuación
            score_result = self.scorer.score_fix(original_code, fixed_code, language)
            
            scored_proposal = {
                **proposal,
                'score': score_result,
                'total_score': score_result['total_score']
            }
            
            scored_proposals.append(scored_proposal)
        
        # Ordenar por puntuación total
        scored_proposals.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Verificar si la mejor propuesta supera el umbral
        best_proposal = scored_proposals[0]
        threshold = self.config['acceptance_threshold']
        
        if best_proposal['total_score'] >= threshold:
            best_proposal['selected_reason'] = f"Mejor puntuación ({best_proposal['total_score']} >= {threshold})"
            return best_proposal
        else:
            print(f"    ⚠️ Mejor propuesta no supera umbral: {best_proposal['total_score']} < {threshold}")
            
            # Buscar la mejor que supere el umbral
            for proposal in scored_proposals:
                if proposal['total_score'] >= threshold:
                    proposal['selected_reason'] = f"Primera propuesta que supera umbral ({proposal['total_score']} >= {threshold})"
                    return proposal
            
            # Si ninguna supera el umbral, devolver la mejor de todos modos con advertencia
            best_proposal['selected_reason'] = f"Ninguna supera umbral. Mejor disponible: {best_proposal['total_score']}"
            best_proposal['warning'] = "Puntuación por debajo del umbral de aceptación"
            return best_proposal
    
    async def _validate_fix(self, vulnerability: Vulnerability, 
                           selected_fix: Dict) -> Dict:
        """Valida que el fix seleccionado funcione correctamente."""
        # Por ahora, simular validación
        # TODO: Implementar ejecución real de tests
        
        return {
            'validated_at': datetime.now().isoformat(),
            'fix_applied': True,
            'tests_run': 0,  # TODO: Implementar
            'tests_passed': 0,
            'tests_failed': 0,
            'all_passing': True,  # Asumir éxito por ahora
            'notes': 'Validación simulada - implementar ejecución real de tests'
        }
    
    def _detect_language(self, code_snippet: str) -> str:
        """Detecta el lenguaje de programación del snippet."""
        # Detección simple basada en patrones
        if 'def ' in code_snippet and ':' in code_snippet and not ';' in code_snippet:
            return 'python'
        elif '#include' in code_snippet or 'printf(' in code_snippet:
            return 'c'
        elif 'std::' in code_snippet or 'cout ' in code_snippet:
            return 'cpp'
        elif 'function ' in code_snippet and '{' in code_snippet:
            return 'javascript'
        else:
            return 'unknown'
    
    async def _simulate_sast_scan(self, workspace_path: str) -> List[Vulnerability]:
        """Simula un escaneo SAST (para desarrollo)."""
        # Vulnerabilidades de ejemplo
        return [
            Vulnerability(
                vuln_id="VULN-001",
                description="Buffer overflow in strcpy",
                severity="CRITICAL",
                location="src/main.c:42",
                code_snippet="""
#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // CWE-120: Buffer overflow
    printf("%s\n", buffer);
}
""",
                cwe="CWE-120"
            ),
            Vulnerability(
                vuln_id="VULN-002",
                description="SQL injection vulnerability",
                severity="HIGH",
                location="src/database.py:15",
                code_snippet="""
def get_user_data(username):
    import sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    
    return cursor.fetchall()
""",
                cwe="CWE-89"
            )
        ]
    
    def _save_result(self, result: Dict):
        """Guarda el resultado del procesamiento en un archivo de log."""
        session_id = self.current_session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tdh_logs/result_{session_id}_{result['vulnerability']['id']}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"    📄 Resultado guardado en: {filename}")


# Función principal de ejemplo
async def main():
    """Función principal de ejemplo para demostrar el uso del engine."""
    print("=" * 60)
    print("TDH ENGINE - Test Driven Hardening")
    print("Prototipo Python - Modo Local/Offline")
    print("=" * 60)
    
    # Crear instancia del engine
    engine = TDHEngine()
    
    # 1. Analizar repositorio (simulado)
    print("\n[Fase 1] Analizando repositorio...")
    vulnerabilities = await engine.analyze_repository("/ruta/simulada/repo")
    
    print(f"\nEncontradas {len(vulnerabilities)} vulnerabilidades:")
    for vuln in vulnerabilities:
        print(f"  • {vuln['id']}: {vuln['description']} ({vuln['severity']})")
    
    # 2. Procesar cada vulnerabilidad
    print("\n[Fase 2] Procesando vulnerabilidades con TDH...")
    
    for vuln_dict in vulnerabilities:
        # Convertir diccionario a objeto Vulnerability
        vuln = Vulnerability(
            vuln_dict['id'],
            vuln_dict['description'],
            vuln_dict['severity'],
            vuln_dict['location'],
            vuln_dict.get('code_snippet', ''),
            vuln_dict.get('cwe')
        )
        
        # Procesar con TDH
        result = await engine.process_vulnerability(vuln)
        
        # Mostrar resumen
        print(f"\n{'='*40}")
        print(f"RESULTADO: {vuln.id}")
        print(f"Estado final: {result.get('final_status', 'UNKNOWN')}")
        
        if 'selected_fix' in result:
            fix = result['selected_fix']
            print(f"Fix seleccionado: {fix['provider']}")
            print(f"Puntuación: {fix['score']['total_score']}/100")
            print(f"Razón: {fix.get('selected_reason', 'N/A')}")
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        elif 'warning' in result:
            print(f"⚠️  Advertencia: {result['warning']}")
        else:
            print("✅ Procesamiento completado")
    
    print("\n" + "=" * 60)
    print("TDH Engine - Proceso completado")
    print(f"Total resultados: {len(engine.results)}")
    print("=" * 60)


if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(main())