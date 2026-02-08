#!/bin/bash
# provision/docker.sh
echo "🐳 Instalando Docker nativo en Linux..."

# Instalar Docker oficial
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configurar usuario
sudo usermod -aG docker vagrant

# Habilitar e iniciar
sudo systemctl enable docker
sudo systemctl start docker

echo "✅ Docker instalado: $(docker --version)"
echo "✅ Docker Compose: $(docker-compose --version)"