# 🌐 GitHub Repository Analyzer

Analizador de repositorios GitHub que usa AST para detectar vulnerabilidades en código.

## 🚀 Características

- **Análisis AST** de Python y C/C++
- **Detección automática** de vulnerabilidades comunes (CWE-120, CWE-22, etc.)
- **Clonado automático** de repositorios GitHub
- **Múltiples formatos de salida**: texto, JSON, HTML
- **Cache local** para análisis repetidos
- **Detección de lenguajes** usados en el repositorio

## 📦 Instalación

```bash
# Clonar repositorio
git clone https://github.com/alonsoir/test-driven-hardening.git
cd test-driven-hardening/engine-prototype

# Crear entorno virtual (opcional)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

🎯 Uso Rápido

# Analizar un repositorio GitHub:

python github_analyzer.py analyze usuario/repositorio

# Ejemplos:
python github_analyzer.py analyze torvalds/linux --max-files 100
python github_analyzer.py analyze OWASP/CheatSheetSeries --output json
python github_analyzer.py analyze apple/swift --branch main
python github_analyzer.py analyze https://github.com/alonsoir/test-zeromq-c- --branch main

# Obtener información del repositorio:

python github_analyzer.py info usuario/repositorio
python github_analyzer.py info microsoft/vscode

# Analizar repositorio local:

python github_analyzer.py local /ruta/al/repositorio
python github_analyzer.py local /vagrant/ml-defender --output html

# Ver repositorios de seguridad populares:

python github_analyzer.py trending

📊 Formatos de Salida

--output text: Salida en consola con colores (por defecto)
--output json: JSON estructurado para automatización
--output html: Reporte HTML interactivo con gráficos
🔍 Qué Detecta

Python:

✅ Uso de eval(), exec(), compile()
✅ Imports peligrosos (pickle, marshal, subprocess)
✅ Credenciales hardcodeadas (password, secret, token)
✅ Path traversal (../, rutas relativas)
C/C++:

✅ Buffer overflows (strcpy(), gets(), sprintf())
✅ Command injection (system(), popen())
✅ Memory leaks (malloc() sin free())
✅ Use-after-free
✅ Path traversal
📈 Reporte HTML

Genera reportes interactivos con gráficos:

python github_analyzer.py analyze usuario/repositorio --output html > reporte.html

🔧 Dependencias

gitpython - Clonado de repositorios
requests - Peticiones HTTP
click - Interfaz de línea de comandos
rich - Salida formateada en consola
pygments - Resaltado de sintaxis

🏗️ Arquitectura

github_analyzer.py
├── GitHubRepositoryAnalyzer
│   ├── clone_repository()
│   ├── analyze_python_file()
│   ├── analyze_cpp_file()
│   └── generate_report()
├── CLI (Click)
│   ├── analyze
│   ├── info
│   ├── local
│   └── trending
└── Reporters
    ├── Text
    ├── JSON
    └── HTML

📁 Estructura del Proyecto

engine-prototype/
├── github_analyzer.py      # Script principal
├── requirements.txt        # Dependencias
├── README.md              # Esta documentación
├── .gitignore            # Archivos ignorados
└── venv/                 # Entorno virtual (opcional)

🔄 Ejemplos Prácticos

1. Análisis rápido:

# Analizar primeros 50 archivos del kernel de Linux
python github_analyzer.py analyze torvalds/linux --max-files 50

# Ver resultados en JSON
python github_analyzer.py analyze nodejs/node --max-files 100 --output json > node_analysis.json

2. Integración en CI/CD:

# Script para pipeline
python github_analyzer.py analyze $REPO_URL --output json > security_report.json

# Verificar si hay vulnerabilidades críticas
if grep -q '"severity": "CRITICAL"' security_report.json; then
    echo "❌ Vulnerabilidades críticas encontradas"
    exit 1
fi

3. Monitoreo periódico:

# Analizar repositorio cada semana
python github_analyzer.py analyze mi-org/mi-proyecto --output html > reporte_$(date +%Y%m%d).html

🐛 Solución de Problemas

Error: "ModuleNotFoundError: No module named 'git'"

pip install gitpython

Error: "Repository not found"

Verifica que el repositorio existe y es público
Usa formato usuario/repositorio o URL completa
El análisis es muy lento

Usa --max-files para limitar archivos
Usa --branch para analizar solo una rama
📈 Roadmap

Análisis de más lenguajes (Java, JavaScript, Go, Rust)
Integración con GitHub API (sin clonar)
Análisis de dependencias (npm, pip, cargo)
Machine Learning para detección avanzada
Dashboard web en tiempo real
🤝 Contribuir

Haz fork del repositorio
Crea una rama (git checkout -b feature/nueva-funcionalidad)
Haz commit de tus cambios (git commit -m 'Añadir nueva funcionalidad')
Push a la rama (git push origin feature/nueva-funcionalidad)
Abre un Pull Request
📄 Licencia

MIT License - Ver LICENSE para más detalles.

🙏 Agradecimientos

Test Driven Hardening - Filosofía de desarrollo
University of Extremadura - Investigación académica
GitHub - Por la API y repositorios públicos
¿Preguntas o problemas? Abre un issue en GitHub o contacta a @alonsoir


