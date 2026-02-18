Aquí tienes una propuesta para `PROCESS_SPECIFICATION.md` adaptada al nuevo diseño con el orquestador determinista.

---

```markdown
# TDH Engine – Especificación del Proceso

## 1. Propósito

El proceso TDH (Test Driven Hardening) define cómo el motor analiza, reproduce y corrige automáticamente vulnerabilidades en código fuente, utilizando agentes de lenguaje (LLM) en un entorno estrictamente controlado. El objetivo es **producir un parche validado** (o un informe de falso positivo) sin intervención humana, garantizando la integridad del repositorio en cada paso.

El proceso se basa en tres fases consecutivas:

1. **Test Design** – Crear un test que reproduzca la vulnerabilidad.
2. **Fix Design** – Modificar el código para eliminar la vulnerabilidad sin romper funcionalidad existente.
3. **Documentation** – Generar una explicación del cambio y, opcionalmente, un mensaje de commit.

Cada fase es gestionada por el **orquestador (manager)** y ejecutada por el **agente (LLM)** mediante un protocolo de acciones estructuradas.

---

## 2. Actores y Responsabilidades

### Orquestador (Manager)
- Prepara el entorno (contenedor, worktree, contexto).
- Inicia la comunicación con el agente.
- Recibe solicitudes de acción en JSON.
- Ejecuta las acciones permitidas con wrappers controlados.
- Mantiene la máquina de estados transaccional (backup/rollback).
- Decide cuándo una fase ha terminado (éxito o fracaso).
- Genera logs y reportes.

### Agente (LLM SOTA)
- Recibe el contexto y el historial de la fase.
- Decide qué acción realizar a continuación.
- Devuelve una acción en JSON.
- No tiene acceso directo al sistema de archivos ni a la red.
- Su comportamiento está guiado por los **skills** imperecederos (definidos en `config/skills/`) y el feedback del orquestador.

---

## 3. Fases del Proceso

Cada fase sigue el mismo patrón de interacción, con objetivos específicos.

### 3.1. Fase de Test Design

**Objetivo**: Crear un programa de prueba (por ejemplo, un archivo `.c` con `main`) que, al compilarse y ejecutarse, reproduzca la vulnerabilidad (crash, salida inesperada, etc.) en el binario vulnerable original. El test debe ser **autocontenido** y usar el código vulnerable real (no una copia).

**Entradas**:
- Código fuente del archivo vulnerable.
- Análisis SAST detallado (línea, tipo de vulnerabilidad, mensaje de la herramienta).
- Skills de diseño de tests (ej. `test_design/SKILL.md`).

**Salida esperada**:
- Un archivo de test (por ejemplo, `test_vuln.c`) que, al compilarse y ejecutarse, provoque la vulnerabilidad.
- El test debe compilar sin errores (salvo los provocados por la vulnerabilidad) y fallar en ejecución.

**Criterio de éxito**:
- El orquestador compila el test y ejecuta el binario resultante.
- El binario termina con código de error distinto de cero o produce una salida que indique la vulnerabilidad (según lo definido en el skill).

**Máximo de intentos**: 3.

### 3.2. Fase de Fix Design

**Objetivo**: Modificar el código fuente original para eliminar la vulnerabilidad, de manera que el test diseñado en la fase anterior **ahora pase** (es decir, el binario ya no falle). Además, debe mantenerse la funcionalidad original (el código debe seguir compilando y, si existen tests de regresión, deben pasar).

**Entradas**:
- Código fuente original.
- Test diseñado (archivo de test).
- Análisis SAST.
- Skills de corrección (`fix_design/SKILL.md`).

**Salida esperada**:
- Versión modificada del archivo vulnerable original.
- (Opcional) Modificaciones en otros archivos si son necesarias para la corrección.

**Criterio de éxito**:
- El orquestador compila el código modificado junto con el test.
- El test se ejecuta y termina con éxito (código 0).
- (Opcional) Se ejecutan tests de regresión preexistentes si los hubiera.

**Máximo de intentos**: 3.

### 3.3. Fase de Documentación

**Objetivo**: Generar una explicación clara de la vulnerabilidad y la corrección, así como un mensaje de commit estándar.

**Entradas**:
- Código original y modificado (diff).
- Análisis SAST.
- Test diseñado.
- Skills de documentación (`documentation/SKILL.md`).

**Salida esperada**:
- Un archivo de texto (ej. `FIX_REPORT.md`) con:
  - Descripción de la vulnerabilidad.
  - Explicación de la corrección.
  - Instrucciones para verificar.
- Un mensaje de commit (ej. `commit_message.txt`).

**Criterio de éxito**:
- El orquestador valida que los archivos de documentación se hayan creado y tengan contenido no vacío.
- No hay ejecución de código en esta fase.

**Máximo de intentos**: 2.

---

## 4. Flujo de Trabajo Detallado

### 4.1. Inicio de una Tarea

1. El orquestador recibe una tarea (desde línea de comandos o API) con:
   - URL del repositorio.
   - Commit SHA o rama.
   - Ruta al archivo vulnerable.
   - Análisis SAST (salida completa de la herramienta).
2. Clona el repositorio en un directorio temporal.
3. Crea un contenedor Docker con la imagen base.
4. Crea un worktree (copia) dentro del contenedor en `/workspace`.
5. Carga los skills de los tres roles desde `config/skills/`.
6. Prepara el contexto inicial: skills + código vulnerable + análisis SAST completo.
7. Inicia la fase 1.

### 4.2. Bucle de Interacción por Fase

Para cada fase, se ejecuta el siguiente bucle hasta un máximo de intentos:

1. **Orquestador** envía al agente un mensaje que contiene:
   - Contexto persistente (si es el primer mensaje de la fase; en reintentos se puede omitir parte).
   - Historial de acciones de la fase (acciones previas y sus resultados).
   - Instrucción específica de la fase.
   - Recordatorio de las reglas (solo acciones JSON, no crear archivos innecesarios, etc.).
2. **Agente** responde con una acción JSON.
3. **Orquestador** valida la acción:
   - ¿Está en la lista de herramientas permitidas?
   - ¿Los parámetros son correctos?
   Si no, se rechaza y se pide una acción válida (esto cuenta como intento).
4. **Orquestador** ejecuta la acción:
   - Para `read_file` o `search`: devuelve el resultado.
   - Para `write_file`: antes de escribir, crea backup; después, si es una escritura que afecta al código o al test, se desencadena automáticamente una verificación (compilar y ejecutar el test si corresponde).
5. **Orquestador** evalúa el resultado:
   - Si la acción era `write_file` y la fase es test o fix, se ejecutan `compile` y `run_binary` (con el test correspondiente).
   - Si la compilación/ejecución falla, se restaura el backup (rollback) y se registra el fallo.
   - Si tiene éxito, se consolida el cambio (se elimina el backup) y se actualiza el estado.
6. **Orquestador** registra el resultado en el log y lo añade al historial.
7. **Orquestador** determina si la fase ha terminado:
   - **Éxito**: se ha alcanzado el objetivo de la fase (test falla en fase 1, test pasa en fase 2, documentación generada en fase 3).
   - **Fracaso**: se han agotado los intentos sin éxito.
8. Si la fase termina con éxito, se pasa a la siguiente fase. Si fracasa, se aborta toda la tarea y se marca como no reproducible.

### 4.3. Finalización

- Si todas las fases tienen éxito, el orquestador genera un reporte final que incluye:
  - El diff del fix.
  - El test diseñado.
  - La documentación.
  - El mensaje de commit.
- Se destruye el contenedor y el worktree.
- Se devuelve el resultado al invocador (p.ej., archivos en un directorio de salida).

---

## 5. Acciones Permitidas y Formato

### 5.1. Acciones

| Acción       | Parámetros                                                                 | Descripción                                                                 |
|--------------|----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `read_file`  | `path` (str)                                                               | Lee el contenido completo del archivo.                                      |
| `search`     | `pattern` (str), `path` (str, opcional)                                    | Busca el patrón en los archivos (grep).                                     |
| `write_file` | `path` (str), `content` (str)                                              | Escribe contenido en el archivo (crea backup automático).                   |
| `compile`    | `target` (str), `flags` (list, opcional), `files` (list, opcional)        | Compila el objetivo (ej. `test_vuln.c`) o todo el proyecto.                 |
| `run_binary` | `binary` (str), `args` (list, opcional), `stdin` (str, opcional)          | Ejecuta el binario y captura salida.                                        |
| `finish`     | `reason` (str)                                                             | Indica que el agente considera completada la fase.                          |

### 5.2. Formato de Respuesta del Agente

```json
{
  "action": "nombre",
  "parameters": {
    "param1": "valor1",
    ...
  }
}
```

### 5.3. Formato de Resultado del Orquestador (para el agente)

Después de cada acción, el orquestador devuelve un mensaje con:

```
Acción ejecutada: <acción>
Resultado:
  success: true/false
  stdout: <salida estándar>
  stderr: <salida de error>
  exit_code: <código de retorno>
  (opcional) files: <lista de archivos modificados>
```

Si la acción era `write_file` y se desencadenó una verificación, se incluye además el resultado de la compilación/ejecución.

---

## 6. Máquina de Estados y Transacciones

El estado del worktree se define por el conjunto de archivos en el directorio. Cada cambio exitoso produce un nuevo estado. Los cambios fallidos se revierten.

**Reglas**:
- Antes de cada `write_file`, se guarda una copia del archivo original en un directorio `.tdh_backup`.
- Después de la acción, si se requiere verificación (porque la fase lo exige), se ejecuta la compilación/test.
- Si la verificación falla, se restaura el archivo desde el backup y se elimina el backup.
- Si la verificación tiene éxito, se elimina el backup y el cambio se consolida.

**Estados posibles de una fase**:
- `in_progress`
- `succeeded`
- `failed` (tras agotar intentos)

---

## 7. Logging y Depuración

El orquestador escribe un archivo de log en el worktree con nombre `tdh_<timestamp>_<vuln_id>.log`. Contiene:

- Fecha/hora de cada evento.
- Contexto inicial (skills, código, análisis SAST).
- Cada mensaje enviado al agente (prompt completo).
- Cada respuesta del agente (JSON).
- Cada acción ejecutada (comando real, salida, código, duración).
- Resultados de verificaciones.
- Decisiones de cambio de fase.

Este log es crucial para entender el comportamiento del modelo y depurar fallos.

---

## 8. Criterios de Éxito Global

El proceso completo se considera exitoso si:

1. Se completa la fase de test con un test que falla (reproduce la vulnerabilidad).
2. Se completa la fase de fix con un cambio que hace pasar el test.
3. Se genera documentación y mensaje de commit.
4. Todos los pasos se realizan sin intervención humana.

Si alguna fase no se completa tras los intentos máximos, la tarea se marca como fallida y se genera un informe parcial.

---

## 9. Extensiones Futuras (Fase 2 y 3)

En versiones posteriores, el proceso podrá incluir:

- Múltiples agentes compitiendo en paralelo.
- Validación cruzada de tests y fixes.
- Integración con sistemas de CI/CD para envío de pull requests.
- Herramientas adicionales (análisis estático más profundo, fuzzing, etc.).

La base determinista actual permite añadir estas capacidades sin cambiar los fundamentos de seguridad y transaccionalidad.

```

Este documento define el proceso de manera clara y alineada con el nuevo diseño. ¿Quieres que modifique algo o añada más detalles?