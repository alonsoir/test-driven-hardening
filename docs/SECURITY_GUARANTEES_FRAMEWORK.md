# TDH Engine – Security Guarantees Framework

## 1. Introducción

El motor TDH opera en entornos potencialmente hostiles (código fuente con vulnerabilidades reales) y utiliza agentes de lenguaje que podrían, inadvertidamente, generar cambios dañinos o intentar escapar del entorno. Por ello, el sistema está diseñado con múltiples capas de seguridad que garantizan:

- **Aislamiento completo** del proceso de análisis.
- **Control absoluto** de las acciones ejecutadas.
- **Reversibilidad** de cualquier modificación.
- **Trazabilidad** de cada decisión y comando.
- **No persistencia** de efectos laterales.

Este documento describe el modelo de amenazas, las medidas implementadas y las garantías resultantes.

---

## 2. Modelo de Amenazas

Consideramos los siguientes riesgos (ordenados de mayor a menor probabilidad/impacto):

| Amenaza | Descripción | Impacto potencial |
|---------|-------------|-------------------|
| **A1 – Ejecución de comandos maliciosos** | El agente podría intentar ejecutar comandos del sistema (ej. `rm -rf`, descargas, etc.) para dañar el host o exfiltrar datos. | Destrucción del entorno, fuga de información. |
| **A2 – Modificaciones no autorizadas** | El agente podría modificar archivos fuera del repositorio o alterar el código de forma irreversible sin test previo. | Corrupción del repositorio, introducción de nuevas vulnerabilidades. |
| **A3 – Escapamiento del contenedor** | El agente podría explotar alguna vulnerabilidad en Docker o en las herramientas para acceder al host. | Compromiso total del sistema anfitrión. |
| **A4 – Denegación de servicio** | El agente podría lanzar procesos que consuman todos los recursos (fork bombs, bucles infinitos). | Inutilización del contenedor, afectación a otros procesos del host. |
| **A5 – Fuga de información sensible** | El agente podría leer archivos sensibles del repositorio (claves, credenciales) y mostrarlos en logs o intentar enviarlos. | Exposición de secretos. |
| **A6 – Persistencia de cambios no deseados** | Si un test falla, el cambio debería revertirse; si no, el repositorio queda en estado inconsistente. | Dificultad para depurar, resultados incorrectos. |

---

## 3. Capas de Defensa

### 3.1. Aislamiento por Contenedor

- Cada agente se ejecuta en un contenedor Docker **efímero**.
- **Red deshabilitada** (`--network none`), salvo que explícitamente se necesite (no es el caso en Fase 1).
- **Montaje de solo lectura** para el código base (el worktree es una copia, no el original).
- **Límites de recursos**: CPU y RAM estrictos, evitando DoS.
- El contenedor se destruye al finalizar la tarea, sin persistencia.

Esta capa mitiga A3 (escapamiento improbable por diseño de Docker), A4 (límites de recursos) y A5 (sin red, no hay exfiltración).

### 3.2. Ejecución Controlada por el Orquestador

- El agente **nunca ejecuta comandos**; solo propone acciones JSON.
- El orquestador valida que la acción esté en la lista de permitidas (whitelist).
- Las acciones están implementadas como wrappers que sanitizan parámetros (por ejemplo, `path` debe ser relativo al worktree y no contener `..`).
- Cualquier acción no permitida es rechazada y se registra.

Esto mitiga A1 (imposible ejecutar comandos arbitrarios) y A2 (solo se pueden modificar archivos dentro del worktree y mediante `write_file`).

### 3.3. Transaccionalidad con Backup/Rollback

- Antes de cada `write_file`, se guarda una copia del archivo original en un directorio oculto (`.tdh_backup`).
- Después de la escritura, si la fase requiere verificación (compilar/ejecutar), se ejecuta automáticamente.
- Si la verificación falla, se restaura el backup y se elimina el archivo modificado.
- Si tiene éxito, se consolida (se borra el backup).

Esto garantiza que **nunca** persista un cambio no verificado, incluso si el agente intenta escribir múltiples veces sin test (el orquestador siempre ejecuta la verificación correspondiente tras cada escritura). Mitiga A6.

### 3.4. Sanitización de Entradas y Salidas

- Los paths proporcionados por el agente se normalizan y se verifica que estén dentro del worktree.
- El contenido de los archivos se escribe tal cual, pero se limita el tamaño máximo para evitar relleno de disco.
- La salida de los comandos se captura y se trunca si es demasiado grande, evitando que el agente genere salidas desbordantes.

Esto previene ataques de path traversal y DoS por escritura masiva.

### 3.5. Logging Completo (sin secretos)

- Todos los eventos se registran en un archivo de log dentro del worktree.
- Los logs incluyen prompts, respuestas JSON, comandos ejecutados y sus salidas.
- **No se registran secretos** (se asume que el código fuente puede contenerlos; si existen, quedarían en el log, por lo que se recomienda no analizar repositorios con credenciales reales).
- El log se destruye con el contenedor, a menos que se exporte explícitamente.

Esto permite auditoría y depuración sin comprometer información adicional (el código ya es conocido).

### 3.6. Permisos Mínimos en el Contenedor

- El contenedor se ejecuta con un usuario no root (por ejemplo, `nobody`).
- Las herramientas de compilación están instaladas, pero no hay paquetes adicionales innecesarios.
- El sistema de archivos del contenedor es de solo lectura, excepto el worktree.

Esto limita el daño en caso de que el agente lograra ejecutar algo fuera de control.

---

## 4. Garantías Resultantes

| Garantía | Descripción |
|----------|-------------|
| **G1 – No ejecución de código arbitrario** | El agente nunca ejecuta comandos; solo el orquestador ejecuta acciones predefinidas. |
| **G2 – Aislamiento de red** | Sin conectividad, no hay exfiltración ni descarga de malware. |
| **G3 – Reversibilidad total** | Cualquier cambio que no supere las pruebas se deshace automáticamente. |
| **G4 – Integridad del repositorio original** | Se trabaja sobre una copia; el original nunca se modifica. |
| **G5 – Trazabilidad completa** | Cada paso está registrado y puede ser revisado. |
| **G6 – Límites de recursos** | No se puede consumir toda la CPU/memoria del host. |

---

## 5. Limitaciones y Riesgos Residuales

- **Vulnerabilidades en Docker**: aunque poco probables, si existiera un 0-day que permita escapar del contenedor, el host podría verse comprometido. Se recomienda ejecutar el orquestador en una máquina virtual o entorno aún más aislado.
- **Secretos en el código**: si el repositorio contiene contraseñas o claves, el agente podría leerlas y mostrarlas en las acciones (por ejemplo, pidiendo `read_file` de un archivo de configuración). El log las capturaría. Es responsabilidad del usuario no analizar repositorios con secretos reales, o bien utilizar herramientas de detección de secretos antes del análisis.
- **Errores en la lógica de verificación**: si el orquestador no detecta correctamente si un test ha fallado (por ejemplo, porque la vulnerabilidad se manifiesta de forma no estándar), podría dar por bueno un cambio incorrecto. Esto se mitiga con skills bien definidos y, en el futuro, con validación cruzada entre modelos.
- **Agente malicioso deliberado**: aunque improbable (los modelos comerciales tienen alineación), podría darse el caso de un modelo fine-tuneado para causar daño. Las capas de defensa (acciones limitadas, sin red, rollback) limitan el daño a modificaciones dentro del worktree que, además, deben pasar las pruebas. Un agente malicioso podría intentar escribir código que, al ejecutarse, dañe el sistema (por ejemplo, un `system("rm -rf /")` dentro del código compilado). Pero ese código se ejecutaría dentro del binario compilado, que corre en el mismo contenedor con privilegios limitados y sin red. El daño máximo sería borrar el worktree, pero el contenedor se destruye al final. Sigue siendo un riesgo, pero acotado.

---

## 6. Buenas Prácticas para el Usuario

- Ejecutar el orquestador en un entorno aislado (VM, contenedor privilegiado, etc.) por si ocurriera un escape.
- No analizar repositorios que contengan secretos reales; si es inevitable, usar un preprocesado que los elimine o ofusque.
- Revisar los logs después de cada ejecución para detectar comportamientos anómalos.
- Mantener Docker y el sistema actualizados.

---

## 7. Conclusión

El framework de garantías de seguridad de TDH proporciona un entorno robusto para la experimentación con agentes autónomos en código vulnerable, minimizando los riesgos operacionales. La combinación de aislamiento, control de ejecución, transaccionalidad y trazabilidad hace que el sistema sea adecuado para su uso en entornos de investigación y desarrollo, con la confianza de que ningún cambio no deseado persistirá y que cualquier intento de acción maliciosa será contenido.