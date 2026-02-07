# 🤖 **PROMPT DE CONTINUIDAD - TDH ENGINE**

## 📋 **CONTEXTO DE SESIÓN ANTERIOR:**
**Fecha:** Viernes 6 de febrero, primera hora de la mañana  
**Tema:** Diseño de arquitectura completa del TDH Engine  
**Estado:** Prototipo mockeado, plan de implementación definido  
**Próximo paso:** Implementación real de infraestructura Docker + SAST pipeline

## 🎯 **OBJETIVO DE LA PRÓXIMA SESIÓN:**
Implementar la **infraestructura Docker completa** y el **pipeline SAST real** para transicionar del prototipo mockeado al sistema de producción.

---

## 🔧 **TAREAS CONCRETAS PARA COMENZAR:**

### **1. Crear Dockerfile base con todas las herramientas necesarias:**
```dockerfile
# Dockerfile.base
FROM ubuntu:22.04
# Incluir:
# - Compiladores: gcc, g++, clang, make, cmake
# - Herramientas SAST: cppcheck, flawfinder, bandit, semgrep
# - Herramientas de testing: valgrind, gdb, python3-pip
# - Entornos: Python 3.11, Node.js 18+, Java 17
# - Git y herramientas de desarrollo
```

### **2. Implementar docker_manager.py con funcionalidades reales:**
```python
class DockerManager:
    def create_isolated_container(self, llm_name, repo_url):
        # 1. Crear contenedor desde imagen base
        # 2. Montar volumen con worktree
        # 3. Clonar repositorio dentro del contenedor
        # 4. Instalar dependencias específicas del proyecto
        # 5. Configurar red para comunicación LLM
        pass
```

### **3. Implementar SAST pipeline con herramientas reales:**
```python
class SASTPipeline:
    async def run_cppcheck_real(self, repo_path):
        # Ejecutar cppcheck real con parámetros profesionales
        # Parsear resultados en formato estructurado
        # Filtrar falsos positivos inteligentemente
        pass
```

---

## 📊 **CRITERIOS DE ÉXITO PARA ESTA SESIÓN:**

### **✅ Objetivos mínimos (4 horas):**
- [ ] `Dockerfile.base` creado y construido exitosamente
- [ ] `docker_manager.py` puede crear y destruir contenedores
- [ ] Pipeline SAST ejecuta cppcheck real en repositorio de prueba
- [ ] Resultados SAST se parsean a formato estructurado JSON

### **🟡 Objetivos medios (8 horas):**
- [ ] Contenedores aislados con worktrees funcionales
- [ ] 3+ herramientas SAST integradas (cppcheck, bandit, semgrep)
- [ ] Sistema de filtrado de falsos positivos básico
- [ ] Vulnerabilidades priorizadas por severidad/confianza

### **🟢 Objetivos completos (12+ horas):**
- [ ] Red Docker para comunicación entre LLMs
- [ ] Pipeline SAST completo con 5+ herramientas
- [ ] Integración con Docker Manager (SAST → contenedores)
- [ ] Prueba end-to-end con repositorio real

---

## 🔗 **ARCHIVOS A CREAR/MODIFICAR:**

### **Nuevos:**
```
docker/Dockerfile.base
docker/docker_manager.py
sast/sast_pipeline.py
sast/cppcheck_analyzer.py
sast/bandit_analyzer.py
config/docker_config.yaml
```

### **Modificar:**
```
tdh_unified.py (actualizar comandos para usar Docker real)
src/core/sast_orchestrator.py (reemplazar con implementación real)
requirements.txt (añadir docker, aiohttp, etc.)
```

---

## 🚨 **PUNTOS DE ATENCIÓN CRÍTICOS:**

### **1. Gestión de recursos Docker:**
- Limpieza automática de contenedores
- Límites de CPU/memoria por contenedor
- Logging centralizado

### **2. Parseo de resultados SAST:**
- Normalización de formatos diferentes (cppcheck vs bandit vs semgrep)
- Mapeo a CWEs/OWASP Top 10
- Extracción de contexto de código

### **3. Preparación de entornos:**
- Detección automática de lenguajes del proyecto
- Instalación inteligente de dependencias
- Configuración de herramientas de build

---

## 📝 **PROMPT DE INICIO PARA DEEPSEEK:**

"Basándonos en la discusión del viernes sobre la arquitectura completa del TDH Engine, comenzamos la implementación real. 

**Contexto actual:** Tenemos un prototipo mockeado con `tdh_unified.py` funcionando básicamente, pero sin Docker real, sin SAST real, y sin LLMs reales. 

**Objetivo inmediato:** Implementar la infraestructura Docker completa y el pipeline SAST real para analizar vulnerabilidades críticas en repositorios C/C++.

**Tarea concreta:** 
1. Crear `docker/Dockerfile.base` con todas las herramientas de desarrollo y seguridad necesarias
2. Implementar `docker/docker_manager.py` que pueda:
   - Crear contenedores aislados por LLM
   - Clonar repositorios dentro del contenedor
   - Ejecutar comandos en el contenedor
   - Gestionar volúmenes para worktrees
3. Implementar `sast/sast_pipeline.py` que ejecute:
   - **cppcheck** real con configuración profesional
   - **bandit** para Python si existe
   - **semgrep** con reglas de seguridad
   - Parsear resultados a formato JSON normalizado

**Requisitos específicos:**
- Los contenedores deben estar completamente aislados
- El análisis SAST debe identificar vulnerabilidades reales (no mock)
- Los resultados deben incluir: archivo, línea, severidad, CWE, código vulnerable
- El sistema debe funcionar con el repositorio de prueba: `https://github.com/alonsoir/test-zeromq-c-.git`

**Preguntas para guiar la implementación:**
1. ¿Qué herramientas específicas deben incluirse en el Dockerfile base?
2. ¿Cómo estructurar los resultados SAST para que sean útiles para los LLMs?
3. ¿Cómo manejar proyectos con múltiples lenguajes (C, C++, Python, etc.)?
4. ¿Qué sistema de logging implementar para depuración?

**Comencemos creando el Dockerfile.base con las herramientas esenciales para análisis de seguridad en C/C++.**"

---

## 🎪 **EJEMPLO DE FLUJO ESPERADO AL FINAL DE LA SESIÓN:**

```bash
# 1. Construir imagen base
docker build -f docker/Dockerfile.base -t tdh-base:latest .

# 2. Ejecutar análisis SAST real
python tdh_unified.py sast-real https://github.com/alonsoir/test-zeromq-c-.git --output ./results

# Debería mostrar:
# 🔍 Ejecutando cppcheck...
# 🔍 Ejecutando bandit...
# 🔍 Ejecutando semgrep...
# ✅ Encontradas 8 vulnerabilidades CRITICAL
# 💾 Resultados guardados en ./results/sast_results.json

# 3. Crear contenedor para LLM
python tdh_unified.py docker-prepare --llm claude-3-5 --repo https://github.com/alonsoir/test-zeromq-c-.git

# Debería mostrar:
# 🐳 Creando contenedor para claude-3-5...
# 📦 Clonando repositorio en contenedor...
# ⚙️ Instalando dependencias...
# ✅ Contenedor listo: tdh-claude-3-5-abc123
```

---

## 📞 **PUNTOS DE DECISIÓN PARA CONSULTA:**

### **Decisiones de arquitectura necesarias:**
1. ¿Usar Docker Compose o Docker SDK for Python?
2. ¿Estructura de volúmenes: named volumes o bind mounts?
3. ¿Sistema de comunicación entre contenedores: Redis, RabbitMQ, o sockets Docker?
4. ¿Formato de resultados SAST: SARIF, JSON personalizado, o ambos?

### **Decisiones de configuración:**
1. ¿Qué reglas de cppcheck habilitar/deshabilitar?
2. ¿Qué configuraciones de semgrep usar (auto, security, etc.)?
3. ¿Cómo manejar proyectos con sistemas de build complejos (CMake, Makefile, Autotools)?

---

## 🎯 **METRICA DE PROGRESO FINAL:**

Al final de esta sesión, deberíamos poder responder **SÍ** a:
- [ ] ¿Puede el TDH Engine analizar un repositorio C/C++ real y encontrar vulnerabilidades reales?
- [ ] ¿Puede crear contenedores Docker aislados con el código del repositorio?
- [ ] ¿Los resultados del análisis son estructurados y listos para enviar a LLMs?
- [ ] ¿El sistema es reproducible y escalable?

---

**¿Comenzamos con la implementación del Dockerfile base y la integración de cppcheck real?** Este es el fundamento sobre el cual construiremos todo el sistema de hardening test-driven. 🚀