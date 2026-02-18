Aquí tienes una versión actualizada de `RELATED_WORK.md` que incorpora la inspiración de Karpathy y la influencia de OpenClaw, además de contextualizar el enfoque determinista de TDH.

---

```markdown
# Related Work

## 1. Andrej Karpathy – Agents from Scratch

En su charla y código de ejemplo “Agents from Scratch” (y su serie “Let’s build GPT: from scratch, Agentic”), Karpathy explora la construcción de agentes simples que pueden escribir y ejecutar código. Demuestra la importancia de un bucle controlado (modelo → ejecución → observación) y la necesidad de entornos aislados para evitar efectos secundarios no deseados.  
El trabajo de Karpathy sienta las bases conceptuales de TDH: un agente de lenguaje que interactúa con un entorno de ejecución real, pero en su implementación el agente tiene libertad para ejecutar comandos directamente, lo que puede llevar a comportamientos inseguros si no se acota. TDH toma esta idea y la **endurece** mediante un orquestador que ejecuta todas las acciones, garantizando la reversibilidad y el aislamiento.

## 2. OpenClaw – Skills Imperecederos

OpenClaw es una arquitectura de agentes donde cada modelo (SOTA) posee una personalidad definida por **skills imperecederos** (por ejemplo, `test_design`, `fix_design`, `documentation`) que se le inyectan en cada interacción. Estos skills actúan como instrucciones permanentes que guían el comportamiento del agente, independientemente del contexto específico de la tarea.  
TDH adopta este concepto directamente: cada agente tiene tres skills fijos (diseño de test, diseño de fix, documentación) que se cargan desde `config/skills/` y se incluyen en el contexto de cada fase. Esto asegura que el modelo recuerde su rol y las restricciones (por ejemplo, “no crear archivos nuevos”) aunque el prompt específico varíe. La combinación de skills persistentes con un orquestador determinista es el núcleo de la filosofía **OpenClaw aplicada a la seguridad**.

## 3. AutoGPT y BabyAGI

Estos sistemas populares demuestran el potencial de los agentes autónomos para planificar y ejecutar tareas complejas mediante división en subobjetivos y uso de herramientas. Sin embargo, adolecen de falta de control fino y pueden generar acciones destructivas o no reversibles. TDH se diferencia en que:

- El agente **no ejecuta** nada; solo propone acciones.
- El orquestador valida, ejecuta y garantiza la integridad del repositorio mediante backups automáticos.
- No hay recursividad ni planificación libre; el proceso está rígidamente dividido en tres fases con objetivos claros.

## 4. SWE-agent (Princeton)

SWE-agent es un sistema que utiliza modelos de lenguaje para resolver issues de GitHub, especialmente en repositorios de código. Incluye un entorno controlado y un conjunto de comandos limitados. Es el trabajo más cercano a TDH en espíritu, pero:

- SWE-agent permite al modelo ejecutar comandos bash directamente (aunque restringidos), mientras que TDH solo permite cinco acciones primitivas y toda la ejecución es gestionada por el orquestador.
- TDH introduce una máquina de estados transaccional (backup/rollback) que garantiza que nunca se acumulan cambios no verificados.
- Además, TDH separa explícitamente las fases (test, fix, doc) y utiliza skills persistentes para mantener la coherencia del agente.

## 5. Reproducibility in AI-assisted Security

Existen múltiples trabajos académicos sobre generación automática de parches y tests (por ejemplo, APR tools como GenProg, o herramientas basadas en LLM como VulnFix). La mayoría se centran en la calidad del parche, pero no en la **garantía de que el proceso no dañe el repositorio** ni en la trazabilidad completa de las decisiones. TDH aporta una capa de **hardening del proceso** que complementa estas aproximaciones: antes de confiar en el resultado, aseguramos que cada paso es reversible y está documentado.

## 6. Conclusión: La Singularidad de TDH

TDH no inventa el concepto de agente autónomo ni el de skills persistentes, sino que los combina en un **sistema determinista y transaccional** orientado a la seguridad del código. La principal contribución es la separación radical entre **propuesta (modelo)** y **ejecución (orquestador)** , junto con la garantía de que el estado del repositorio nunca se corrompe, permitiendo así iteraciones seguras incluso cuando el modelo se equivoca.

Este enfoque está directamente inspirado en la filosofía **OpenClaw** (skills imperecederos) y en la necesidad de un **sandboxing fiable** señalada por Karpathy y otros, pero llevado al extremo para aplicaciones de seguridad donde la integridad del código es crítica.
```

Este documento sitúa el proyecto en el panorama actual y explica las diferencias clave. ¿Quieres que añada alguna referencia más o modifique algo?