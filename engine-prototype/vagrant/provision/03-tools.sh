#!/bin/bash
# 03-tools.sh
set -e

echo "🔧 Instalando herramientas SAST y de desarrollo..."

# 1. Instalar Node.js para algunas herramientas SAST
echo "📦 Instalando Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y -qq nodejs

# 2. Instalar herramientas SAST globales
echo "🛡️ Instalando herramientas SAST..."

# Semgrep
python3 -m pip install --quiet semgrep

# Bandit
python3 -m pip install --quiet bandit

# Safety
python3 -m pip install --quiet safety

# Trivy
echo "📥 Instalando Trivy..."
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | \
  sh -s -- -b /usr/local/bin

# Hadolint
echo "📥 Instalando Hadolint..."
curl -fsSL -o /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
chmod +x /usr/local/bin/hadolint

# Gitleaks
echo "📥 Instalando Gitleaks..."
curl -fsSL https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz | \
  tar -xz -C /usr/local/bin
chmod +x /usr/local/bin/gitleaks

# Checkov
echo "📥 Instalando Checkov..."
python3 -m pip install --quiet checkov

# TruffleHog
echo "📥 Instalando TruffleHog..."
python3 -m pip install --quiet trufflehog

# 3. Instalar herramientas adicionales útiles
echo "🧰 Instalando herramientas adicionales..."

# yq (YAML processor)
curl -fsSL https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -o /usr/local/bin/yq
chmod +x /usr/local/bin/yq

# bat (cat mejorado)
curl -fsSL https://github.com/sharkdp/bat/releases/download/v0.24.0/bat-v0.24.0-x86_64-unknown-linux-musl.tar.gz | \
  tar -xz --strip-components=1 -C /usr/local/bin bat-v0.24.0-x86_64-unknown-linux-musl/bat

# fd (find mejorado)
curl -fsSL https://github.com/sharkdp/fd/releases/download/v8.7.1/fd-v8.7.1-x86_64-unknown-linux-musl.tar.gz | \
  tar -xz --strip-components=1 -C /usr/local/bin fd-v8.7.1-x86_64-unknown-linux-musl/fd

# Instalar herramientas NFS
echo "🔧 Instalando soporte NFS..."
apt-get install -y nfs-common nfs-kernel-server

# 4. Verificar instalaciones
echo "✅ Herramientas instaladas:"
echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"
echo "  - Semgrep: $(semgrep --version | head -1)"
echo "  - Trivy: $(trivy --version | head -1)"
echo "  - Hadolint: $(hadolint --version | head -1)"
echo "  - Checkov: $(checkov --version | head -1)"

echo "🎉 Todas las herramientas SAST instaladas"