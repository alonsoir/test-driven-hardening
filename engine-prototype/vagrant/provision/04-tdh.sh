#!/bin/bash
set -e

echo "🚀 Configurando TDH Engine dentro de la VM..."

# Cambiar al directorio del proyecto
cd /home/vagrant/tdh-engine

# 1. Crear entorno virtual Python
echo "🐍 Creando entorno virtual Python..."
python3 -m venv venv
source venv/bin/activate

# 2. Actualizar pip
echo "📦 Actualizando pip..."
pip install --quiet --upgrade pip

# 3. Instalar dependencias del proyecto
echo "📚 Instalando dependencias Python..."
if [ -f "requirements.txt" ]; then
    pip install --quiet -r requirements.txt
fi

# 4. Instalar dependencias de desarrollo
echo "🔧 Instalando dependencias de desarrollo..."
pip install --quiet pytest pytest-cov black flake8 mypy

# 5. Instalar el propio TDH Engine en modo desarrollo
echo "⚙️ Instalando TDH Engine en modo desarrollo..."
if [ -f "setup.py" ]; then
    pip install --quiet -e .
elif [ -f "pyproject.toml" ]; then
    pip install --quiet -e .
fi

# 6. Configurar permisos Docker para el usuario vagrant (en esta sesión)
echo "🔓 Configurando permisos Docker en tiempo real..."
# Esto soluciona el problema de tener que reiniciar sesión
sudo chmod a+rw /var/run/docker.sock

# 6.5 Construir imagen base TDH \
echo "🔨 Construyendo imagen Docker base para TDH..." 
cd /home/vagrant/tdh-engine 
if [ -f "docker/Dockerfile.base" ]; then 
    echo "📦 Construyendo tdh-base:latest desde docker/Dockerfile.base..." 
    docker build -t tdh-base:latest -f docker/Dockerfile.base . 
    echo "✅ Imagen tdh-base construida exitosamente" 
else 
    echo "❌ No se encontró docker/Dockerfile.base" 
    echo "⚠️  Necesitas construir manualmente: docker build -t tdh-base:latest -f docker/Dockerfile.base ." 
fi 

# 7. Verificar que Docker funciona con el SDK de Python
echo "🧪 Verificando integración Docker Python..."
if python3 -c "import docker; client = docker.from_env(); print('✅ Docker SDK conectado:', client.ping())"; then
    echo "🎉 ¡INTEGRACIÓN DOCKER-PYTHON FUNCIONA!"
else
    echo "⚠️  Problema con Docker SDK. Solucionando..."
    # Forzar reinicio del socket
    sudo systemctl restart docker
    sleep 2
    python3 -c "import docker; client = docker.from_env(); print('✅ Docker SDK ahora funciona:', client.ping())"
fi

# 8. Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p {reports,logs,data}

# 9. Crear alias útiles
echo "🎨 Configurando entorno de desarrollo..."
cat << 'EOF' >> /home/vagrant/.bashrc

# TDH Engine aliases
alias tdh-activate="cd /home/vagrant/tdh-engine && source venv/bin/activate"
alias tdh-run="cd /home/vagrant/tdh-engine && source venv/bin/activate && python tdh_unified.py"
alias tdh-test="cd /home/vagrant/tdh-engine && source venv/bin/activate && pytest -v"
alias tdh-logs="tail -f /home/vagrant/tdh-engine/logs/*.log"

# Docker aliases
alias docker-clean="docker system prune -af --volumes"
alias docker-stats="docker stats --no-stream"
alias docker-list="docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Quick navigation
alias cd-tdh="cd /home/vagrant/tdh-engine"
alias ll="ls -la"
EOF

# 10. Mensaje final
echo "
🎉 TDH Engine configurado exitosamente!

Comandos disponibles:
  tdh-activate   - Activar entorno virtual y cambiar al directorio
  tdh-run        - Ejecutar TDH Engine
  tdh-test       - Ejecutar tests
  cd-tdh         - Cambiar al directorio del proyecto

Ubicación del proyecto: /home/vagrant/tdh-engine
Entorno virtual: /home/vagrant/tdh-engine/venv

Prueba rápida:
  cd /home/vagrant/tdh-engine
  source venv/bin/activate
  python -c \"import docker; print('Docker SDK:', docker.from_env().ping())\"
"

echo "✅ TDH Engine completamente configurado"