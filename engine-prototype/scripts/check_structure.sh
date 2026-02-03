# engine-prototype/scripts/check_structure.sh
#!/bin/bash

echo "🔍 Verificando estructura del proyecto..."

# Verificar archivos esenciales
essential_files=(
    "config/tdh_config.yaml"
    "config/sast_tools.yaml"
    "src/core/sast_orchestrator.py"
    "src/core/config_validator.py"
    "scripts/test_sast.py"
    "README.md"
    "requirements.txt"
    "Makefile"
)

missing_files=0
for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (FALTANTE)"
        missing_files=$((missing_files + 1))
    fi
done

# Verificar archivos que NO deberían existir
unwanted_files=(
    "config/sast_tools_minimal.yaml"
    "config/sast_tools_quick.yaml"
    "config/sast_tools_robust.yaml"
    "src/core/llm_orchestrator.py"
    "test_semgrep.py"
    "setup.py"
    "run_sast.sh"
    "tdh"
    "dashboard/"
)

echo ""
echo "🔍 Verificando archivos no deseados..."

for file in "${unwanted_files[@]}"; do
    if [ -e "$file" ]; then
        echo "⚠️  $file (DEBERÍA ELIMINARSE)"
    fi
done

# Resumen
echo ""
echo "📊 RESUMEN:"
if [ $missing_files -eq 0 ]; then
    echo "✅ Estructura del proyecto OK"
else
    echo "❌ Faltan $missing_files archivos esenciales"
    exit 1
fi