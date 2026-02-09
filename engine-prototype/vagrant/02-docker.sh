#!/bin/bash
set -e

echo "🐳 INSTALANDO DOCKER NATIVO EN LINUX (la forma correcta)"

# 1. Eliminar instalaciones previas (si las hay)
echo "🔧 Limpiando instalaciones anteriores..."
apt-get remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
apt-get update -qq
apt-get install -y -qq \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# 3. Añadir clave GPG oficial de Docker sin requerir interacción
echo "🔑 Añadiendo clave GPG de Docker..."
mkdir -p /etc/apt/keyrings
# Descargar la clave y guardarla en un archivo temporal, luego procesarla con gpg en modo batch
curl -fsSL https://download.docker.com/linux/ubuntu/gpg > /tmp/docker.gpg
gpg --batch --dearmor -o /etc/apt/keyrings/docker.gpg /tmp/docker.gpg
rm -f /tmp/docker.gpg

# 4. Añadir repositorio oficial
echo "📁 Configurando repositorio Docker..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Instalar Docker Engine
echo "⚙️ Instalando Docker Engine..."
apt-get update -qq
apt-get install -y -qq \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-compose-plugin

# 6. Configurar Docker para usar sin sudo
echo "👤 Configurando permisos Docker..."
usermod -aG docker vagrant

# 7. Configurar daemon Docker
echo "⚙️ Configurando daemon Docker..."
mkdir -p /etc/docker
cat << EOF > /etc/docker/daemon.json
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF

# 8. Habilitar e iniciar Docker
echo "🚀 Iniciando servicio Docker..."
systemctl enable docker
systemctl start docker

# 9. Instalar Docker Compose standalone (por si acaso)
echo "📦 Instalando Docker Compose standalone..."
curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 10. Verificar instalación
echo "✅ Docker version: $(docker --version)"
echo "✅ Docker Compose version: $(docker compose version)"
echo "✅ Docker info - ServerVersion: $(docker info --format '{{.ServerVersion}}')"

# 11. Probar Docker
echo "🧪 Probando Docker..."
docker run --rm hello-world | grep -q "Hello from Docker!" && echo "✅ Docker funciona correctamente"

echo "🎉 DOCKER NATIVO INSTALADO Y CONFIGURADO - ¡ADIÓS DOCKER DESKTOP!"