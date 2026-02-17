📋 Prompt de Continuidad – Día 2026-02-18

✅ Resumen de lo que hemos avanzado

Contexto del problema: La ejecución del orquestador TDH muestra que los agentes SOTA fallan en la fase test_designing (test_failed) debido a una retroalimentación insuficiente cuando un test no reproduce la vulnerabilidad. El modelo pierde el contexto original (skills, archivo vulnerable, análisis SAST) y comienza a crear nuevos archivos o a desviarse, como se observó en ejecuciones anteriores.

Filosofía OpenClaw: Hemos definido que el comportamiento del modelo debe estar guiado por instrucciones imperecederas (skills) que se cargan una sola vez al inicio del contenedor y persisten durante toda la vida del agente (máximo 3 intentos). El contenedor debe comunicarse con el orquestador mediante logs detallados que capturen todo el contexto, prompts, respuestas y salidas de comandos.

Análisis de la situación actual:

En sota_agent.py, la función phase_test_design recarga el prompt base en cada intento, pero el prompt base no incluye el contexto completo (skills, análisis SAST) si no se le pasa explícitamente.
La función call_openrouter vuelve a cargar las skills y core instructions en cada llamada, lo que es ineficiente y propenso a errores.
El orquestador no proporciona un análisis SAST detallado en el input.json, solo un objeto vulnerability con campos mínimos.
Los logs actuales son insuficientes para trazar el comportamiento del agente.
Decisiones tomadas:
Contexto persistente en el contenedor: Al iniciar sota_agent.py, se cargarán:
tdh_agent_core.md (instrucciones generales).
Los skills específicos (test_design/SKILL.md, fix_design/SKILL.md, documentation/SKILL.md).
El contenido completo del archivo vulnerable.
El análisis SAST detallado (proporcionado por el orquestador).
Todo esto se almacenará en un objeto de contexto que se pasará a las fases.
Comunicación mediante logs: Cada contenedor generará un archivo de log (por ejemplo, tdh_agent_<vuln_id>.log) en el worktree, que contendrá:
El contexto completo al inicio.
Para cada intento: el prompt enviado al modelo, la respuesta completa, los comandos ejecutados y sus salidas.
Estos logs serán accesibles por el orquestador al finalizar la tarea.
Mejora del prompt de test_designing: El prompt base incluirá:
Core instructions + skill test_design.
El análisis SAST detallado.
La vulnerabilidad (con archivo, línea, descripción).
El contenido del archivo vulnerable.
Instrucciones claras sobre el formato [test] y [command] y la obligación de usar el archivo real.
Retroalimentación en caso de fallo: Cuando un test falla, se añadirá al prompt un bloque de feedback con:
El código de test usado.
El comando ejecutado y su salida completa (stdout/stderr).
El código de retorno.
Un recordatorio de las reglas del skill.
El prompt para el siguiente intento será: base_prompt + feedback (sin perder el contexto original).
🎯 Plan de acción para mañana (2026-02-18)

🔹 Fase 1 – Modificar sota_agent.py para contexto persistente
En main(), cargar:
core_instructions (load_agent_core)
skill_test, skill_fix, skill_doc (load_skill_instructions)
Leer file_content del archivo vulnerable (ruta absoluta)
Obtener sast_analysis del campo task.get("sast_analysis", "")
Crear un diccionario context con todo lo anterior + vulnerability, repo_path, api_key, model_config, max_iter.
Eliminar las llamadas a load_agent_core y load_skill_instructions dentro de call_openrouter (ahora el prompt ya las incluirá).
🔹 Fase 2 – Rediseñar phase_test_design
Construir base_prompt usando el contexto:

base_prompt = f"{context['core']}\n{context['skills']['test_design']}\n\n## Análisis SAST\n{context['sast_analysis']}\n\n## Vulnerabilidad\n{json.dumps(context['vulnerability'], indent=2)}\n\n## Archivo vulnerable\n**Ruta:** {context['vulnerability']['file']}\n**Contenido:**\n```cpp\n{context['file_content']}\n```\n\n## Instrucciones\nDebes generar un test que reproduzca la vulnerabilidad. Recuerda usar el archivo real y el formato [test] y [command].\n"

En cada intento, llamar a call_openrouter con prompt (que puede ser base_prompt o base_prompt + feedback).
Al fallar, construir feedback con los detalles del intento y asignar prompt = base_prompt + "\n\n" + feedback.
Asegurar que el feedback incluya un recordatorio explícito de no crear nuevos archivos.
🔹 Fase 3 – Mejorar el logging
En phase_test_design (y análogamente en fix_design), abrir un archivo de log en modo append (tdh_agent_<vuln_id>.log) en el directorio del worktree.
Escribir al inicio: contexto completo (skills, análisis SAST, contenido del archivo).
Por cada intento, escribir:
=== INTENTO {attempt} ===
PROMPT:\n{prompt}
RESPUESTA DEL MODELO:\n{response}
CÓDIGO DE TEST EXTRAÍDO:\n{test_code}
COMANDO EJECUTADO:\n{command}
SALIDA:\n{output_log}
CÓDIGO DE RETORNO: {retcode}
ÉXITO: {success}
Al finalizar la fase, escribir === FIN DE FASE ===.
🔹 Fase 4 – Actualizar el orquestador para enviar análisis SAST detallado
En sast_orchestrator.py, modificar _run_sast para que al crear Vulnerability se incluya en additional_properties la salida completa de la herramienta que detectó el problema (por ejemplo, raw_output del resultado SAST).
En _generate_task_input, añadir el campo "sast_analysis": task.vulnerability.additional_properties.get("tool_output", "").
Asegurar que este campo se incluya en el input.json que se pasa al contenedor.
🔹 Fase 5 – Pruebas
Reconstruir la imagen base: make build-base o docker build -f docker/Dockerfile.base -t tdh-base:latest .
Ejecutar el orquestador sobre el repositorio de prueba:
bash
python tdh_unified.py sast-orchestrated https://github.com/alonsoir/test-zeromq-c-.git
Observar los logs del contenedor (en el worktree) y verificar:
El contexto completo aparece al inicio.
En cada intento, el modelo recibe el prompt adecuado.
Si falla, el feedback incluye toda la información.
El modelo no crea archivos nuevos.
Si la vulnerabilidad es un falso positivo, documentar el comportamiento y considerar añadir en el futuro una detección de falsos positivos.
🔹 Fase 6 – (Opcional) Mejorar la evaluación del test
En lugar de preguntar al modelo si el test reproduce el bug, podríamos usar una heurística para errores de sintaxis (código de retorno != 0 y presencia de "error" en la salida). Pero por ahora mantener la evaluación por LLM con un prompt más específico.
📝 Tareas concretas para mañana

Modificar sota_agent.py (fases 1, 2 y 3).
Modificar sast_orchestrator.py (fase 4).
Reconstruir imagen Docker y probar.
Analizar logs y ajustar prompts si es necesario.
⚠️ Supuestos y riesgos

El análisis SAST detallado puede ser muy extenso; habrá que limitarlo a un tamaño razonable (ej. primeras 1000 líneas) para no saturar el contexto del modelo.
Los modelos gratuitos pueden seguir teniendo rate limiting; considerar usar modelos de pago si es necesario.
La persistencia del contexto en el contenedor asume que el contenedor vive durante toda la tarea (máx 3 intentos). Esto ya es así.
📦 Mensaje de commit para mañana

text
feat(agent): contexto persistente y logs trazables en agente SOTA

- Se carga core y skills una sola vez al inicio del contenedor.
- El análisis SAST detallado se incluye en el input.json y se pasa al agente.
- En test_design, el prompt base incluye todo el contexto (skills, análisis, archivo).
- En caso de fallo, se añade feedback detallado sin perder el contexto original.
- Se genera un archivo de log por vulnerabilidad con prompts, respuestas y salidas.
- Se elimina recarga innecesaria de skills en call_openrouter.
Este prompt de continuidad te permitirá retomar mañana exactamente donde lo dejamos, con todas las tareas claramente definidas. ¡Éxito con la implementación!