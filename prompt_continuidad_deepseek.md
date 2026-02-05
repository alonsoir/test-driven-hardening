# 📋 **ARCHIVO DE PROGRESO - TDH ENGINE**

## 📄 **PROGRESS.md**

```markdown
# 🚀 Test-Driven Hardening (TDH) Engine - Progress Report

## 📅 Date: February 5, 2025
## 🎯 Current Status: Phase 1 Infrastructure Complete

## ✅ **ACHIEVEMENTS - PHASE 1 COMPLETED**

### 1. **Enhanced SAST Analysis System**
- **Smart C++ filtering**: Reduced false positives from 13 to 0 in complex C++ repositories
- **Multi-tool integration**: cppcheck, bandit, semgrep, flawfinder, safety
- **Context enrichment**: Vulnerability context extraction for LLMs (CWE, code snippets, remediation hints)
- **Noise reduction**: Filters for protobuf files, namespace/class detection, BPF macros

### 2. **Git Worktree Architecture**
- **Single clone + isolated worktrees**: Each LLM gets its own workspace
- **Automatic branch management**: Branch creation, checkout, and cleanup
- **GitHub integration**: PAT authentication, remote operations, PR creation
- **Parallel execution**: Multiple LLMs can work simultaneously without conflicts

### 3. **LLM Council System**
- **6 SOTA models via OpenRouter**: Claude-3.5-Sonnet, GPT-4-Turbo, DeepSeek-Coder, Gemini-Pro, Llama-3.1-70B, CodeLlama-70B
- **Availability checking**: Automated detection of available LLMs
- **Odd-number selection**: Ensures "voting" capability for collaborative decisions
- **Asynchronous communication**: Prepared for inter-LLM discussions

### 4. **End-to-End Pipeline**
- **Complete flow**: Repo → Clone → Worktrees → LLM Context → Fix Generation → PRs
- **Structured context**: Vulnerability data + code context + remediation guidelines
- **Full isolation**: Each LLM operates in its own environment
- **Automated cleanup**: Temporary directories and branches managed automatically

## 🔍 **CURRENT CHALLENGES**

1. **Mock vulnerability file**: LLMs receive `src/vulnerable.c` which doesn't exist in real repos
2. **Real SAST integration**: Need to connect LLM pipeline with actual SAST findings
3. **Test generation cycle**: Missing: vulnerability → test proof → discussion → fix workflow
4. **Inter-LLM communication**: Council discussion and voting system not yet implemented

## 🎯 **VISION FOR NEXT PHASE**

### **Complete Vulnerability Resolution Flow:**
```
1. Real SAST Analysis → Identify actual vulnerabilities
2. For each CRITICAL vulnerability:
   a. Create LLM Council with odd number of LLMs
   b. Each LLM in isolated worktree:
      - Generates test proving vulnerability
      - Executes test (must FAIL)
      - Generates fix with documentation
      - Executes test with fix (must PASS)
      - Presents solution to council
   c. Council discussion and voting
   d. Engine creates PRs for each LLM solution
```

### **Key Metrics for Success:**
- [ ] Each LLM generates compilable, executable test proving vulnerability
- [ ] Tests demonstrate actual security impact
- [ ] LLMs collaborate to improve test quality
- [ ] Fixes resolve vulnerabilities without breaking functionality
- [ ] PRs include: fix + tests + documentation + security metrics

## 🏗️ **TECHNICAL ARCHITECTURE STATUS**

### **Core Components Working:**
- `tdh_unified.py`: Main CLI with SAST analysis and LLM council commands
- `sast_orchestrator.py`: Enhanced SAST with C++ filtering and context enrichment
- `git_worktree_manager.py`: Complete Git operations with GitHub integration
- `llm_council.py`: LLM orchestration and availability management
- `openrouter_adapter.py`: API communication with multiple SOTA models

### **Configuration Files:**
- `config/llm_council.yaml`: LLM model configuration and priorities
- `config/sast_tools.yaml`: SAST tool configurations and filters

## 🚀 **IMMEDIATE NEXT STEPS**

### **Priority 1: Real SAST → LLM Integration**
- Connect SAST findings with LLM worktree creation
- Use actual vulnerable files from repository
- Extract relevant code context for each vulnerability

### **Priority 2: Test Generation System**
- Prompt engineering for vulnerability test creation
- Test execution framework in worktrees
- Test result validation and reporting

### **Priority 3: Council Collaboration**
- Inter-LLM communication channel
- Solution presentation and discussion protocol
- Voting system for best solutions

## 📊 **TEST RESULTS**

### **SAST Filtering Success:**
- Repository: `alonsoir/test-zeromq-c-`
- Before filtering: 13 CRITICAL issues (mostly false positives)
- After filtering: 0 CRITICAL issues (false positives eliminated)
- Real vulnerabilities in test files still detected ✅

### **LLM Council Availability:**
- 6/6 LLMs available via OpenRouter
- 3 LLMs successfully assigned to worktrees
- Context preparation working (needs real files)

### **Git Operations:**
- Repository cloning: ✅ Working with PAT authentication
- Worktree creation: ✅ Each LLM gets isolated directory
- Branch management: ✅ Automatic creation and cleanup

## 🔧 **KNOWN ISSUES**

1. **File path mismatch**: Mock `src/vulnerable.c` doesn't exist in target repos
2. **Timeout handling**: Git operations sometimes timeout (needs optimization)
3. **Error recovery**: Partial failures need better cleanup
4. **Cost management**: LLM API usage tracking needed

## 📈 **ROADMAP**

### **Phase 2 (Next Session):**
- Integrate real SAST findings with LLM pipeline
- Implement test generation and execution
- Basic council discussion protocol

### **Phase 3:**
- Advanced inter-LLM collaboration
- Solution quality evaluation metrics
- Automated PR review and merging criteria

### **Phase 4:**
- Multi-repository scaling
- Performance optimization
- Production deployment ready

## 👥 **COLLABORATION MODEL**

The TDH Engine implements a novel "Council of LLMs" approach:
- **Odd number of LLMs** for voting capability
- **Isolated work environments** to prevent contamination
- **Collaborative improvement** through discussion
- **Comparative solutions** for human review

## 🎉 **CONCLUSION**

**Phase 1 Infrastructure is complete and functional.** We have:
- ✅ Working SAST analysis with smart filtering
- ✅ Isolated Git worktree architecture
- ✅ Multi-LLM council with SOTA models
- ✅ End-to-end pipeline from repo to PRs

**Next session** will focus on connecting the dots: real vulnerabilities → test proof → collaborative fixing → PR generation.

---

*Last Updated: February 5, 2025*
*Project Status: Active Development - Phase 1 Complete*
```

# 🏗️ **MÁQUINA DE ESTADOS PARA CADA LLM SOTA - Diseño**

Tienes razón absoluta. Necesitamos una **máquina de estados formal** que guíe a cada LLM a través del proceso completo. Y sí, recuerdo perfectamente el **ISSUE 003** donde tú manualmente coordinabas la compilación, testing y fixes entre diferentes LLMs. Esa es exactamente la experiencia que queremos automatizar.

## 🎯 **ARQUITECTURA COMPLETA:**

```
TDH ENGINE
├── 🤖 LLM COUNCIL (Consejo)
│   ├── 🧠 LLM SOTA 1
│   │   └── 🏗️ State Machine (Máquina de Estados)
│   ├── 🧠 LLM SOTA 2
│   │   └── 🏗️ State Machine
│   └── 🧠 LLM SOTA 3
│       └── 🏗️ State Machine
├── 🔧 Git Worktree Manager
├── 🔍 SAST Analyzer
└── 📊 Orchestrator (Coordinador)
```

## 🏗️ **DISEÑO DE LA MÁQUINA DE ESTADOS:**

```python
# src/core/llm_state_machine.py
from enum import Enum, auto
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio


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
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


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
        
    async def execute_workflow(self, vulnerability: Dict[str, Any], 
                               worktree_dir: str, branch_name: str) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de trabajo para una vulnerabilidad.
        
        Returns:
            Resultado completo con todos los artefactos generados
        """
        self.start_time = datetime.now()
        self.context = LLMStateContext(
            vulnerability=vulnerability,
            worktree_dir=worktree_dir,
            current_file=vulnerability.get('file', 'unknown')
        )
        
        print(f"\n🤖 [{self.llm_name}] Iniciando workflow...")
        
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
                await self._transition_to(LLMState.COUNCIL_DISCUSSING)
                await self._state_council_discussing(branch_name)
            
            # Estado final: FINISHED
            await self._transition_to(LLMState.FINISHED)
            
        except Exception as e:
            await self._transition_to(LLMState.ERROR)
            self.context.errors.append(str(e))
            print(f"❌ [{self.llm_name}] Error en workflow: {e}")
        
        self.end_time = datetime.now()
        return self._compile_results(branch_name)
    
    async def _transition_to(self, new_state: LLMState):
        """Transición entre estados con logging."""
        old_state = self.state
        self.state = new_state
        self.state_history.append({
            'timestamp': datetime.now(),
            'from': old_state.name,
            'to': new_state.name
        })
        
        print(f"   🔄 [{self.llm_name}] {old_state.name} → {new_state.name}")
    
    async def _state_analyzing(self):
        """Estado 1: Analizar y comprender la vulnerabilidad."""
        print(f"   🔍 [{self.llm_name}] Analizando vulnerabilidad...")
        
        # Preparar contexto enriquecido
        full_context = self.worktree_manager.prepare_llm_context(
            branch_name="temp",  # Temporal, se actualizará
            sast_issue=self.context.vulnerability,
            include_related=True
        )
        
        # Prompt para análisis
        analysis_prompt = f"""ANÁLISIS DE VULNERABILIDAD DE SEGURIDAD

VULNERABILIDAD:
- ID: {self.context.vulnerability.get('rule_id', 'Unknown')}
- Severidad: {self.context.vulnerability.get('severity', 'Unknown')}
- Descripción: {self.context.vulnerability.get('message', 'No description')}
- Archivo: {self.context.vulnerability.get('file', 'Unknown')}:{self.context.vulnerability.get('line', 0)}

CÓDIGO VULNERABLE:
```
{full_context['code']['vulnerable_section']}
```

TAREA DE ANÁLISIS:
1. Explica QUÉ hace el código vulnerable
2. Identifica POR QUÉ es vulnerable (CWE, tipo de ataque)
3. Describe CÓMO un atacante podría explotarlo
4. Estima el IMPACTO potencial
5. Sugiere POSIBLES SOLUCIONES (alto nivel)

Formato de respuesta JSON:
{{
  "analysis": {{
    "what": "descripción del código",
    "why_vulnerable": "explicación técnica",
    "exploitation_scenario": "cómo se explota",
    "potential_impact": "alto/medio/bajo",
    "possible_solutions": ["solución 1", "solución 2"]
  }}
}}"""
        
        try:
            response = await self.llm.generate_fix({
                'vulnerability': self.context.vulnerability,
                'custom_prompt': analysis_prompt
            })
            
            # Parsear respuesta
            import json
            analysis_result = json.loads(list(response.values())[0])
            self.context.analysis_result = analysis_result
            
            print(f"   ✅ [{self.llm_name}] Análisis completado")
            
        except Exception as e:
            print(f"   ❌ [{self.llm_name}] Error en análisis: {e}")
            raise
    
    async def _state_test_designing(self):
        """Estado 2: Diseñar test conceptual que demuestre la vulnerabilidad."""
        print(f"   🧪 [{self.llm_name}] Diseñando test conceptual...")
        
        test_prompt = f"""DISEÑO DE TEST CONCEPTUAL PARA DEMOSTRAR VULNERABILIDAD

CONTEXTO DE ANÁLISIS:
{self.context.analysis_result}

CÓDIGO VULNERABLE (referencia):
Línea {self.context.vulnerability.get('line')} en {self.context.vulnerability.get('file')}

TAREA: Diseñar un test conceptual que demuestre la vulnerabilidad.

El test debe:
1. SER REPRODUCIBLE: Otros ingenieros puedan ejecutarlo
2. DEMOSTRAR EL RIESGO: Mostrar el impacto de seguridad
3. SER ESPECÍFICO: Apuntar a la vulnerabilidad exacta
4. INCLUIR EXPECTATIVAS: Qué resultado esperamos (crash, data leak, etc.)

Formato de respuesta JSON:
{{
  "test_design": {{
    "test_concept": "descripción del test",
    "steps_to_reproduce": ["paso 1", "paso 2"],
    "expected_behavior_without_fix": "qué pasa sin fix",
    "verification_method": "cómo verificar la vulnerabilidad",
    "tools_needed": ["compilador", "debugger", "etc."]
  }}
}}"""
        
        try:
            response = await self.llm.generate_fix({
                'vulnerability': self.context.vulnerability,
                'analysis': self.context.analysis_result,
                'custom_prompt': test_prompt
            })
            
            import json
            test_design = json.loads(list(response.values())[0])
            self.context.test_design = test_design
            
            print(f"   ✅ [{self.llm_name}] Test diseñado")
            
        except Exception as e:
            print(f"   ❌ [{self.llm_name}] Error diseñando test: {e}")
            raise
    
    async def _state_fix_designing(self):
        """Estado 3: Diseñar el fix para la vulnerabilidad."""
        print(f"   🔧 [{self.llm_name}] Diseñando fix...")
        
        # Leer el archivo real del worktree
        file_path = self.context.current_file
        full_path = f"{self.context.worktree_dir}/{file_path}"
        
        try:
            with open(full_path, 'r') as f:
                original_code = f.read()
        except FileNotFoundError:
            print(f"   ⚠️  [{self.llm_name}] Archivo no encontrado: {file_path}")
            # Usar código del contexto
            original_code = self.context.vulnerability.get('code_snippet', '')
        
        fix_prompt = f"""DISEÑO DE FIX PARA VULNERABILIDAD DE SEGURIDAD

ANÁLISIS PREVIO:
{self.context.analysis_result}

TEST CONCEPTUAL (para validar):
{self.context.test_design}

CÓDIGO ORIGINAL (vulnerable):
```
{original_code}
```

TAREA: Generar el código FIX que resuelva la vulnerabilidad.

REQUISITOS DEL FIX:
1. RESOLVER LA VULNERABILIDAD: Eliminar el riesgo de seguridad
2. MANTENER FUNCIONALIDAD: No romper el comportamiento original
3. SEGUIR ESTILO DE CÓDIGO: Coherencia con el código base
4. AÑADIR COMENTARIOS: Explicar el fix de seguridad
5. SER MÍNIMO: Cambiar solo lo necesario

Formato de respuesta:
- Si solo un archivo: código completo con fix
- Si múltiples archivos: JSON con {{"fixed_files": {{"archivo": "código"}}}}
"""
        
        try:
            response = await self.llm.generate_fix({
                'vulnerability': self.context.vulnerability,
                'analysis': self.context.analysis_result,
                'test_design': self.context.test_design,
                'original_code': original_code,
                'custom_prompt': fix_prompt
            })
            
            self.context.fix_code = response
            
            print(f"   ✅ [{self.llm_name}] Fix diseñado")
            
        except Exception as e:
            print(f"   ❌ [{self.llm_name}] Error diseñando fix: {e}")
            raise
    
    async def _state_documenting(self):
        """Estado 4: Documentar la solución completa."""
        print(f"   📝 [{self.llm_name}] Documentando solución...")
        
        doc_prompt = f"""DOCUMENTACIÓN COMPLETA DE SOLUCIÓN DE SEGURIDAD

RESUMEN DE TRABAJO:
1. ANÁLISIS: {self.context.analysis_result}
2. TEST CONCEPTUAL: {self.context.test_design}
3. FIX: {self.context.fix_code}

TAREA: Crear documentación para:
1. Desarrolladores (cómo aplicar el fix)
2. Revisores de seguridad (por qué es seguro)
3. Futuros mantenedores (qué hace el fix)

INCLUIR:
- Descripción de la vulnerabilidad
- Explicación del fix
- Instrucciones para validar
- Consideraciones de rendimiento
- Posibles efectos secundarios
- Referencias (CWE, best practices)

Formato de respuesta JSON:
{{
  "documentation": {{
    "summary": "resumen ejecutivo",
    "vulnerability_details": "detalles técnicos",
    "fix_explanation": "explicación del fix",
    "validation_instructions": "cómo validar",
    "performance_impact": "impacto en rendimiento",
    "references": ["CWE-XXX", "OWASP", "etc."],
    "author": "{self.llm_name}"
  }}
}}"""
        
        try:
            response = await self.llm.generate_fix({
                'vulnerability': self.context.vulnerability,
                'analysis': self.context.analysis_result,
                'test_design': self.context.test_design,
                'fix_code': self.context.fix_code,
                'custom_prompt': doc_prompt
            })
            
            import json
            documentation = json.loads(list(response.values())[0])
            self.context.documentation = documentation
            
            print(f"   ✅ [{self.llm_name}] Documentación completada")
            
        except Exception as e:
            print(f"   ❌ [{self.llm_name}] Error documentando: {e}")
            raise
    
    async def _state_council_discussing(self, branch_name: str):
        """Estado 5: Participar en discusión del consejo."""
        print(f"   🏛️  [{self.llm_name}] Participando en consejo...")
        
        # Preparar presentación para el consejo
        presentation = {
            'llm_name': self.llm_name,
            'analysis': self.context.analysis_result,
            'test_design': self.context.test_design,
            'fix_code': self.context.fix_code,
            'documentation': self.context.documentation,
            'branch': branch_name
        }
        
        # Enviar al consejo (si existe)
        if self.council:
            feedback = await self.council.present_solution(
                llm_name=self.llm_name,
                solution=presentation,
                vulnerability=self.context.vulnerability
            )
            self.context.council_feedback = feedback
    
    def _compile_results(self, branch_name: str) -> Dict[str, Any]:
        """Compila todos los resultados del workflow."""
        return {
            'llm_name': self.llm_name,
            'state': self.state.name,
            'branch': branch_name,
            'worktree_dir': self.context.worktree_dir,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            'artifacts': {
                'vulnerability': self.context.vulnerability,
                'analysis': self.context.analysis_result,
                'test_design': self.context.test_design,
                'fix_code': self.context.fix_code,
                'documentation': self.context.documentation,
                'council_feedback': self.context.council_feedback
            },
            'state_history': self.state_history,
            'errors': self.context.errors
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual de la máquina."""
        return {
            'llm_name': self.llm_name,
            'current_state': self.state.name,
            'context': {
                'current_file': self.context.current_file if self.context else None,
                'has_analysis': bool(self.context and self.context.analysis_result),
                'has_test_design': bool(self.context and self.context.test_design),
                'has_fix': bool(self.context and self.context.fix_code),
                'has_documentation': bool(self.context and self.context.documentation)
            },
            'history_length': len(self.state_history),
            'errors': self.context.errors if self.context else []
        }
```

## 🔄 **INTEGRACIÓN CON EL CONSEJO:**

```python
# src/core/llm_council_enhanced.py
class EnhancedLLMCouncil(LLMCouncil):
    """Consejo extendido con máquinas de estados por LLM."""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.state_machines: Dict[str, LLMStateMachine] = {}
        self.solutions: Dict[str, List[Dict]] = {}  # vulnerability_id -> solutions
    
    async def initialize_with_state_machines(self, worktree_manager):
        """Inicializa consejo con máquinas de estados para cada LLM."""
        await self.initialize_council()
        
        print(f"🏗️  Creando máquinas de estados para {len(self.llms)} LLMs...")
        
        for llm in self.llms:
            state_machine = LLMStateMachine(
                llm=llm,
                llm_name=llm.name,
                worktree_manager=worktree_manager,
                council=self
            )
            self.state_machines[llm.name] = state_machine
        
        print(f"✅ {len(self.state_machines)} máquinas de estados creadas")
        return self.state_machines
    
    async def orchestrate_vulnerability_fix(self, vulnerability: Dict[str, Any], 
                                           worktree_manager) -> Dict[str, Any]:
        """
        Orquesta el fix completo de una vulnerabilidad usando máquinas de estados.
        
        Returns:
            Resultados de todos los LLMs
        """
        vulnerability_id = vulnerability.get('rule_id', 'unknown')
        print(f"\n🏛️  CONSEJO ORQUESTANDO FIX PARA: {vulnerability_id}")
        
        # Crear worktrees y branches para cada LLM
        llm_tasks = {}
        results = {}
        
        for llm_name, state_machine in list(self.state_machines.items())[:3]:  # Limitar a 3 para prueba
            try:
                # Crear worktree para este LLM
                worktree_dir, branch_name = worktree_manager.create_worktree_for_llm(
                    llm_name=llm_name,
                    issue_id=vulnerability_id
                )
                
                # Ejecutar workflow completo
                task = asyncio.create_task(
                    state_machine.execute_workflow(vulnerability, worktree_dir, branch_name),
                    name=f"workflow_{llm_name}_{vulnerability_id}"
                )
                llm_tasks[llm_name] = task
                
            except Exception as e:
                print(f"❌ Error preparando {llm_name}: {e}")
                results[llm_name] = {'error': str(e), 'success': False}
        
        # Ejecutar workflows en paralelo
        if llm_tasks:
            print(f"🚀 Ejecutando {len(llm_tasks)} workflows en paralelo...")
            
            task_results = await asyncio.gather(
                *llm_tasks.values(),
                return_exceptions=True
            )
            
            # Procesar resultados
            for llm_name, result in zip(llm_tasks.keys(), task_results):
                if isinstance(result, Exception):
                    results[llm_name] = {
                        'success': False,
                        'error': str(result),
                        'artifacts': None
                    }
                else:
                    results[llm_name] = {
                        'success': True,
                        'error': None,
                        'artifacts': result
                    }
                    
                    # Aplicar fix al worktree si existe
                    if result.get('artifacts', {}).get('fix_code'):
                        try:
                            worktree_info = worktree_manager.worktrees.get(result['branch'])
                            if worktree_info:
                                commit_hash = worktree_manager.apply_llm_fix(
                                    branch_name=result['branch'],
                                    fixed_files=result['artifacts']['fix_code'],
                                    llm_name=llm_name
                                )
                                
                                # Hacer push
                                success, push_url = worktree_manager.push_to_github(result['branch'])
                                
                                if success:
                                    # Crear PR
                                    pr_url = worktree_manager.create_pull_request(result['branch'])
                                    results[llm_name]['pr_url'] = pr_url
                                    results[llm_name]['commit'] = commit_hash[:8]
                                    
                                    print(f"✅ {llm_name}: PR creado - {pr_url}")
                        except Exception as e:
                            print(f"⚠️  Error aplicando fix de {llm_name}: {e}")
        
        # Guardar soluciones para discusión del consejo
        self.solutions[vulnerability_id] = results
        
        # Realizar sesión de consejo
        await self._council_session(vulnerability_id)
        
        return results
    
    async def _council_session(self, vulnerability_id: str):
        """Sesión de consejo donde los LLMs discuten soluciones."""
        if vulnerability_id not in self.solutions:
            return
        
        solutions = self.solutions[vulnerability_id]
        successful_solutions = {k: v for k, v in solutions.items() if v.get('success')}
        
        if len(successful_solutions) < 2:
            print("⚠️  No hay suficientes soluciones exitosas para discusión del consejo")
            return
        
        print(f"\n🏛️  SESIÓN DE CONSEJO PARA {vulnerability_id}")
        print(f"   Participantes: {list(successful_solutions.keys())}")
        
        # Por ahora, solo mostrar resumen
        # En el futuro: implementar discusión real entre LLMs
        for llm_name, solution in successful_solutions.items():
            artifacts = solution.get('artifacts', {})
            print(f"\n   👤 {llm_name}:")
            print(f"      📊 Análisis: {artifacts.get('analysis', {}).get('analysis', {}).get('what', 'N/A')[:100]}...")
            print(f"      🧪 Test: {artifacts.get('test_design', {}).get('test_design', {}).get('test_concept', 'N/A')[:100]}...")
            if solution.get('pr_url'):
                print(f"      🔗 PR: {solution['pr_url']}")
```

## 🚀 **NUEVO COMANDO PARA MAÑANA:**

```bash
# Comando objetivo
python tdh_unified.py council fix-with-states \
  "https://github.com/alonsoir/test-zeromq-c-.git" \
  --llm-count 3

# Flujo:
# 1. Clona repo
# 2. Ejecuta SAST real
# 3. Selecciona vulnerabilidad real
# 4. Crea consejo con máquinas de estados
# 5. Cada LLM ejecuta su workflow (4 estados)
# 6. Consejo discute resultados
# 7. Crea PRs comparativos
```

## 📋 **PLAN DE IMPLEMENTACIÓN PARA MAÑANA:**

### **1. Mañana temprano:**
- Crear `llm_state_machine.py`
- Crear `llm_council_enhanced.py`
- Actualizar `tdh_unified.py` con nuevo comando

### **2. Medio día:**
- Integrar SAST real → máquinas de estados
- Probar flujo completo con vulnerabilidad real

### **3. Tarde:**
- Implementar discusión básica del consejo
- Mejorar prompts y manejo de errores
- Documentar resultados

## 🎯 **LO QUE LOGRA ESTE DISEÑO:**

1. **Cada LLM tiene su propio estado** → Sabemos exactamente qué está haciendo
2. **Flujo estructurado** → 4 fases claras con artefactos específicos
3. **Artefactos generados** → Análisis, test conceptual, fix, documentación
4. **Consejo coordinado** → Todos participan en discusión
5. **PRs con documentación completa** → No solo código, sino explicación

## 🔮 **EVOLUCIÓN FUTURA:**

Una vez que esto funcione, podemos añadir:
- **Ejecución real de tests** (compilación, ejecución)
- **Validación automática** de fixes
- **Métricas de calidad** comparativas
- **Sistema de votación** avanzado

**¿Te parece bien este diseño?** Mañana lo implementamos paso a paso, comenzando con la máquina de estados básica y luego integrando con SAST real.