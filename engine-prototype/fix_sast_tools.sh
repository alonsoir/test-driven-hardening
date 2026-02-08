#!/bin/bash
# engine-prototype/fix_sast_tools.sh

echo "🔧 Verificando y corrigiendo herramientas SAST..."

# Verificar Python virtual env
if [ ! -d "venv" ]; then
    echo "❌ No se encontró entorno virtual. Ejecuta: make setup"
    exit 1
fi

source venv/bin/activate

# Verificar e instalar herramientas Python
echo "📦 Verificando herramientas Python..."
for tool in bandit semgrep; do
    if ! python -c "import $tool" 2>/dev/null; then
        echo "Instalando $tool..."
        pip install $tool
    else
        echo "✅ $tool está instalado"
    fi
done

# Verificar e instalar herramientas del sistema (macOS)
echo "🔧 Verificando herramientas del sistema..."
if ! command -v cppcheck &> /dev/null; then
    echo "Instalando cppcheck..."
    brew install cppcheck
else
    echo "✅ cppcheck está instalado"
fi

if ! command -v flawfinder &> /dev/null; then
    echo "Instalando flawfinder..."
    brew install flawfinder
else
    echo "✅ flawfinder está instalado"
fi

# Corregir importación en sast_pipeline.py
echo "📝 Corrigiendo importación en sast_pipeline.py..."
SAST_FILE="src/core/sast_pipeline.py"
if grep -q "import tempfile" "$SAST_FILE"; then
    echo "✅ tempfile ya está importado"
else
    # Agregar después de las otras importaciones
    sed -i '' '/import asyncio/a\
import tempfile' "$SAST_FILE"
    echo "✅ Importación de tempfile agregada"
fi

echo ""
echo "🎉 Correcciones completadas!"
echo "Prueba de nuevo con:"
echo "python tdh_unified.py sast-real https://github.com/alonsoir/test-zeromq-c-.git"