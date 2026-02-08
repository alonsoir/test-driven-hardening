#!/bin/bash
# provision/base.sh
echo "🚀 Actualizando sistema base..."
sudo apt-get update
sudo apt-get upgrade -y

# Herramientas esenciales
sudo apt-get install -y \
    git \
    curl \
    wget \
    htop \
    tmux \
    vim \
    build-essential \
    software-properties-common