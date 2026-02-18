# TDH Engine – Roadmap

## Visión General

El desarrollo del motor TDH se organiza en tres fases principales, cada una construyendo sobre la anterior. El objetivo final es un sistema capaz de analizar, reproducir y corregir vulnerabilidades de forma autónoma y fiable, con garantías de integridad y trazabilidad.

---

## Fase 1: Deterministic Single‑Model Loop (Actual)

**Objetivo**: Conseguir un ciclo completamente automático con **un solo modelo** y **un solo bug**, utilizando únicamente las cinco herramientas básicas. Esta fase debe ser estable antes de pasar a la siguiente.

### Herramientas habilitadas
- `read_file`
- `search` (grep-like)
- `write_file` (con backup automático)
- `compile`
- `run_binary`

### Hitos

1. **Implementación del orquestador básico** (semanas 1-2)
   - Clonado de repositorios.
   - Creación de contenedor Docker con aislamiento.
   - Creación de worktree transaccional.
   - Backups automáticos antes de `write_file`.
   - Rollback en caso de fallo de verificación.

2. **Integración con el agente LLM** (semana 3)
   - Comunicación con OpenRouter (o API similar).
   - Inyección de skills persistentes (`test_design`, `fix_design`, `documentation`).
   - Protocolo de acciones JSON.
   - Validación de acciones permitidas.

3. **Ciclo completo para un caso simple** (semana 4)
   - Prueba con una vulnerabilidad conocida (ej. buffer overflow simple).
   - El agente debe:
     - Leer el archivo vulnerable.
     - Diseñar un test que reproduzca el fallo.
     - El orquestador compila y ejecuta el test → falla (éxito de la fase 1).
     - El agente propone un fix.
     - El orquestador aplica el fix, recompila y ejecuta el test → pasa (éxito de la fase 2).
     - El agente genera documentación.
   - Manejo de reintentos (hasta 3 por fase) con feedback enriquecido.
   - Logging detallado.

4. **Refinamiento y pruebas** (semana 5)
   - Probar con 2-3 vulnerabilidades diferentes.
   - Ajustar prompts y feedback según los logs.
   - Documentar el proceso y los resultados.

**Criterio de salida de Fase 1**:
- El sistema completa automáticamente el ciclo (test→fix→doc) para al menos 3 casos de prueba diferentes, sin intervención humana.
- Los logs contienen toda la información necesaria para depurar cualquier desviación.
- El orquestador nunca deja el repositorio en un estado inconsistente (verificado por pruebas de rollback).

---

## Fase 2: Multi‑Model Competition (Futuro)

**Objetivo**: Introducir múltiples agentes que compitan o colaboren para mejorar la calidad del test y del fix, manteniendo las garantías de la Fase 1.

### Nuevas capacidades
- Lanzamiento de varios contenedores en paralelo, cada uno con un agente diferente (o el mismo modelo con diferentes semillas/prompts).
- Un supervisor que compare los resultados de cada agente:
  - Tests que reproducen la vulnerabilidad.
  - Fixes propuestos.
- Validación cruzada: el test de un agente se usa para verificar el fix de otro.
- Selección de la mejor solución (por ejemplo, la que pase todos los tests y tenga el menor impacto en el código).

### Herramientas adicionales (opcionales)
- `diff` para comparar cambios.
- `analyze` para ejecutar análisis estático adicional.

**Criterio de salida de Fase 2**:
- El sistema es capaz de generar al menos dos fixes diferentes para una misma vulnerabilidad y elegir el mejor según criterios predefinidos.
- Se ha probado con modelos distintos (ej. GPT-4, Claude, Llama) y se han documentado las diferencias.

---

## Fase 3: Escalado y Automatización Completa (Visión a Largo Plazo)

**Objetivo**: Integrar TDH en flujos de CI/CD, permitir análisis masivo de repositorios y generar pull requests automáticas.

### Nuevas capacidades
- Integración con sistemas de gestión de código (GitHub, GitLab) mediante webhooks.
- Análisis por lotes de múltiples vulnerabilidades en un mismo repositorio.
- Generación de informes consolidados y pull requests con los fixes validados.
- Plugin para IDE que permita al desarrollador solicitar un análisis TDH sobre una línea de código.

### Herramientas adicionales
- `fuzz` para generar entradas de fuzzing.
- `trace` para ejecutar con debugger y obtener trazas.
- `measure` para evaluar métricas de seguridad (complejidad ciclomática, etc.).

**Criterio de salida de Fase 3**:
- TDH se ejecuta automáticamente en cada push a un repositorio protegido, analizando las vulnerabilidades detectadas por SAST y proponiendo fixes en forma de PR.
- El sistema ha sido usado en producción durante al menos 3 meses con una tasa de éxito >80% en vulnerabilidades sencillas.

---

## Hitos Transversales

A lo largo de todas las fases, se mantendrán los siguientes principios:

- **Seguridad**: el modelo nunca ejecuta comandos; el orquestador sí.
- **Transaccionalidad**: todos los cambios son reversibles.
- **Trazabilidad**: logs detallados de cada paso.
- **Aislamiento**: contenedores sin red y efímeros.

---

## Resumen de Timeline Estimado

| Fase | Duración estimada | Estado       |
|------|-------------------|--------------|
| 1    | 5 semanas         | En progreso  |
| 2    | 4 semanas         | Planificado  |
| 3    | 6 semanas         | Visión       |

*Nota: Las duraciones son orientativas y dependerán de los hallazgos durante el desarrollo.*

---

## Cómo Contribuir en Cada Fase

- **Fase 1**: issues etiquetados como `phase-1` (core, orquestador, integración con modelo).
- **Fase 2**: issues etiquetados como `phase-2` (multi-agente, comparación, validación cruzada).
- **Fase 3**: issues etiquetados como `phase-3` (CI/CD, escalado, plugins).

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) para más detalles.

---

Este roadmap está vivo y se actualizará a medida que avance el proyecto. Las prioridades pueden ajustarse según los resultados de cada fase.