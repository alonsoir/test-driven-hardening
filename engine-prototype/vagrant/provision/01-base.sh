#!/bin/bash
# 01-base.sh
set -e

echo "🔄 Actualizando sistema base..."
export DEBIAN_FRONTEND=noninteractive

# Actualizar repositorios
apt-get update -qq

# Instalar herramientas esenciales
apt-get install -y -qq \
  build-essential \
  curl \
  wget \
  git \
  vim \
  htop \
  tmux \
  tree \
  jq \
  unzip \
  software-properties-common \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release \
  net-tools \
  iputils-ping \
  python3-pip \
  python3-venv \
  python3-dev \
  python3-full

# Configurar python3 como python por defecto
update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Limpiar caché
apt-get autoremove -y -qq
apt-get clean -qq

echo "✅ Sistema base configurado"