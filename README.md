Claro, aquí tienes el README.md actualizado y corregido, eliminando el diagrama Mermaid problemático y asegurando que toda la información refleje el estado actual del proyecto.

---

```markdown
# 🛡️ TDH Engine - Test Driven Hardening

Motor de análisis de seguridad avanzado que combina análisis SAST tradicional con agentes autónomos multi‑SOTA para la detección y **corrección automática** de vulnerabilidades en código.

## 🏗️ Arquitectura del Proyecto

```
engine-prototype/
├── tdh_unified.py                 # 🎛️ CLI unificada (punto de entrada principal)
├── src/
│   ├── core/
│   │   ├── sast_orchestrator.py   # 🧠 Orquestador multi‑SOTA (worktrees, contenedores, PRs)
│   │   ├── sast_pipeline.py       # 🔍 Pipeline SAST (cppcheck, flawfinder, bandit, semgrep, trivy)
│   │   └── docker_manager.py      # 🐳 Gestión de contenedores (legacy)
│   └── ...
├── docker/
│   ├── Dockerfile.base            # 📦 Imagen base con herramientas y sota_agent.py
│   └── sota_agent.py              # 🤖 Agente autónomo SOTA (test/fix/document)
├── config/
│   ├── llm_council.yaml           # ⚙️ Configuración de modelos y prompts
│   └── sast_config.yaml           # ⚙️ Configuración de herramientas SAST
├── results/                       # 📊 Reportes generados
├── logs/                          # 📝 Logs de ejecución
├── vagrant/                       # 🖥️ Entorno de desarrollo con Vagrant
└── Makefile                       # 🔧 Automatización completa
```

## 🔄 Flujo de Orquestación Multi‑SOTA

El orquestador ejecuta el siguiente proceso de forma completamente autónoma:

1. **Análisis SAST** con herramientas profesionales (cppcheck, flawfinder, bandit, semgrep, trivy).
2. **Filtrado** de vulnerabilidades HIGH/CRITICAL (según configuración).
3. **Asignación round‑robin** de modelos del consejo (definidos en `llm_council.yaml`).
4. **Creación de worktrees aislados** por vulnerabilidad (ramas únicas con timestamp).
5. **Lanzamiento de contenedores Docker** efímeros con `sota_agent.py`.
6. **Ejecución autónoma del agente**:
   - Diseña y prueba un test que reproduzca la vulnerabilidad.
   - Diseña y aplica un fix, verificando que el test pasa.
   - Documenta el cambio.
7. **Commit, push y creación de Pull Request** en GitHub.
8. **Generación de reporte** JSON con resultados y enlaces a los PRs.

## 🚀 Características Principales

- **Análisis SAST completo** con 5+ herramientas profesionales.
- **Filtrado inteligente** por severidad (solo HIGH/CRITICAL).
- **Múltiples modelos SOTA** configurables (OpenRouter).
- **Worktrees aislados** por vulnerabilidad.
- **Contenedores Docker** limpios y efímeros.
- **Agente autónomo** que itera test/fix hasta éxito.
- **Pull Requests automáticos** con explicación, test y fix.
- **Modo `--dry-run`** para pruebas sin interacción externa.
- **Reportes detallados** en JSON y consola.

## ⚡ Instalación Rápida

### Con Vagrant (recomendado)
```bash
git clone https://github.com/alonsoir/test-driven-hardening.git
cd test-driven-hardening/engine-prototype
make vagrant-up      # Crea y provisiona la VM
make vagrant-ssh     # Conéctate a la VM
cd /home/vagrant/tdh-engine
```

### Manual (en máquina local)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
make build-base      # Construye imagen Docker tdh-base
```

## 🔑 Configuración

### 1. Archivo `.env` (en la raíz del proyecto)
```bash
OPENROUTER_API_KEY=sk-or-v1-...
GITHUB_TOKEN=ghp_...
```

### 2. Consejo de modelos (`config/llm_council.yaml`)
```yaml
llm_configs:
  claude-3-5-sonnet:
    provider: openrouter
    model: anthropic/claude-3.5-sonnet
    max_tokens: 4000
    temperature: 0.1
    priority: 1

  gpt-4-turbo:
    provider: openrouter
    model: openai/gpt-4-turbo
    max_tokens: 4000
    temperature: 0.1
    priority: 2

  deepseek-coder:
    provider: openrouter
    model: deepseek/deepseek-coder
    max_tokens: 4000
    temperature: 0.1
    priority: 3
```

## 🎯 Uso

### Análisis SAST puro (sin agentes)
```bash
tdh_unified.py sast-real https://github.com/usuario/repo.git
```

### Orquestación multi‑SOTA completa (con fixes y PRs)
```bash
# Modo dry‑run (solo simula)
tdh_unified.py sast-orchestrated https://github.com/usuario/repo.git --dry-run

# Modo real (genera PRs)
tdh_unified.py sast-orchestrated https://github.com/usuario/repo.git
```

### Opciones adicionales
```bash
# Limitar modelos a usar
tdh_unified.py sast-orchestrated https://github.com/usuario/repo.git --council claude-3-5-sonnet gpt-4-turbo

# Construir imagen base
tdh_unified.py build-base
```

## 📋 Ejemplo Completo

```bash
# 1. Activar entorno (si no se está en la VM)
source venv/bin/activate

# 2. Ejecutar orquestación real
tdh_unified.py sast-orchestrated https://github.com/tu-usuario/test-zeromq-c-.git
```

Salida esperada:
```
🚀 ORQUESTACIÓN MULTI‑SOTA para https://github.com/tu-usuario/test-zeromq-c-.git
✅ SAST completado. 1183 vulnerabilidades encontradas.
Vulnerabilidades HIGH/CRITICAL: 14
[TASK:a1b2c3] Estado → worktree_created
[TASK:d4e5f6] Estado → worktree_created
[TASK:a1b2c3] Estado → container_started
[SOTA:claude-3.5-sonnet][STATE:test_designing] Starting test design...
...
✅ Pull request creado: https://github.com/tu-usuario/test-zeromq-c-.git/pull/1
✅ Pull request creado: https://github.com/tu-usuario/test-zeromq-c-.git/pull/2
📊 Reporte guardado en results/orchestration_20260214_123456.json
```

## 🐳 Desarrollo con Vagrant

### Comandos útiles (desde el host)
```bash
make vagrant-up        # Inicia VM
make vagrant-ssh       # Conecta a VM
make vagrant-halt      # Detiene VM
make vagrant-destroy   # Destruye VM
make vm-example        # Ejecuta ejemplo dry‑run dentro de la VM
```

## 🔧 Solución de Problemas

### Error 429 / 402 en OpenRouter
- Añade crédito a tu cuenta (https://openrouter.ai/settings/limits).
- Usa modelos gratuitos verificados (ej. `google/gemma-3-27b-it:free`).
- Reduce concurrencia (el orquestador ya usa semáforo `asyncio.Semaphore(1)`).

### Error de autenticación GitHub
- Verifica que `GITHUB_TOKEN` tiene permisos `repo`.
- Comprueba que el token está en el `.env` y se carga correctamente.

### Error en el agente (código 1)
- Revisa los logs DEBUG en la salida del orquestador.
- Asegura que `sota_agent.py` tiene permisos de ejecución en la imagen.
- Verifica que el modelo especificado en `input.json` coincide con una clave en `llm_council.yaml`.

## 📊 Reportes

Cada ejecución genera un JSON en `results/` con:
- Total de tareas, completadas, fallidas, PRs creados.
- Lista detallada por tarea: modelo, vulnerabilidad, estado, URL del PR, error.

## 🤝 Contribuir

1. Haz un fork del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza los cambios y prueba con `make vm-example`.
4. Envía un Pull Request.

## 📄 Licencia

MIT License – Ver [LICENSE](LICENSE) para más detalles.

---

**¿Listo para automatizar la corrección de vulnerabilidades?** ⭐ Dale una estrella en GitHub y únete a la revolución del hardening autónomo.
```

