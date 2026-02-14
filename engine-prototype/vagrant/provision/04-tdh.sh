#!/bin/bash
set -e

echo "🚀 Configurando TDH Engine dentro de la VM..."

# Crear entorno virtual FUERA de la carpeta compartida
echo "🐍 Creando entorno virtual Python en /home/vagrant/tdh-venv..."
python3 -m venv /home/vagrant/tdh-venv
source /home/vagrant/tdh-venv/bin/activate

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --quiet --upgrade pip

# Instalar dependencias del proyecto (desde la carpeta compartida)
echo "📚 Instalando dependencias Python..."
cd /home/vagrant/tdh-engine
if [ -f "requirements.txt" ]; then
    pip install --quiet -r requirements.txt
fi

# Instalar dependencias de desarrollo
echo "🔧 Instalando dependencias de desarrollo..."
pip install --quiet pytest pytest-cov black flake8 mypy

# Instalar el propio TDH Engine en modo desarrollo (si existe setup.py)
if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    echo "⚙️ Instalando TDH Engine en modo desarrollo..."
    pip install --quiet -e .
fi

# Configurar permisos Docker
echo "🔓 Configurando permisos Docker..."
sudo chmod a+rw /var/run/docker.sock

# Construir imagen base TDH
echo "🔨 Construyendo imagen Docker base para TDH..."
if [ -f "docker/Dockerfile.base" ]; then
    docker build -t tdh-base:latest -f docker/Dockerfile.base .
    echo "✅ Imagen tdh-base construida"
else
    echo "⚠️  docker/Dockerfile.base no encontrado, omite construcción"
fi

# Verificar Docker SDK
echo "🧪 Verificando integración Docker Python..."
python3 -c "import docker; client = docker.from_env(); print('✅ Docker SDK conectado:', client.ping())" || {
    sudo systemctl restart docker
    sleep 2
    python3 -c "import docker; client = docker.from_env(); print('✅ Docker SDK ahora funciona:', client.ping())"
}

# Crear directorios necesarios dentro del proyecto (logs, reports, etc.)
mkdir -p /home/vagrant/tdh-engine/{reports,logs,data}

# Configurar bashrc con alias que usen el nuevo venv
echo "🎨 Configurando entorno de desarrollo..."
cat << 'EOF' >> /home/vagrant/.bashrc

# TDH Engine aliases (usando venv en /home/vagrant/tdh-venv)
alias tdh-activate="source /home/vagrant/tdh-venv/bin/activate"
alias tdh-run="cd /home/vagrant/tdh-engine && source /home/vagrant/tdh-venv/bin/activate && python tdh_unified.py"
alias tdh-test="cd /home/vagrant/tdh-engine && source /home/vagrant/tdh-venv/bin/activate && pytest -v"
alias tdh-logs="tail -f /home/vagrant/tdh-engine/logs/*.log"

# Docker aliases
alias docker-clean="docker system prune -af --volumes"
alias docker-stats="docker stats --no-stream"
alias docker-list="docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Quick navigation
alias cd-tdh="cd /home/vagrant/tdh-engine"
alias ll="ls -la"
EOF

echo "
🎉 TDH Engine configurado exitosamente!

Comandos disponibles:
  tdh-activate   - Activar entorno virtual (fuera de carpeta compartida)
  tdh-run        - Ejecutar TDH Engine
  tdh-test       - Ejecutar tests
  cd-tdh         - Cambiar al directorio del proyecto

Ubicación del proyecto: /home/vagrant/tdh-engine
Entorno virtual: /home/vagrant/tdh-venv

Prueba rápida:
  source /home/vagrant/tdh-venv/bin/activate
  python -c \"import docker; print('Docker SDK:', docker.from_env().ping())\"
"