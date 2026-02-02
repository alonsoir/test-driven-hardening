#!/bin/bash
# Script de limpieza para engine-prototype

echo "🧹 Limpiando engine-prototype..."

# Archivos a eliminar
patterns=(
    "tdh_report_*.json"
    "tdh_*.py"
    "test_*.sh"
    "fix_*.py"
    "pyproject.toml"
    "setup.py"
    "install.sh"
)

for pattern in "${patterns[@]}"; do
    if ls $pattern 1>/dev/null 2>&1; then
        echo "Eliminando $pattern"
        rm -f $pattern
    fi
done

# Directorios a limpiar (opcional)
if [ "$1" == "--all" ]; then
    dirs=("__pycache__" "src" "config" "knowledge_base" "examples" "tests" "logs")
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "Eliminando directorio $dir/"
            rm -rf "$dir"
        fi
    done
fi

# Verificar requirements
if [ -f "requirements_github.txt" ] && [ ! -f "requirements.txt" ]; then
    echo "📦 Renombrando requirements_github.txt a requirements.txt"
    mv requirements_github.txt requirements.txt
fi

echo "✅ Limpieza completada"
echo ""
echo "Estructura actual:"
ls -la
