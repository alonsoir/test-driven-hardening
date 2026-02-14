#!/bin/bash
# example-run.sh
# Ejemplo de cómo ejecutar TDH Engine dentro de la VM

set -e

echo "🎪 EJEMPLO TDH ENGINE - VM Vagrant"
echo "=================================="

# Verificar que estamos en la VM
if [ ! -d "/home/vagrant" ]; then
    echo "❌ Este script debe ejecutarse dentro de la VM Vagrant"
    echo "   Usa: vagrant ssh"
    echo "   Luego: cd /home/vagrant/tdh-engine"
    echo "   Luego: ./example-run.sh"
    exit 1
fi

# Cambiar al directorio del proyecto
cd /home/vagrant/tdh-engine

# 1. Activar entorno virtual
echo "🐍 Activando entorno virtual..."
source venv/bin/activate

# 2. Verificar Docker
echo "🐳 Verificando Docker..."
python -c "import docker; client = docker.from_env(); print('✅ Docker SDK conectado:', client.ping())"

# 3. Verificar imagen base
echo "📦 Verificando imagen tdh-base..."
if ! docker images | grep -q tdh-base; then
    echo "⚠️  Imagen tdh-base no encontrada, construyendo..."
    make build-base
fi

# 4. Mostrar herramientas disponibles
echo "🛠️  Herramientas SAST disponibles:"
for tool in semgrep bandit trivy hadolint; do
    if command -v $tool >/dev/null 2>&1; then
        echo "  ✅ $tool"
    else
        echo "  ❌ $tool"
    fi
done

# 5. Ejecutar análisis de ejemplo
echo ""
echo "🚀 EJECUTANDO ANÁLISIS DE PRUEBA"
echo "Repositorio: https://github.com/alonsoir/test-zeromq-c-.git"
echo ""

python tdh_unified.py sast-orchestrated https://github.com/alonsoir/test-zeromq-c-.git

# 6. Mostrar resultados
echo ""
echo "📊 RESULTADOS:"
echo "Reportes guardados en: ./reports/"
ls -la reports/ 2>/dev/null || echo "No hay reportes aún"

echo ""
echo "✅ Ejemplo completado. ¡TDH Engine funciona en Vagrant! 🎉"