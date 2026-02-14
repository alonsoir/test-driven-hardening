#!/bin/bash
# engine-prototype/setup.sh

echo "🔧 Configurando TDH Engine..."

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    echo "   Visita: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar herramientas del sistema
echo "📦 Verificando herramientas del sistema..."
TOOLS=("git" "python3" "pip3")
for tool in "${TOOLS[@]}"; do
    if ! command -v $tool &> /dev/null; then
        echo "❌ $tool no está instalado"
        exit 1
    fi
done

# Crear entorno virtual
echo "🐍 Creando entorno virtual Python..."
python3 -m venv venv

# Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p src/core src/llm_integration src/sast_integration src/utils
mkdir -p docker config tests results

# Crear __init__.py básico
touch src/core/__init__.py
touch src/llm_integration/__init__.py
touch src/sast_integration/__init__.py
touch src/utils/__init__.py

echo "✅ Configuración completada!"
echo ""
echo "📖 PRÓXIMOS PASOS:"
echo "1. Construir la imagen base Docker:"
echo "   make build-base"
echo ""
echo "2. Instalar herramientas SAST del sistema (Ubuntu/Debian):"
echo "   sudo apt-get install cppcheck flawfinder"
echo ""
echo "3. Ejecutar prueba completa:"
echo "   make test"
echo ""
echo "💡 NOTA: Algunas herramientas SAST (cppcheck, flawfinder) deben"
echo "   instalarse a nivel de sistema, no via pip."