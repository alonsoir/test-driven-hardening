## 📋 Prompt de Continuidad – Día 2026-02-18

### 🧠 Contexto actual
Estamos desarrollando el motor **TDH (Test Driven Hardening)** con filosofía **OpenClaw**: cada modelo (agente SOTA) debe tener una personalidad definida por **skills imperecederos** (`test_design`, `fix_design`, `documentation`) y **contexto persistente** (análisis SAST, archivo vulnerable) durante toda su vida en el contenedor. La comunicación con el orquestador se realiza mediante logs detallados que permitan trazar cada decisión.

Hasta ahora:
- Tenemos definidos los skills en `config/skills/*/SKILL.md`.
- El agente `sota_agent.py` lee una tarea desde `stdin` y ejecuta las fases `test_designing`, `fix_designing`, `documenting`.
- El orquestador (`sast_orchestrator.py`) lanza contenedores, monta el worktree y pasa la tarea en `input.json`.
- En las ejecuciones recientes, la fase `test_designing` ha fallado tras 3 intentos con el estado `test_failed`.

### 🐞 Problema detectado
El fallo se debe a que, cuando un test no reproduce la vulnerabilidad, la retroalimentación que recibe el modelo es insuficiente:

```python
# Código actual en phase_test_design (simplificado)
prompt = f"Previous test failed to reproduce. Output:\n{output_log}\nTry again. Remember the format."
```

Esto provoca que el modelo **pierda el contexto original** (skills, archivo vulnerable, análisis SAST) y empiece a generar tests que crean nuevos archivos o se desvían de las instrucciones, como se observó en ejecuciones previas.

Además:
- El análisis SAST que se envía al modelo es solo un resumen (campos básicos), no la salida detallada de la herramienta que justifica por qué se marcó esa línea como vulnerable.
- Los logs actuales no capturan el contexto completo (prompts enviados, respuestas, comandos ejecutados), lo que dificulta la depuración.

### 🔍 Causa raíz
1. **Falta de persistencia del contexto**: cada llamada al modelo reconstruye el prompt desde cero, perdiendo las instrucciones imperecederas (skills) y la información del archivo/SAST.
2. **Retroalimentación pobre**: el modelo no recibe suficiente información sobre por qué falló su test anterior, ni se le recuerdan explícitamente las reglas (no crear archivos, usar el archivo real, estrategia para errores de sintaxis).
3. **Ausencia de análisis SAST detallado**: el modelo no sabe exactamente qué detectó la herramienta, solo un identificador y una línea.

### 🎯 Solución propuesta
Rediseñar `sota_agent.py` para que:

1. **Al iniciar el contenedor**, cargue de una vez:
   - Instrucciones generales (`tdh_agent_core.md`).
   - Skills específicos (`test_design/SKILL.md`, `fix_design/SKILL.md`, `documentation/SKILL.md`).
   - Contenido completo del archivo vulnerable.
   - Análisis SAST detallado (incluido en la tarea desde el orquestador).
2. **Mantenga este contexto en memoria** (variables globales o un objeto de contexto) durante todas las iteraciones (hasta 3 intentos por fase).
3. **En cada llamada al modelo**, use un prompt compuesto por:
   - El contexto persistente (skills + análisis + archivo).
   - La instrucción específica de la fase.
   - En caso de reintento, **feedback enriquecido** con:
     - Código del test anterior.
     - Comando ejecutado y su salida completa.
     - Código de retorno.
     - Recordatorio explícito de las reglas del skill.
4. **Registre todo** en un archivo de log dentro del worktree (ej. `tdh_agent_<vuln_id>.log`) que contenga:
   - Contexto completo cargado al inicio.
   - Prompts enviados en cada intento.
   - Respuestas del modelo.
   - Comandos ejecutados y sus salidas.
   - Resultado final (éxito/fallo).
5. **Modifique `call_openrouter`** para que ya no cargue skills (ahora se cargan una sola vez al inicio).

Además, en el orquestador (`sast_orchestrator.py`):
- Enriquecer el objeto `vulnerability` con el campo `sast_analysis` que contenga la salida completa de la herramienta que detectó el problema (por ejemplo, el mensaje de error de cppcheck o semgrep).
- Incluir este campo en el `input.json` que se pasa al agente.

### 📝 Tareas concretas para mañana

1. **Modificar `sota_agent.py`**:
   - En `main()`, cargar core y skills una sola vez.
   - Leer el archivo vulnerable y el análisis SAST de la tarea.
   - Crear un diccionario `context` con toda esta información.
   - Pasar `context` a las funciones de fase (`phase_test_design`, etc.).
   - En `phase_test_design`, construir el prompt base a partir del `context`.
   - En cada iteración, si falla, generar feedback detallado y añadirlo al prompt (sin perder el base).
   - Implementar logging persistente en archivo.

2. **Modificar `call_openrouter`**:
   - Eliminar las llamadas a `load_agent_core()` y `load_skill_instructions()`.
   - Aceptar el prompt ya completo.

3. **Modificar `sast_orchestrator.py`**:
   - En `_run_sast`, al crear `Vulnerability`, incluir en `additional_properties` el campo `tool_output` con la salida cruda de la herramienta (si está disponible en el resultado del pipeline SAST).
   - En `_generate_task_input`, añadir `"sast_analysis": task.vulnerability.additional_properties.get("tool_output", "")`.

4. **Probar** con el repositorio de prueba `https://github.com/alonsoir/test-zeromq-c-.git` y verificar que:
   - En el primer intento, el test usa el archivo real.
   - Si falla (porque no hay error real), el segundo intento recibe feedback completo y sigue usando el archivo real.
   - Los logs generados contienen toda la información necesaria.

5. **Evaluar** si tras 3 intentos fallidos podemos considerar la vulnerabilidad como posible falso positivo y marcarla en el reporte.

### ⚠️ Riesgos y consideraciones
- El prompt puede crecer mucho si se concatenan muchos intentos. Con un máximo de 3 intentos por fase, es aceptable. Si en el futuro se aumentan los intentos, habría que considerar un enfoque con historial de mensajes.
- Asegurarse de que el análisis SAST detallado no contenga información sensible (no debería, es código).
- Verificar que el logging no consuma demasiado espacio; los logs se borrarán al eliminar el worktree (al final de la orquestación o tras un tiempo).


```

Este es un analisis que he desarrollado con ChatGPT, yo creo que es el camino adecuado. Analizalo, dime que te parece y decidimos si seguir con el camino que tenemos descrito arriba o merece más la pena este camino:

# TDH Engine — Deterministic Orchestrator Action Plan

## Objective

Build a deterministic manager (orchestrator) that allows LLM SOTA agents to safely analyze, reproduce, and fix vulnerabilities inside isolated repositories without human interaction.

The manager is the only component allowed to execute commands. Models only propose actions.

---

## Core Principle

The system is not an autonomous coding agent.
It is a transactional experimentation runtime over source code.

Models propose.
Manager validates, executes, records, and reverts.

---

## Phase 1 — Deterministic Single‑Model Loop (Mandatory First Goal)

Goal: Fully automatic cycle using ONE model and ONE bug.
No multi‑model logic yet.

### Required Tools (only 5 initially)

1. read_file
2. search (grep-like)
3. write_file (with backup)
4. compile
5. run_binary

If this phase is not stable → stop development. Do not add features.

---

## System Components

### 1. Manager (Central Process)

Responsibilities:

* Clone repository
* Create container per agent
* Create worktree per agent
* Execute tools requested by model
* Maintain state machine
* Handle backups and rollback
* Run tests and compilation
* Provide structured results back to model
* Record experiment history

The manager is the only executor of shell commands.

Models never directly access the system.

---

### 2. Agent (LLM SOTA)

The agent produces structured action requests.
It never executes anything.

Example action request:
{
"action": "write_file",
"path": "src/parser.cpp",
"content": "...",
"backup": true
}

Manager validates → executes → returns structured result.

---

### 3. Container Environment

Each agent has:

* Dedicated container
* Dedicated worktree
* No network access
* CPU/RAM limits
* Execution timeout

Filesystem is never shared between agents.

---

## Transactional State Machine

Every attempt is a reversible transaction.

STATE_N
-> model proposes change
-> manager applies change (creates backup)
-> compile
-> run test
-> collect result
-> if failure: rollback
-> return to STATE_N

No corrupted state can persist.

---

## Required Manager Subsystems

### Workspace Controller

* Create worktrees
* Reset to clean state
* Snapshot revision hashes

### Backup Engine

* Automatic backup before modification
* Restore on failure
* Track modified files list

### Tool Executor

Allowed commands only through controlled wrappers:

* read_file
* search
* write_file
* compile
* run_binary

All outputs normalized to structured JSON.

### Result Interpreter

Convert raw execution into structured response:

* success/failure
* compiler errors
* runtime errors
* stdout/stderr
* exit code

### State Tracker

For each attempt store:

* diff
* result
* duration
* files touched
* reproducibility

---

## Model Interaction Protocol

Loop:

1. Manager sends context
2. Model returns action JSON
3. Manager executes
4. Manager returns structured result
5. Repeat

No natural language execution instructions allowed.
Only structured actions.

---

## Success Criteria (Phase 1 Complete)

The system automatically:

1. Reads code
2. Locates bug
3. Creates reproducible test
4. Compiles test
5. Test fails (bug proven)
6. Generates fix
7. Compiles fix
8. Test passes

Without human intervention.

---

## Phase 2 — Multi‑Model Competition (Future)

(Not to be implemented yet)

Manager responsibilities later:

* Share discovered tests
* Validate reproducibility
* Compare fixes
* Produce candidate pull requests

This stage only begins after Phase 1 is reliable.

---

## Non‑Goals (For Now)

* No parallel models
* No scoring systems
* No voting
* No ranking
* No advanced tools
* No internet access

Simplicity first. Determinism first.

---

## Immediate Next Tasks

1. Define action JSON schema
2. Implement manager execution loop
3. Implement file backup system
4. Implement compile/run wrappers
5. Run on one known C++ bug until stable

Only after stability → expand capabilities.

---

## Guiding Rule

If a human is needed during the loop, the system is not finished.
