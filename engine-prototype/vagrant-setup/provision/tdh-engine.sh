#!/bin/bash
# provision/tdh-engine.sh
echo "🔧 Configurando TDH Engine..."

cd /home/vagrant/tdh-engine

# Python 3.11 (más estable que 3.13)
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Instalar herramientas SAST del sistema
sudo apt-get install -y \
    cppcheck \
    flawfinder \
    clang \
    clang-tools

echo "✅ TDH Engine configurado"
echo ""
echo "📋 Comandos disponibles:"
echo "  cd /home/vagrant/tdh-engine"
echo "  source venv/bin/activate"
echo "  make build-base"
echo "  make test"