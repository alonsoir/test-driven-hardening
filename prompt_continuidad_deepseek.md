# 📋 Continuidad para 2026-02-16

## Estado actual
- El entorno Vagrant funciona perfectamente: `make vagrant-up` + `make vagrant-ssh` te deja dentro de la VM con todo listo.
- El orquestador multi‑SOTA ejecuta tareas reales, pero los agentes fallan en la generación de tests (Claude) o en la generación de fixes (Gemma).
- Hemos mejorado los prompts y la extracción de bloques, pero los LLM gratuitos de OpenRouter no siguen consistentemente el formato.

## Pendiente para mañana
1. **Implementar instrucciones extra** tipo `claude.md` para todos los modelos: añadir un preámbulo al prompt del sistema con el formato de salida obligatorio y ejemplos. Esto podría estar en un archivo `system_prompt_base.txt` que se concatene.
2. **Probar con modelos de pago** (Claude 3.5 Sonnet) que tienen mejor seguimiento de instrucciones. Tenemos crédito.
3. **Mejorar logging** en `sota_agent.py` para guardar la respuesta completa del LLM en cada intento (ya lo hace, pero podemos añadir más contexto).
4. **Iterar sobre los prompts** de `fix_designing` para que el agente entienda mejor cómo aplicar el fix en el archivo correcto.
5. **Depurar el caso de Claude**: ¿por qué no genera bloques? Posiblemente el prompt es demasiado largo o el modelo ignora las instrucciones. Probar con un prompt más corto y directo.
6. **Si persisten los fallos, considerar usar un modelo más pequeño pero más fiable** (ej. `mistralai/mistral-7b-instruct:free`) y ajustar prompts para ese modelo.

## Próximos pasos concretos
- Modificar `sota_agent.py` para que en `get_prompt` cargue un `base_system_prompt` desde un archivo (ej. `config/system_prompt_base.txt`) y lo concatene al prompt específico del estado.
- Probar con el modelo de pago `anthropic/claude-3.5-sonnet` (sin `:free`) para ver si mejora.
- Si funciona, ajustar el `llm_council.yaml` para darle prioridad máxima a ese modelo.
- Documentar los resultados y ajustar los prompts en base a las respuestas fallidas.

