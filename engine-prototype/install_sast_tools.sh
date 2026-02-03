#!/bin/bash
echo "🔧 Instalando herramientas SAST para TDH Engine..."

# Actualizar pip
pip install --upgrade pip

# Herramientas multi-lenguaje
pip install semgrep bandit safety

# Herramientas C/C++ (algunas necesitan instalación del sistema)
echo "Instalando herramientas de sistema para C/C++..."

# Para macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install cppcheck flawfinder clang-tidy
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Para Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y cppcheck flawfinder clang-tidy
fi

# Herramientas Java (necesitan Java Runtime)
echo "Instalando herramientas para Java..."
pip install spotbugs

# Herramientas JavaScript
pip install eslint

# Verificar instalación
echo ""
echo "✅ Herramientas instaladas:"
which cppcheck && cppcheck --version
which flawfinder && flawfinder --version
which semgrep && semgrep --version
which bandit && bandit --version
