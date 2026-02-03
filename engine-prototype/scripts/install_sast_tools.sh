# engine-prototype/scripts/install_sast_tools.sh
#!/bin/bash

set -e  # Detener en caso de error

echo "🔧 Instalando herramientas SAST para TDH Engine..."

# Verificar sistema operativo
echo "🖥️  Sistema: $(uname -s)"

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Herramientas Python (instalar con pip)
echo "🐍 Instalando herramientas Python..."
if command_exists pip3; then
    pip3 install --upgrade pip
    pip3 install semgrep bandit safety PyYAML xmltodict rich tabulate
    echo "✅ Herramientas Python instaladas"
else
    echo "❌ pip3 no encontrado. Instala Python 3 y pip."
    exit 1
fi

# 2. Herramientas C/C++
echo "🔨 Instalando herramientas C/C++..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command_exists brew; then
        echo "📦 Usando Homebrew..."
        brew install cppcheck
        
        # Intentar instalar flawfinder
        if brew list flawfinder &>/dev/null; then
            echo "✅ flawfinder ya instalado"
        else
            brew install flawfinder || echo "⚠️  No se pudo instalar flawfinder"
        fi
        
        # Intentar instalar clang-tidy
        if brew list llvm &>/dev/null; then
            echo "✅ llvm/clang-tidy ya instalado"
        else
            brew install llvm || echo "⚠️  No se pudo instalar llvm (clang-tidy)"
        fi
    else
        echo "⚠️  Homebrew no instalado. Instala manualmente:"
        echo "   brew install cppcheck flawfinder llvm"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command_exists apt; then
        echo "📦 Usando apt..."
        sudo apt update
        sudo apt install -y cppcheck flawfinder clang-tidy
    elif command_exists yum; then
        echo "📦 Usando yum..."
        sudo yum install -y cppcheck flawfinder clang-tidy
    else
        echo "⚠️  Gestor de paquetes no reconocido"
    fi
else
    echo "⚠️  Sistema operativo no soportado: $OSTYPE"
fi

# 3. Herramientas JavaScript (Node.js/npm)
echo "📜 Instalando herramientas JavaScript..."
if command_exists npm; then
    npm install -g eslint
    echo "✅ eslint instalado globalmente"
    
    # También instalar el paquete Python para interfaz
    pip3 install python-eslint || echo "⚠️  No se pudo instalar python-eslint"
else
    echo "⚠️  npm no encontrado. ESLint no se instalará."
    echo "   Instala Node.js desde: https://nodejs.org/"
fi

# 4. Herramientas Java (SpotBugs)
echo "☕ Instalando herramientas Java..."
if command_exists java; then
    echo "✅ Java está instalado"
    
    # SpotBugs se instala desde su sitio web o con gestores de paquetes
    if [[ "$OSTYPE" == "darwin"* ]] && command_exists brew; then
        brew install spotbugs || echo "⚠️  No se pudo instalar spotbugs"
    elif [[ "$OSTYPE" == "linux-gnu"* ]] && command_exists apt; then
        sudo apt install -y spotbugs || echo "⚠️  No se pudo instalar spotbugs"
    else
        echo "ℹ️  Para instalar SpotBugs manualmente:"
        echo "   Descarga de: https://spotbugs.github.io/"
    fi
else
    echo "⚠️  Java no encontrado. SpotBugs no se instalará."
fi

# 5. Verificar instalaciones
echo ""
echo "✅ Verificación de instalación:"
echo "=========================================="

# Lista de herramientas a verificar
declare -A tools
tools=(
    ["semgrep"]="semgrep --version"
    ["bandit"]="bandit --version"
    ["cppcheck"]="cppcheck --version"
    ["flawfinder"]="flawfinder --version"
    ["eslint"]="eslint --version"
    ["spotbugs"]="spotbugs --version 2>/dev/null || echo 'SpotBugs no encontrado'"
)

for tool in "${!tools[@]}"; do
    if command_exists "$tool"; then
        echo "✅ $tool instalado"
    else
        echo "❌ $tool NO instalado"
    fi
done

# Verificar pip packages
echo ""
echo "📦 Paquetes Python instalados:"
pip3 list --format=columns | grep -E "(semgrep|bandit|safety|PyYAML|xmltodict|rich)"

echo ""
echo "🎉 Instalación completada."
echo "💡 Ejecuta 'source venv/bin/activate' si estás usando un entorno virtual."