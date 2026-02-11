# ROADMAP.md

# 🚀 TDH ENGINE – ROADMAP DE DESARROLLO

**Última actualización:** 2026-02-11  
**Versión objetivo:** 1.0.0 (Q2 2026)  
**Repositorio:** [test-driven-hardening/engine-prototype](https://github.com/alonsoir/test-driven-hardening)

---

## 📌 VISIÓN GENERAL

**TDH Engine** es una plataforma de *Test-Driven Hardening* que combina análisis estático de seguridad (SAST) con un consejo de agentes LLM (SOTAs) para **identificar, demostrar y corregir vulnerabilidades de forma automatizada**. El engine orquesta contenedores aislados, asigna tareas críticas a múltiples modelos de lenguaje (Claude, GPT, DeepSeek, etc.) a través de OpenRouter, y genera Pull Requests listas para revisión.

**Objetivo estratégico:** Convertir el proceso de hardening de código en un flujo completamente automatizado, reproducible y extensible, reduciendo el tiempo entre la detección y la corrección de vulnerabilidades.

---

## ✅ ESTADO ACTUAL (2026-02-11)

### 🟢 Completado / Estable

| Componente | Estado | Observaciones |
|-----------|--------|---------------|
| **Entorno Vagrant** | ✅ | VM Ubuntu 22.04, sincronización de archivos, Docker nativo sin Desktop |
| **Imagen base Docker** | ✅ | `tdh-base:latest` con Python 3.11, compiladores C/C++, herramientas SAST |
| **Pipeline SAST** | ✅ | Integración completa de **cppcheck**, **flawfinder**, **bandit**, **semgrep**, **trivy** |
| - Filtrado de falsos positivos | ✅ | Patrones configurables por herramienta |
| - Mapeo CWE / OWASP | ✅ | Automático en resultados |
| - Reportes JSON / SARIF / texto | ✅ | Almacenamiento estructurado |
| **Prueba end-to-end** | ✅ | `tdh_unified.py test` – SAST + creación de contenedor + limpieza |
| **Comando `sast-orchestrated`** | ⚠️ | Crea 1 contenedor, ejecuta SAST, **NO** asigna tareas LLM ni genera PRs |

### 🟡 En progreso / Parcial

| Componente | Estado | Pendiente |
|-----------|--------|-----------|
| **Configuración de SOTAs** | 🟡 | Archivo `llm_council.yaml` con 6 modelos, prompts personalizados – **sin uso en código** |
| **Máquina de estados** | 🟡 | Definición YAML completa – **sin implementación** |

### 🔴 No iniciado

| Componente | Prioridad | Dependencias |
|-----------|-----------|--------------|
| **Agente OpenRouter en contenedor** | 🔥 Alta | Dockerfile.base, script Python, API key |
| **Orquestador multi‑SOTA** | 🔥 Alta | Lectura de YAML, contenedores por SOTA, asignación de worktrees |
| **Gestión de worktrees Git** | 🔥 Alta | `git worktree add` dentro del volumen del contenedor |
| **Asignación granular de vulnerabilidades** | 🔥 Alta | Filtrado HIGH/CRITICAL, una tarea por SOTA |
| **Ejecución asíncrona y timeouts** | 🔥 Alta | Control de procesos en contenedores |
| **Máquina de estados operativa** | 🔥 Alta | Seguimiento de tareas, logs de progreso |
| **Interacción entre SOTAS** | 🔥 Media | Comunicación vía engine (simulada → real) |
| **Generación de Pull Requests** | 🔥 Media | PyGithub, ramas por SOTA, commit + PR |
| **Soporte multiplataforma (C/C++/Python con Makefile)** | 🔥 Alta | Compilación y tests dentro del contenedor |
| **Configuración avanzada de prompts** | 🟡 Media | Uso de sección `state_prompts` del YAML |
| **Dashboard / logs en tiempo real** | 🟡 Baja | Visualización con `rich` o similar |
| **Pruebas unitarias e integración continua** | 🟡 Baja | Pytest, GitHub Actions |

---

## 🗺️ HOJA DE RUTA POR HITOS

### 🎯 **HITO 1 – Fundación SOTA** (3-5 días)
*Hacer que el contenedor pueda hablar con OpenRouter y devolver resultados.*

- [ ] **1.1** Crear `docker/sota_agent.py` (lectura stdin → OpenRouter → stdout JSON)
- [ ] **1.2** Actualizar `Dockerfile.base` (copiar script, instalar `requests`)
- [ ] **1.3** Reconstruir imagen (`make build-base`) y probar manualmente
- [ ] **1.4** Integración básica en `sast_orchestrator.py`:
  - Leer 1 vulnerabilidad crítica
  - Crear 1 contenedor
  - Ejecutar `sota_agent.py` vía `docker exec`
  - Capturar y mostrar resultado

**Entregable:** Un flujo que, dado un repo con Makefile, ejecute SAST, tome la primera vulnerabilidad HIGH y la envíe a Claude 3.5 Sonnet, mostrando el test y fix propuestos.

---

### 🎯 **HITO 2 – Consejo de Sabios (Multi‑SOTA)** (4-6 días)
*Múltiples contenedores trabajando en paralelo sobre worktrees independientes.*

- [ ] **2.1** Cargar `llm_council.yaml` y filtrar SOTAS habilitadas
- [ ] **2.2** Crear **worktree** por contenedor:
  - `git clone --bare` del repositorio en volumen compartido
  - `git worktree add /path/to/worktree <branch>`
- [ ] **2.3** Bucle de creación de contenedores (uno por SOTA)
- [ ] **2.4** Ejecución concurrente de `sota_agent.py` en cada contenedor (asyncio)
- [ ] **2.5** Recolección de resultados y limpieza

**Entregable:** Análisis orquestado que lanza 3-5 SOTAS simultáneamente, cada una con su copia del código, y reporta sus propuestas.

---

### 🎯 **HITO 3 – Estado y Visibilidad** (2-3 días)
*Seguimiento del progreso de cada tarea y logs enriquecidos.*

- [ ] **3.1** Implementar clase `StateMachine` (o usar `transitions`)
- [ ] **3.2** Estados: `ASSIGNED → ANALYZING → TEST_DESIGN → FIX_DESIGN → DOCUMENTING → PR_READY`
- [ ] **3.3** Registrar eventos en memoria y persistencia opcional (checkpoint)
- [ ] **3.4** Mostrar en consola tabla de estado con `rich` (SOTA, vulnerabilidad, estado)
- [ ] **3.5** Logs de interacción: `[SOTA:claude] consultando a gpt-4...`

**Entregable:** El engine muestra en tiempo real el avance de cada SOTA y las comunicaciones entre ellas.

---

### 🎯 **HITO 4 – Generación de Pull Requests** (3-4 días)
*Creación automática de ramas, commits y PRs en GitHub.*

- [ ] **4.1** Integrar `PyGithub` y manejo de token
- [ ] **4.2** Función para aplicar cambios en el worktree:
  - Reescribir archivo con `fixed_code`
  - Añadir test en `tests/` (o donde indique la SOTA)
- [ ] **4.3** Commit + push a rama `sota/<modelo>/<cwe-id>`
- [ ] **4.4** Crear Pull Request usando la API
- [ ] **4.5** Incluir en el cuerpo de la PR la explicación de la SOTA

**Entregable:** Al finalizar el análisis, el engine abre PRs en el repositorio objetivo (por ahora en un fork de prueba).

---

### 🎯 **HITO 5 – Robustez y Extensibilidad** (2-3 semanas)
*Soporte para más lenguajes, configuración externa y tests de integración.*

- [ ] **5.1** Soporte para proyectos sin Makefile (CMake, autotools, setup.py)
- [ ] **5.2** Lenguajes adicionales: Go, Rust, Java (con Maven/Gradle)
- [ ] **5.3** Personalización de prompts por vulnerabilidad / CWE
- [ ] **5.4** Caché de resultados SAST y análisis LLM
- [ ] **5.5** Pruebas unitarias con `pytest` y mocks de OpenRouter
- [ ] **5.6** GitHub Actions para CI

**Entregable:** Engine listo para pruebas en repositorios reales con diferentes stacks tecnológicos.

---

## 🧩 DEPENDENCIAS TÉCNICAS

| Recurso | Uso | Estado |
|--------|-----|--------|
| **OpenRouter API Key** | Llamadas a modelos LLM | ⚠️ Pendiente de configurar |
| **GitHub Token** | Creación de PRs | ⚠️ Pendiente |
| **Docker** | Contenedores SOTA | ✅ Instalado |
| **Git >= 2.5** | Soporte `worktree` | ✅ En VM |
| **Make** | Compilación en contenedores | ✅ En imagen base |
| **Python 3.11** | Entorno del engine | ✅ En VM |

---

## 📈 MÉTRICAS DE ÉXITO (OKRs)

### **Q1 2026 (Ene-Mar)**
- [ ] **KR1:** Pipeline SAST operativo con 5 herramientas → ✅ (Feb)
- [ ] **KR2:** Al menos una SOTA (Claude) completando análisis de una vulnerabilidad HIGH → 🟡 (pendiente Hito 1)
- [ ] **KR3:** Demostración con repositorio público (test-zeromq-c-) generando PRs → 🟡

### **Q2 2026 (Abr-Jun)**
- [ ] **KR4:** Mínimo 3 SOTAS trabajando en paralelo (consejo de sabios)
- [ ] **KR5:** Soporte para C, C++, Python
- [ ] **KR6:** Tasa de acierto en fixes > 70% (validación manual)
- [ ] **KR7:** Lanzamiento de versión 1.0.0

---

## 🧭 PRÓXIMOS PASOS INMEDIATOS (2026-02-12)

1. **Commit del ROADMAP.md y prompt de continuidad** ✅ *(este archivo)*
2. **Revisión del estado de la VM** – ejecutar `make check-env` (aún no existe)
3. **Hito 1 – Fundación SOTA**:
   - Escribir `sota_agent.py`
   - Actualizar `Dockerfile.base`
   - Reconstruir imagen
   - Prueba manual con OpenRouter
4. **Actualizar `sast_orchestrator.py`** para invocar el agente en lugar de solo crear/limpiar

---

## 🤝 CÓMO CONTRIBUIR

1. **Bifurcar el repositorio** y trabajar en la rama `feature/tdh-state-machines-20260207`
2. **Seguir la convención de commits**: `feat|fix|docs|chore(scope): mensaje`
3. **Abrir Pull Requests** tempranas para recibir feedback
4. **Documentar** cualquier cambio en la configuración

---

## 📚 REFERENCIAS

- [Arquitectura del Consejo de Sabios (Andrej Karpathy)](https://x.com/karpathy/status/1748043513156272416)
- [OpenRouter API Docs](https://openrouter.ai/docs)
- [Git Worktree](https://git-scm.com/docs/git-worktree)
- [TDH Engine – Prompt de Continuidad](prompt_continuidad_deepseek.md)

---

**“El hardening de código ya no es un arte; es ingeniería reproducible.”**

*— Roadmap generado el 2026-02-11 tras la integración exitosa de Trivy y el diagnóstico de las SOTAs.*