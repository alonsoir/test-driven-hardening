# src/core/llm_state_machine.py
"""
Máquina de estados que guía a cada LLM SOTA a través del proceso completo
de análisis y resolución de vulnerabilidades.
"""

import json
from enum import Enum, auto
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import os


class LLMState(Enum):
    """Estados de la máquina de estados de un LLM"""
    IDLE = auto()              # Esperando trabajo
    ANALYZING = auto()         # Analizando vulnerabilidad
    TEST_DESIGNING = auto()    # Diseñando test conceptual
    FIX_DESIGNING = auto()     # Diseñando fix
    DOCUMENTING = auto()       # Documentando solución
    WAITING_COUNCIL = auto()   # Esperando discusión del consejo
    COUNCIL_DISCUSSING = auto() # Discutiendo en consejo
    FINISHED = auto()          # Trabajo completado
    ERROR = auto()             # Error en algún estado


@dataclass
class LLMStateContext:
    """Contexto que se mantiene a través de los estados"""
    vulnerability: Dict[str, Any]
    worktree_dir: str
    current_file: str
    analysis_result: Optional[Dict] = None
    test_design: Optional[Dict] = None
    fix_code: Optional[Dict] = None
    documentation: Optional[Dict] = None
    council_feedback: Optional[List] = None
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Añade un error al contexto"""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")


class LLMStateMachine:
    """
    Máquina de estados que guía a un LLM a través del proceso completo.
    
    Estados:
    1. ANALYZING → Comprender vulnerabilidad
    2. TEST_DESIGNING → Diseñar test que demuestre vulnerabilidad
    3. FIX_DESIGNING → Diseñar solución
    4. DOCUMENTING → Documentar solución
    5. COUNCIL_DISCUSSING → Participar en consejo
    6. FINISHED → Completado
    """
    
    def __init__(self, llm, llm_name: str, worktree_manager, council=None):
        self.llm = llm
        self.llm_name = llm_name
        self.worktree_manager = worktree_manager
        self.council = council
        
        self.state = LLMState.IDLE
        self.context: Optional[LLMStateContext] = None
        self.state_history = []
        self.start_time = None
        self.end_time = None
        self._current_task = None
        
    async def execute_workflow(self, vulnerability: Dict[str, Any], 
                               worktree_dir: str, branch_name: str) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de trabajo para una vulnerabilidad.
        
        Args:
            vulnerability: Dict con información de la vulnerabilidad del SAST
            worktree_dir: Directorio del worktree asignado
            branch_name: Nombre de la rama de trabajo
            
        Returns:
            Resultado completo con todos los artefactos generados
        """
        self.start_time = datetime.now()
        self.context = LLMStateContext(
            vulnerability=vulnerability,
            worktree_dir=worktree_dir,
            current_file=vulnerability.get('file', 'unknown')
        )
        
        print(f"\n🤖 [{self.llm_name}] Iniciando workflow en rama '{branch_name}'...")
        
        try:
            # Estado 1: ANALYZING
            await self._transition_to(LLMState.ANALYZING)
            await self._state_analyzing()
            
            # Estado 2: TEST_DESIGNING
            await self._transition_to(LLMState.TEST_DESIGNING)
            await self._state_test_designing()
            
            # Estado 3: FIX_DESIGNING
            await self._transition_to(LLMState.FIX_DESIGNING)
            await self._state_fix_designing()
            
            # Estado 4: DOCUMENTING
            await self._transition_to(LLMState.DOCUMENTING)
            await self._state_documenting()
            
            # Estado 5: COUNCIL_DISCUSSING (si hay consejo)
            if self.council:
                await self._transition_to(LLMState.WAITING_COUNCIL)
                await self._transition_to(LLMState.COUNCIL_DISCUSSING)
                await self._state_council_discussing(branch_name)
            
            # Estado final: FINISHED
            await self._transition_to(LLMState.FINISHED)
            
        except Exception as e:
            error_msg = f"Error en workflow: {str(e)}"
            print(f"❌ [{self.llm_name}] {error_msg}")
            self.context.add_error(error_msg)
            await self._transition_to(LLMState.ERROR)
        
        self.end_time = datetime.now()
        return self._compile_results(branch_name)
    
    async def _transition_to(self, new_state: LLMState):
        """Transición entre estados con logging."""
        old_state = self.state
        self.state = new_state
        self.state_history.append({
            'timestamp': datetime.now().isoformat(),
            'from': old_state.name,
            'to': new_state.name
        })
        
        print(f"   🔄 [{self.llm_name}] {old_state.name} → {new_state.name}")
    
    async def _state_analyzing(self):
        """Estado 1: Analizar y comprender la vulnerabilidad."""
        print(f"   🔍 [{self.llm_name}] Analizando vulnerabilidad...")
        
        try:
            # Preparar contexto enriquecido del worktree
            full_context = await self.worktree_manager.prepare_llm_context(
                issue_id=self.context.vulnerability.get('rule_id', 'unknown'),
                sast_issue=self.context.vulnerability,
                include_related=True
            )
            
            # Construir prompt de análisis
            analysis_prompt = self._build_analysis_prompt(full_context)
            
            # Llamar al LLM
            response = await self.llm.generate_response(
                prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parsear respuesta JSON
            try:
                analysis_result = json.loads(response)
                if isinstance(analysis_result, str):
                    # Algunos LLMs devuelven JSON como string dentro de string
                    analysis_result = json.loads(analysis_result)
            except:
                # Si no es JSON válido, crear estructura básica
                analysis_result = {
                    "analysis": {
                        "what": "Análisis no estructurado",
                        "why_vulnerable": "No se pudo parsear respuesta",
                        "exploitation_scenario": "N/A",
                        "potential_impact": "desconocido",
                        "possible_solutions": []
                    },
                    "raw_response": response[:500]
                }
            
            self.context.analysis_result = analysis_result
            print(f"   ✅ [{self.llm_name}] Análisis completado")
            
        except Exception as e:
            error_msg = f"Error en análisis: {str(e)}"
            self.context.add_error(error_msg)
            raise
    
    def _build_analysis_prompt(self, full_context: Dict) -> str:
        """Construye el prompt para análisis de vulnerabilidad."""
        vuln = self.context.vulnerability
        
        prompt = f"""# ANÁLISIS DE VULNERABILIDAD DE SEGURIDAD

## INFORMACIÓN DE LA VULNERABILIDAD:
- **ID**: {vuln.get('rule_id', 'Unknown')}
- **Severidad**: {vuln.get('severity', 'Unknown')}
- **Confianza**: {vuln.get('confidence', 'Unknown')}
- **Descripción**: {vuln.get('message', 'No description')}
- **Archivo**: {vuln.get('file', 'Unknown')}:{vuln.get('line', 0)}
- **CWE**: {vuln.get('cwe', 'N/A')}
- **OWASP**: {vuln.get('owasp', 'N/A')}

## CÓDIGO VULNERABLE:
```{self._get_file_extension(vuln.get('file', ''))}
{full_context.get('code', {}).get('vulnerable_section', '// No se pudo extraer código')}
```

## CONTEXTO ADICIONAL:
{full_context.get('code', {}).get('surrounding_code', '// No hay contexto adicional')}

## INSTRUCCIONES:
Analiza la vulnerabilidad reportada. Determina si es un falso positivo o un riesgo real.
Si es real, identifica exactamente por qué es vulnerable y cómo podría ser explotada.

Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
{{
    "analysis": {{
        "what": "Breve descripción de la vulnerabilidad",
        "why_vulnerable": "Explicación técnica de la debilidad",
        "exploitation_scenario": "Cómo un atacante podría aprovecharla",
        "potential_impact": "Impacto en el sistema",
        "possible_solutions": ["solución 1", "solución 2"]
    }},
    "is_false_positive": false,
    "confidence_score": 0.9
}}
"""
        return prompt

    def _get_file_extension(self, filename: str) -> str:
        """Obtiene la extensión del archivo para el bloque de código."""
        _, ext = os.path.splitext(filename)
        return ext.lstrip('.') if ext else ''

    async def _state_test_designing(self):
        """Estado 2: Diseñar un test que demuestre la vulnerabilidad."""
        print(f"   🧪 [{self.llm_name}] Diseñando test de concepto...")
        # Implementación pendiente
        pass

    async def _state_fix_designing(self):
        """Estado 3: Diseñar el fix para la vulnerabilidad."""
        print(f"   🛠️ [{self.llm_name}] Diseñando solución...")
        # Implementación pendiente
        pass

    async def _state_documenting(self):
        """Estado 4: Documentar la solución."""
        print(f"   📝 [{self.llm_name}] Documentando solución...")
        # Implementación pendiente
        pass

    async def _state_council_discussing(self, branch_name: str):
        """Estado 5: Participar en el consejo de sabios."""
        print(f"   🏛️ [{self.llm_name}] Participando en el consejo...")
        # Implementación pendiente
        pass

    def _compile_results(self, branch_name: str) -> Dict[str, Any]:
        """Compila todos los resultados del workflow."""
        return {
            "llm_name": self.llm_name,
            "branch": branch_name,
            "vulnerability": self.context.vulnerability,
            "analysis": self.context.analysis_result,
            "test_design": self.context.test_design,
            "fix": self.context.fix_code,
            "documentation": self.context.documentation,
            "errors": self.context.errors,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        }
