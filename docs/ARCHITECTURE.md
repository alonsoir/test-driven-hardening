Claro, aquí tienes una propuesta para `ARCHITECTURE.md` alineada con el nuevo enfoque de **Deterministic Orchestrator**. Incluye los componentes, el flujo de trabajo, el protocolo de acciones y la máquina de estados transaccional.

---

```markdown
# TDH Engine – Arquitectura

## Visión General

El motor TDH (Test Driven Hardening) es un sistema para el análisis, reproducción y corrección automatizada de vulnerabilidades en código fuente, utilizando modelos de lenguaje (SOTA) en un entorno estrictamente controlado.  
El principio fundamental es: **el modelo propone, el orquestador ejecuta y garantiza la integridad del repositorio**.

El sistema se compone de:

- **Orquestador (Manager)**: proceso central que gestiona contenedores, worktrees, ejecuta comandos y mantiene el estado transaccional.
- **Agente (LLM SOTA)**: modelo de lenguaje que recibe contexto y genera acciones estructuradas en JSON.
- **Contenedor Aislado**: entorno efímero por agente, sin red, con recursos limitados.
- **Worktree Transaccional**: copia del repositorio sobre la que se aplican cambios con capacidad de rollback.
- **Conjunto Acotado de Herramientas**: únicamente las operaciones necesarias para leer, buscar, escribir, compilar y ejecutar.

---

## Componentes Principales

### 1. Orquestador (Manager)

Es el único componente con capacidad de ejecutar comandos en el sistema operativo y modificar el sistema de archivos. Sus responsabilidades:

- Clonar el repositorio objetivo.
- Crear un contenedor Docker por agente.
- Crear un worktree (copia aislada) dentro del contenedor.
- Inicializar el contexto para el agente (skills, archivo vulnerable, análisis SAST completo).
- Enviar el contexto al agente y recibir solicitudes de acción en JSON.
- Validar que la acción solicitada esté entre las permitidas.
- Ejecutar la acción con wrappers que capturen salida, código de retorno y duración.
- Antes de cualquier modificación, realizar un backup automático del archivo afectado.
- Después de la ejecución, evaluar el resultado:
  - Si la acción es de escritura, compilar y ejecutar el test (cuando corresponda).
  - Si el test falla, restaurar el backup (rollback) y notificar al agente.
  - Si tiene éxito, consolidar los cambios y continuar.
- Mantener un log detallado de toda la interacción.

### 2. Agente (LLM SOTA)

El agente es un modelo de lenguaje (por ejemplo, Claude, GPT-4, etc.) que se comunica exclusivamente mediante mensajes estructurados. No ejecuta código, no accede al sistema de archivos, no lanza subprocesos. Su función es:

- Recibir el contexto inicial (skills, archivo vulnerable, análisis SAST).
- Recibir resultados de acciones previas (éxito/fallo, salidas de compilación/ejecución).
- Decidir la siguiente acción a realizar.
- Devolver una solicitud de acción en formato JSON.

El agente no tiene "memoria" propia más allá de la conversación; el orquestador le recuerda el contexto en cada mensaje si es necesario.

### 3. Contenedor Aislado

Cada instancia de agente se ejecuta en un contenedor Docker con las siguientes características:

- **Imagen base**: Ubuntu 22.04 con las herramientas de compilación necesarias (g++, make, cmake, etc.).
- **Sin acceso a red** (`--network none`).
- **Límites de recursos**: CPU y RAM restringidos (configurables).
- **Montaje**: el worktree se monta como volumen, pero el contenedor no tiene acceso al sistema de archivos del host más allá de ese directorio.
- **Ciclo de vida**: el contenedor se crea al inicio de un análisis y se destruye al finalizar (éxito o fracaso).

### 4. Worktree Transaccional

El worktree es una copia del repositorio en un directorio temporal dentro del contenedor. El orquestador gestiona esta copia de manera transaccional:

- Antes de cualquier `write_file`, se guarda una copia del archivo original (backup).
- Si una acción falla (por ejemplo, el test no compila o no reproduce la vulnerabilidad), se restaura el backup.
- Si la acción tiene éxito, se mantiene el cambio y se actualiza el "estado base" para futuras acciones.
- El worktree se destruye junto con el contenedor al finalizar.

Este mecanismo garantiza que el repositorio nunca queda en un estado inconsistente.

### 5. Herramientas Permitidas

Inicialmente, solo se habilitan las siguientes cinco herramientas. Cada una tiene un wrapper que normaliza la salida a JSON.

| Herramienta    | Descripción                                                                 | Ejemplo de acción (JSON)                                                                 |
|----------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `read_file`    | Lee el contenido completo de un archivo.                                    | `{ "action": "read_file", "path": "src/vuln.c" }`                                       |
| `search`       | Busca un patrón (grep) en el repositorio.                                   | `{ "action": "search", "pattern": "strcpy", "path": "src" }`                            |
| `write_file`   | Escribe contenido en un archivo (crea backup automático).                   | `{ "action": "write_file", "path": "src/vuln.c", "content": "..." }`                    |
| `compile`      | Compila el proyecto o un archivo específico.                                | `{ "action": "compile", "target": "test_vuln", "flags": ["-g", "-o", "test_vuln"] }`    |
| `run_binary`   | Ejecuta un binario compilado, opcionalmente con argumentos y entrada.       | `{ "action": "run_binary", "binary": "./test_vuln", "args": ["arg1"], "stdin": "input" }` |

El orquestador valida que la acción esté en esta lista; cualquier otra es rechazada.

---

## Flujo de Trabajo Típico (Fase 1)

1. **Inicio**: El orquestador recibe una tarea (repositorio, archivo vulnerable, análisis SAST).
2. **Preparación**:
   - Clona el repositorio.
   - Crea contenedor y worktree.
   - Carga los skills del agente (`test_design`, `fix_design`, `documentation`) desde `config/skills/`.
   - Prepara el contexto inicial (archivo vulnerable + análisis SAST completo).
3. **Bucle de interacción** (hasta 3 intentos por fase):
   - Orquestador envía al agente: contexto + historial + solicitud de acción.
   - Agente responde con JSON de acción.
   - Orquestador valida, ejecuta y captura resultado.
   - Si la acción es `write_file`, se ejecutan automáticamente `compile` y `run_binary` para verificar el test (según la fase).
   - Si el test falla, se hace rollback y se registra el fallo.
   - Si el test pasa (o la fase lo requiere), se avanza a la siguiente fase o se finaliza.
4. **Finalización**:
   - Se genera un reporte con el resultado (fix exitoso, falso positivo, etc.).
   - Se destruye el contenedor y el worktree.

---

## Protocolo de Comunicación (Manager ↔ Agente)

La comunicación se realiza mediante mensajes de texto (completamente deterministas). Cada mensaje del manager incluye:

- **Contexto persistente**: skills, código vulnerable, análisis SAST (solo al inicio, o si se necesita refrescar).
- **Instrucción de la fase**: qué se espera lograr (ej. "Diseña un test que reproduzca la vulnerabilidad").
- **Resultado de la acción anterior** (si la hay): salida del comando, código de retorno, éxito/fallo.
- **Recordatorio de las reglas**: solo acciones JSON permitidas, no crear archivos fuera de lo necesario, etc.

La respuesta del agente debe ser un JSON válido con la siguiente estructura:

```json
{
  "action": "nombre_de_la_herramienta",
  "parameters": {
    "param1": "valor1",
    ...
  }
}
```

Si el agente desea finalizar (porque cree que ha completado la fase o no puede continuar), puede enviar:

```json
{
  "action": "finish",
  "reason": "Test successfully reproduces vulnerability"
}
```

---

## Máquina de Estados Transaccional

El estado del worktree se representa mediante un hash del contenido después de cada cambio exitoso. Cualquier fallo revierte al hash anterior.

```plaintext
Estado inicial (hash H0)
  │
  ├─ write_file (crea backup)
  │    │
  │    └─ compile / run
  │         │
  │         ├─ éxito → nuevo estado (hash H1)
  │         │
  │         └─ fallo → rollback (restaura backup) → permanece H0
  │
  └─ ...
```

Este enfoque asegura que nunca se acumulan cambios no verificados.

---

## Logging y Trazabilidad

El orquestador genera un archivo de log en el worktree (ej. `tdh_<vuln_id>.log`) que contiene:

- Contexto inicial completo.
- Cada mensaje enviado al agente (prompt).
- Cada respuesta del agente (JSON).
- Cada acción ejecutada, con comando real, salida, código de retorno y duración.
- Resultado de cada fase.

Estos logs son esenciales para depurar el comportamiento del modelo y mejorar los prompts.

---

## Resumen de Garantías

- **Determinismo**: el mismo input (repositorio + vulnerabilidad) produce el mismo flujo de acciones (salvo variaciones del modelo, pero el orquestador siempre actúa igual).
- **Seguridad**: el modelo nunca ejecuta comandos; el contenedor está aislado y sin red.
- **Integridad del repositorio**: cualquier cambio fallido se revierte automáticamente.
- **Trazabilidad**: cada decisión del modelo y cada comando ejecutado queda registrado.

---

## Próximos Pasos (Fase 1)

1. Implementar el orquestador con las cinco herramientas básicas.
2. Integrar la comunicación con el agente (OpenRouter o similar).
3. Probar con un caso conocido (ej. buffer overflow simple) hasta que el ciclo completo funcione sin intervención.
4. Refinar prompts y feedback en función de los logs.

Una vez estable, se abordarán fases posteriores (múltiples modelos, competición, etc.).
```

Este documento describe la arquitectura de manera autónoma y sirve como guía para desarrolladores. ¿Te parece adecuado o quieres modificar algún aspecto?