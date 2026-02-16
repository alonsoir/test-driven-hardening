📋 Prompt de Continuidad – Día 2026-02-16

✅ Lo que hemos logrado hoy
Mejora del agente SOTA:
Se modificó sota_agent.py para leer el contenido del archivo vulnerable (file_content) y pasarlo como placeholder en los prompts de test_designing y fix_designing.
Se mejoró extract_code_blocks para capturar el lenguaje del bloque de código.
Se añadió manejo de rate limiting con backoff exponencial en call_openrouter.
Se añadió logging de la salida del test cuando falla, para depuración.
Actualización de prompts:
En llm_council.yaml, se actualizó test_designing para incluir el contenido del archivo, la línea exacta y la instrucción de no crear nuevos archivos fuente (usar el archivo existente).
Se creó openrouter_instructions.md con instrucciones universales de formato.
Resultados de la última ejecución:
Claude generó un test que compilaba el archivo real en el primer intento, pero el test falló (quizás porque el archivo no tiene error de sintaxis real o la detección no fue correcta).
En intentos posteriores, Claude ignoró el archivo real y creó archivos nuevos, lo que indica que la retroalimentación no fue suficientemente clara.
Gemma sufrió rate limiting prolongado, que con el nuevo backoff debería manejarse mejor.
🐞 Problemas detectados
Retroalimentación insuficiente: Cuando un test falla, el agente no explica por qué falló, lo que lleva al modelo a cambiar de estrategia.
Formato de bloques: A veces los modelos no siguen el formato [test] y [command] exacto, a pesar de las instrucciones.
Rate limiting: Aunque mejorado, aún puede causar tiempos de espera largos (80s) que podrían agotar el tiempo del orquestador.
Validación de tests: No está claro si el test de Claude (primer intento) realmente debería haber pasado o no.
🎯 Plan de acción para mañana (2026-02-17)

🔹 Fase 1 – Mejorar la retroalimentación en phase_test_design
Modificar phase_test_design para que, cuando un test falla, se envíe al LLM un mensaje detallado con:
La salida completa del comando ejecutado (stdout y stderr).
El código de retorno.
Una instrucción explícita de que debe usar el archivo vulnerable existente y no crear nuevos.
Un recordatorio del formato esperado.
🔹 Fase 2 – Validar el test del primer intento de Claude
Ejecutar manualmente el test generado por Claude en el primer intento para ver si realmente detecta el error de sintaxis.
Si el test debería haber pasado pero no lo hizo, ajustar la lógica de evaluación (quizás el grep no captura el error correctamente).
Si el archivo no tiene error real, considerar que el SAST puede estar generando un falso positivo.
🔹 Fase 3 – Ajustar el prompt test_designing aún más
Incluir un ejemplo específico para el caso de error de sintaxis, mostrando cómo capturar la salida del compilador y verificar el error.
Reforzar la instrucción de no crear archivos nuevos con un ejemplo negativo.
🔹 Fase 4 – Mejorar el manejo de rate limiting
Considerar usar un semáforo en el orquestador para no lanzar múltiples tareas a la vez que puedan saturar la cuota.
Añadir un límite de tiempo global para cada fase, de modo que si un modelo se queda atascado en reintentos, la tarea falle rápidamente.
🔹 Fase 5 – Probar con un modelo de pago
Usar claude-3.5-sonnet (de pago) tiene menos restricciones de rate limiting. Verificar que la API key tiene crédito suficiente.
📝 Tareas concretas
Ejecutar manualmente el test del primer intento de Claude (en la VM) y documentar resultado.
Modificar phase_test_design para enviar retroalimentación detallada.
Actualizar llm_council.yaml con ejemplos más precisos.
Reconstruir imagen Docker y probar.
Si el test falla, iterar sobre el prompt hasta que el modelo genere tests correctos.
⚠️ Supuestos y riesgos
El archivo ipset_wrapper.cpp puede no tener realmente un error de sintaxis, lo que explicaría por qué el test falla. Verificar con cppcheck o compilación manual.
Los modelos gratuitos pueden seguir siendo lentos o tener rate limiting. Considerar cambiar a modelos de pago en el llm_council.yaml.
La nueva retroalimentación debe ser clara y concisa para no confundir al modelo.
📦 Mensaje de commit para hoy

bash
git add .
git commit -m "feat(agent): mejorar prompts y retroalimentación en test_designing

- Añade contenido del archivo vulnerable en prompts.
- Mejora extract_code_blocks para capturar lenguaje.
- Implementa backoff exponencial en rate limiting.
- Agrega logging de salida de tests fallidos.
- Actualiza openrouter_instructions.md con formato universal.

Pendiente: Validar test de Claude y mejorar retroalimentación cuando falla."