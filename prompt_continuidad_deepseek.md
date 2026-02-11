## 📋 **PROMPT DE CONTINUIDAD – TDH ENGINE (2026-02-11)**

---

### ✅ **LO QUE HEMOS LOGRADO HOY**

| Área | Estado | Detalle |
|------|--------|---------|
| **SAST Pipeline** | ✅ COMPLETO | 5 herramientas integradas: cppcheck, flawfinder, bandit, semgrep, **trivy** |
| **Configuración SAST** | ✅ COMPLETO | `sast_config.yaml` con trivy, filtros de falsos positivos, mapeo CWE/OWASP |
| **Entorno Vagrant** | ✅ ESTABLE | VM Ubuntu 22.04, sincronización VirtualBox shared folders, Docker nativo, herramientas SAST preinstaladas |
| **Imagen Docker base** | ✅ CONSTRUIDA | `tdh-base:latest` con Python 3.11, compiladores, bandit, semgrep, requests (pendiente script SOTA) |
| **Prueba end-to-end** | ✅ FUNCIONAL | `python tdh_unified.py test` clona repo, ejecuta SAST, crea contenedor, limpia – **sin ejecución de LLM** |
| **Análisis orquestado** | ⚠️ PARCIAL | Crea 1 contenedor, ejecuta SAST, **no asigna tareas, no usa OpenRouter, no genera PRs** |
| **SOTAs / OpenRouter** | ❌ NO IMPLEMENTADO | No hay llamadas API, no hay script agente, no hay consejo de sabios |
| **Máquina de estados** | ❌ NO IMPLEMENTADO | Solo existe configuración YAML, no hay código que gestione estados |
| **Pull Requests** | ❌ NO IMPLEMENTADO | No hay integración con GitHub API |

---

### 🧠 **ARQUITECTURA OBJETIVO (CONFIRMADA)**

#### 1. **Worktrees**
- **Sí, un worktree es una copia funcional del repositorio en un directorio separado, compartiendo el historial de Git.**
- El engine crea un worktree por cada SOTA dentro del volumen montado en su contenedor.
- **No es una funcionalidad de GitHub, sino nativa de Git.**  
  El engine usará `git worktree add` para tener una copia aislada que la SOTA pueda modificar libremente.

#### 2. **Asignación de vulnerabilidades**
- El engine **filtra solo vulnerabilidades HIGH y CRITICAL** del informe SAST.
- Cada vulnerabilidad se asigna **individualmente** a una SOTA (configurable: una por SOTA o varias).
- Se mantiene el **estado de cada tarea** (pendiente, en análisis, test diseñado, fix propuesto, documentado, listo para PR).
- Las SOTAS **no** atacan todas las vulnerabilidades a la vez; el engine las dosifica.

#### 3. **Comunicación entre SOTAS**
- Las SOTAS pueden **interactuar entre sí** mediante el engine (o directamente si se habilita).
- Los logs deben reflejar claramente: `[SOTA:claude-3-5] consultando a SOTA:gpt-4 sobre CWE-78`.
- El engine actúa como **mediador** o permite que las SOTAS se envíen mensajes a través de la API.

#### 4. **Entorno del contenedor SOTA**
- Cada contenedor tiene **todas las herramientas del sistema base**: `cat, awk, grep, make, ls, wc, git`, etc.
- **Soporte inicial**: proyectos C, C++ y Python que tengan un `Makefile` en la raíz.
- El contenedor debe poder **compilar y ejecutar tests** (gcc/g++, make, python3).
- **Script SOTA**: `sota_agent.py` (dentro del contenedor) que:
  - Recibe vía `stdin` un JSON con: `repo_path`, `model`, `vulnerability`, `openrouter_api_key`.
  - Construye el prompt adecuado (configurable desde YAML).
  - Llama a OpenRouter API.
  - Devuelve un JSON con `test_code`, `fixed_code`, `explanation`.
  - Opcionalmente puede ejecutar comandos en el worktree (buscar, editar, compilar).

#### 5. **Generación de Pull Requests**
- El engine, **después de recibir el resultado de la SOTA**, aplica los cambios en el worktree correspondiente.
- Crea una **rama** con nombre `sota/<modelo>/<cwe-id>`.
- Hace commit y push.
- Crea una **Pull Request** usando la API de GitHub (token con permisos).
- La PR incluye el test y el fix, con descripción generada por la SOTA.

---

### 📦 **ESTADO DEL CÓDIGO ACTUAL (POST-COMMIT)**

- **Rama activa**: `feature/tdh-state-machines-20260207`
- **Commit HEAD**: `85e15f7` – "feat(sast): integrate Trivy for comprehensive security scanning"
- **Archivos pendientes de commit**: 
  - `../prompt_continuidad_deepseek.md` (modificado)
  - `../AGENTS.md` (untracked)
- **Vagrantfile actualizado**: usa VirtualBox shared folders, provisionamiento limpio, sin plugins problemáticos.
- **Dockerfile.base**: listo, solo falta añadir `sota_agent.py` y dependencia `requests` (ya instalada).

---

### 🎯 **PLAN DE ACCIÓN PARA MAÑANA (2026-02-12)**

#### 🔹 **FASE 0 – REPRODUCIBILIDAD (MAKE)**
- [ ] Asegurar que todo el flujo se puede lanzar con `make` desde la raíz del proyecto.
- [ ] Verificar que `make vagrant-up`, `make build-base`, `make test` funcionan sin errores.
- [ ] Confirmar que la imagen `tdh-base` tiene Python 3.11, requests, y el script `sota_agent.py` (aunque sea un placeholder).

#### 🔹 **FASE 1 – AGENTE OPENROUTER DENTRO DEL CONTENEDOR**
- [ ] Crear `docker/sota_agent.py` con:
  - Lectura de JSON desde stdin.
  - Llamada a OpenRouter API usando `requests`.
  - Manejo de errores y timeout.
  - Salida JSON.
- [ ] Modificar `docker/Dockerfile.base` para copiar el script y hacerlo ejecutable.
- [ ] Reconstruir imagen: `make build-base`.
- [ ] **Prueba manual**: `docker run -e OPENROUTER_API_KEY=<key> tdh-base python3 /usr/local/bin/sota_agent.py < test_input.json`

#### 🔹 **FASE 2 – ORQUESTADOR MULTI-SOTA**
- [ ] Leer `config/llm_council.yaml` y cargar las SOTAS habilitadas.
- [ ] Modificar `sast_orchestrator.py` para:
  - Filtrar vulnerabilidades HIGH/CRITICAL.
  - **Crear un contenedor por cada SOTA** (no solo una).
  - Para cada contenedor:
    - Montar un **worktree** específico (usando `git worktree add` dentro del volumen).
    - Inyectar la API key y los datos de la vulnerabilidad.
    - Ejecutar `sota_agent.py` y esperar resultado (asíncrono, con timeout configurable).
    - Registrar el estado de la tarea en una máquina de estados (puede ser simple: diccionario en memoria).
  - Recoger resultados y mostrarlos en logs.
- [ ] Agregar logs de interacción entre SOTAS (simulado al principio, luego real).

#### 🔹 **FASE 3 – MÁQUINA DE ESTADOS Y LOGS**
- [ ] Implementar `StateMachine` simple (o usar `transitions` library).
- [ ] Por cada SOTA/tarea, cambiar estado: `ASSIGNED → ANALYZING → TEST_DESIGN → FIX_DESIGN → DOCUMENTING → PR_READY`.
- [ ] Mostrar en consola el progreso de cada SOTA en tiempo real (usar `rich` o similar).

#### 🔹 **FASE 4 – GENERACIÓN DE PULL REQUESTS**
- [ ] Integrar `PyGithub` en el engine.
- [ ] Obtener token de GitHub desde variable de entorno.
- [ ] Función para crear rama, commit y PR por cada SOTA.
- [ ] Incluir en la PR los archivos modificados y el mensaje generado por la LLM.

---

### ⚠️ **RESTRICCIONES Y SUPUESTOS PARA MAÑANA**

1. **Solo se analizarán repositorios que contengan un Makefile** (simplifica compilación y tests).
2. **Las vulnerabilidades asignadas serán únicamente HIGH/CRITICAL**.
3. **Cada SOTA recibirá UNA vulnerabilidad por ejecución** (configurable después).
4. **OpenRouter API key** debe estar presente en el entorno del engine (`OPENROUTER_API_KEY`).
5. **GitHub token** (`GITHUB_TOKEN`) para creación de PRs (opcional al principio, podemos simular).
6. **Los prompts serán configurables** desde `llm_council.yaml` (sección `state_prompts`).
7. **Los contenedores tendrán acceso a Internet** (para llamar a OpenRouter).

---

### 📝 **LO QUE DEJAMOS ESCRITO (ESTE PROMPT)**

Este documento (`prompt_continuidad_deepseek.md`) debe ser commiteado para tener un registro claro del estado y los siguientes pasos. Después de este commit, mañana continuaremos con la implementación de las fases 1-4.

---

### 🚀 **COMANDOS PARA COMENZAR MAÑANA**

```bash
# 1. Actualizar el repositorio
cd engine-prototype
git pull origin feature/tdh-state-machines-20260207

# 2. Levantar entorno limpio (si es necesario)
cd vagrant
vagrant destroy -f
vagrant up

# 3. Conectarse a la VM
vagrant ssh

# 4. Dentro de la VM:
cd /home/vagrant/tdh-engine
source venv/bin/activate
export OPENROUTER_API_KEY="tu-api-key"
export GITHUB_TOKEN="tu-token"

# 5. Construir imagen base con el nuevo script
make build-base

# 6. Probar agente manualmente
echo '{"model":"claude-3.5-sonnet","repo_path":"/workspace/repo","vulnerability":{...}}' | \
docker run -i --rm -e OPENROUTER_API_KEY tdh-base python3 /usr/local/bin/sota_agent.py

# 7. Ejecutar análisis orquestado (aún sin SOTAS, hasta implementar)
python tdh_unified.py sast-orchestrated https://github.com/alonsoir/test-zeromq-c-.git
```

---

## ✅ **CONFIRMACIÓN DE ENTENDIMIENTO**

He entendido perfectamente:
- **Worktrees = copia aislada funcional**, el engine las gestiona.
- **Asignación granular de vulnerabilidades**, solo HIGH/CRITICAL.
- **SOTAS remotas vía OpenRouter**, con script dentro del contenedor.
- **Máquina de estados y logs de interacción**.
- **Soporte inicial C/C++/Python con Makefile**.
- **PRs por SOTA**.

**Mañana nos enfocamos en Fase 1 y 2** para tener el primer flujo completo con una SOTA real.  

---

📌 **Ahora puedes hacer commit de este archivo y empezar mañana con energía.** 💪

```bash
git add ../prompt_continuidad_deepseek.md ../AGENTS.md
git commit -m "docs: add continuity prompt for 2026-02-11 detailing next steps (OpenRouter, multi-SOTA, PRs)"
git push origin feature/tdh-state-machines-20260207
```

**¡Hasta mañana!** 🚀