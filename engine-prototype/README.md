# 🛡️ TDH Engine - Test Driven Hardening Engine

Motor de análisis de seguridad avanzado que combina análisis AST tradicional con herramientas SAST profesionales para detección integral de vulnerabilidades en código.

## 🏗️ Arquitectura del Proyecto

```
engine-prototype/
├── github_analyzer.py            # 🔍 Analizador tradicional AST (script independiente)
├── src/core/
│   ├── sast_orchestrator.py      # 🎛️ Nuevo orquestador principal de SAST
│   ├── config_validator.py       # ✅ Validador de configuración
│   └── (próximamente: integración con github_analyzer)
├── config/
│   ├── tdh_config.yaml           # ⚙️ Configuración principal
│   └── sast_tools.yaml           # 🛠️ Configuración de herramientas SAST
├── scripts/
│   ├── test_sast.py              # 🧪 Pruebas del sistema SAST
│   ├── test_sast_simple.py       # 🧪 Prueba simplificada
│   └── install_sast_tools.sh     # 📦 Instalador de herramientas
├── requirements.txt              # 📦 Dependencias del analizador tradicional
├── requirements-dev.txt          # 📦 Dependencias de desarrollo
├── reports/                      # 📊 Reportes generados
├── logs/                         # 📝 Logs de análisis
└── Makefile                      # 🔧 Automatización completa
```

## 🔄 Dos Enfoques de Análisis

### 1. **SAST Orchestrator (Nuevo - Recomendado)**
Sistema modular que integra múltiples herramientas SAST profesionales:
- **Orquestación inteligente** de herramientas especializadas
- **Configuración centralizada** en YAML
- **Soporte multi-lenguaje** con herramientas nativas
- **Extensible** con nuevas herramientas

### 2. **GitHub Analyzer (Tradicional)**
Script independiente para análisis AST básico:
- **Análisis AST** para Python y C/C++
- **Clonado automático** de repositorios GitHub
- **Formatos múltiples**: texto, JSON, HTML
- **Compatibilidad** con el sistema anterior

## 🚀 Características Principales

### 🔍 **SAST Orchestrator (Moderno)**
- **Integración profesional** con semgrep, bandit, cppcheck, etc.
- **Configuración YAML** centralizada
- **Detección por severidad** configurable
- **Sistema de exclusiones** avanzado
- **Reportes JSON/HTML** para CI/CD
- **Entorno virtual** gestionado por Makefile

### 📦 **GitHub Analyzer (Tradicional)**
- **Análisis AST** para Python y C/C++
- **Clonado automático** de repositorios
- **Detección de vulnerabilidades** comunes
- **Cache local** para análisis repetidos
- **Formatos**: texto, JSON, HTML

## ⚡ Instalación Rápida

### Opción A: Sistema SAST Moderno (Recomendado)
```bash
cd engine-prototype
make init                    # 🎯 Inicializa entorno completo
source venv/bin/activate     # 🔌 Activa entorno virtual
```

### Opción B: Analizador Tradicional
```bash
pip install -r requirements.txt  # Instala dependencias básicas
python github_analyzer.py --help # Verifica funcionamiento
```

## 🎯 Uso Rápido

### Usando el Nuevo SAST Orchestrator
```bash
# Analizar directorio actual
python -m src.core.sast_orchestrator .

# Con configuración personalizada
python -m src.core.sast_orchestrator /ruta/proyecto

# Usar script de prueba simplificado
python scripts/test_sast_simple.py

# Ejecutar a través del Makefile
make run
```

### Usando el GitHub Analyzer Tradicional
```bash
# Analizar repositorio GitHub
python github_analyzer.py analyze usuario/repositorio

# Con diferentes formatos de salida
python github_analyzer.py analyze torvalds/linux --output json
python github_analyzer.py analyze OWASP/CheatSheetSeries --output html

# Analizar repositorio local
python github_analyzer.py local /ruta/al/repositorio
```

## ⚙️ Configuración

### Configuración SAST Moderna (`config/sast_tools.yaml`)
```yaml
tools:
  semgrep:
    enabled: true
    command: "semgrep"
    args:
      base: ["--json", "--config", "auto"]
    file_extensions: [".py", ".js", ".java", ".c", ".cpp"]
  
  bandit:
    enabled: true
    command: "bandit"
    args:
      base: ["-f", "json", "--skip", "B101,B102"]
    file_extensions: [".py"]

exclusions:
  global:
    directories:
      - "**/node_modules/**"
      - "**/.git/**"
      - "**/__pycache__/**"
```

### Migración del Sistema Tradicional
Si vienes usando `github_analyzer.py`, el nuevo sistema ofrece:
- **Más herramientas** de análisis (semgrep, cppcheck, etc.)
- **Mejor configuración** (YAML vs. argumentos CLI)
- **Reportes más detallados** con estadísticas
- **Integración CI/CD** más robusta

## 📋 Comandos Makefile (Productividad)

### 🏗️ Configuración
```bash
make setup          # Configura entorno básico
make setup-dev      # Configura entorno de desarrollo completo
make install-tools  # Instala herramientas SAST
make check-env      # Verifica entorno
make check-tools    # Verifica herramientas instaladas
```

### 🧪 Pruebas
```bash
make test           # Ejecuta todas las pruebas
make test-sast      # Prueba específica de SAST
make test-unit      # Pruebas unitarias
```

### 🚀 Ejecución
```bash
make run            # Ejecuta SAST en directorio actual
make lint           # Ejecuta linters
make format         # Formatea código automáticamente
```

### 🧹 Mantenimiento
```bash
make clean          # Limpia archivos temporales
make clean-reports  # Limpia reportes
make distclean      # Limpieza completa (incluye venv)
```

## 📊 Formatos de Salida

### SAST Orchestrator (JSON Moderno)
```json
{
  "metadata": {
    "project": "test-driven-hardening",
    "scan_id": "20240115_143022",
    "tools_used": ["semgrep", "bandit"],
    "total_issues": 12
  },
  "statistics": {
    "total_files": 45,
    "issues_by_severity": {
      "CRITICAL": 2,
      "HIGH": 3,
      "MEDIUM": 7
    }
  }
}
```

### GitHub Analyzer (JSON Tradicional)
```json
{
  "repository": "torvalds/linux",
  "analysis_date": "2024-01-15",
  "languages": ["C", "Python"],
  "vulnerabilities": [...]
}
```

## 🔍 Qué Detecta Cada Sistema

### SAST Orchestrator (Herramientas Especializadas)
- **semgrep**: 1000+ reglas comunitarias para múltiples lenguajes
- **bandit**: Vulnerabilidades específicas de Python
- **cppcheck**: Análisis estático profundo para C/C++
- **safety**: Dependencias Python vulnerables
- **flawfinder**: Fallos de seguridad en C/C++

### GitHub Analyzer (AST Tradicional)
- **Python**: `eval()`, `exec()`, `subprocess`, credenciales hardcodeadas
- **C/C++**: `strcpy()`, `gets()`, `system()`, memory leaks
- **Path traversal**: `../`, rutas relativas
- **Inyecciones**: comandos, SQL (básico)

## 🎨 Integración CI/CD

### Para el Nuevo SAST Orchestrator
```yaml
# GitHub Actions
- name: Run TDH SAST Scan
  run: |
    cd engine-prototype
    make ci-setup
    make run
```

### Para el GitHub Analyzer Tradicional
```yaml
# GitHub Actions
- name: Run GitHub Analyzer
  run: |
    pip install -r engine-prototype/requirements.txt
    python engine-prototype/github_analyzer.py analyze ${{ github.repository }} --output json
```

## 🔧 Solución de Problemas

### Problemas Comunes del SAST Orchestrator
```bash
# Error: No module named 'yaml'
make setup  # Reinstala dependencias

# Error: Herramienta no encontrada
make install-tools  # Instala herramientas SAST

# Error: Entorno virtual no activado
source venv/bin/activate
```

### Problemas del GitHub Analyzer
```bash
# Error: ModuleNotFoundError
pip install -r requirements.txt

# Error: Repository not found
# Verifica que el repositorio existe y es público
```

## 🚀 Roadmap y Evolución

### Evolución del Proyecto
1. **Fase 1**: `github_analyzer.py` (AST tradicional) ✅
2. **Fase 2**: `SASTOrchestrator` (herramientas SAST) 🚧 En desarrollo
3. **Fase 3**: Integración LLM para fixes automáticos ⏳ Próximo
4. **Fase 4**: Dashboard web y API REST ⏳ Futuro

### Compatibilidad
- **El nuevo sistema NO reemplaza** inmediatamente el antiguo
- **Ambos pueden coexistir** durante la transición
- **Se recomienda migrar** al nuevo sistema para proyectos nuevos
- **El sistema tradicional** se mantendrá para compatibilidad

## 📚 Recursos Adicionales

### Para el Nuevo Sistema SAST
- [Configuración SAST](config/sast_tools.yaml) - Configuración de herramientas
- [SAST Orchestrator](src/core/sast_orchestrator.py) - Código principal
- [Scripts de prueba](scripts/) - Ejemplos de uso

### Para el Sistema Tradicional
- [GitHub Analyzer](github_analyzer.py) - Script principal
- [Ejemplos de uso](#) en el README original
- [Documentación AST] en comentarios del código

## 🤝 Contribuir

### Desarrollo del SAST Orchestrator
```bash
# 1. Clona y configura
git clone https://github.com/alonsoir/test-driven-hardening.git
cd test-driven-hardening/engine-prototype
make init

# 2. Desarrolla nuevas funcionalidades
# 3. Ejecuta pruebas
make test

# 4. Envía PR
```

### Mejoras al GitHub Analyzer
- El código está en `github_analyzer.py`
- Usa issues para reportar bugs
- PRs son bienvenidos para mejoras de compatibilidad

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **University of Extremadura** por la investigación académica
- **Comunidad Open Source** por herramientas como semgrep, bandit, cppcheck
- **GitHub** por la API y repositorios públicos
- **Contribuidores** que hacen posible este proyecto

---

**¿Preguntas o problemas?** 
- 📖 Consulta la [Wiki](https://github.com/alonsoir/test-driven-hardening/wiki)
- 🐛 Reporta [Issues](https://github.com/alonsoir/test-driven-hardening/issues)
- 💬 Únete a [Discussions](https://github.com/alonsoir/test-driven-hardening/discussions)

**¿Te gusta el proyecto?** ⭐ Dale una estrella en GitHub para apoyar el desarrollo.