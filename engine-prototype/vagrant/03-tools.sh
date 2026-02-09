#!/bin/bash
set -e

echo "🔧 Instalando herramientas SAST y de desarrollo..."

# 1. Herramientas de sistema y dependencias base
echo "📦 Instalando herramientas de sistema..."
apt-get update -qq

# Instalar herramientas en categorías para mejor manejo
BASE_TOOLS=(
    # Herramientas de desarrollo
    build-essential cmake ninja-build
    # Herramientas C/C++ SAST  
    cppcheck flawfinder clang-tidy clang-format
    # Python
    python3-pip python3-venv python3-dev python3-full
    # Herramientas de red y sistema
    net-tools iputils-ping curl wget git gnupg lsb-release ca-certificates
    # Utilitarios
    jq tree unzip htop vim tmux rsync
)

apt-get install -y -qq "${BASE_TOOLS[@]}"

# 2. Node.js (necesario para algunas herramientas SAST)
echo "📦 Instalando Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y -qq nodejs
    echo "  ✅ Node.js $(node --version) instalado"
else
    echo "  ⏩ Node.js ya instalado: $(node --version)"
fi

# 3. Herramientas SAST Python (instalación global para disponibilidad inmediata)
echo "🛡️ Instalando herramientas SAST Python..."
PYTHON_TOOLS=(
    bandit
    semgrep
    safety
    pylint
    flake8
    mypy
    pip-audit
    checkov
    trufflehog
    docker
    yamllint
)

pip3 install --quiet --no-cache-dir "${PYTHON_TOOLS[@]}"

# 4. Herramientas SAST binarias
echo "📥 Instalando herramientas SAST binarias..."

# Trivy - escáner de vulnerabilidades
if ! command -v trivy &> /dev/null; then
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
        | sh -s -- -b /usr/local/bin
    echo "  ✅ Trivy instalado"
fi

# Hadolint - linting de Dockerfiles
if ! command -v hadolint &> /dev/null; then
    curl -fsSL -o /usr/local/bin/hadolint \
        https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
    chmod +x /usr/local/bin/hadolint
    echo "  ✅ Hadolint instalado"
fi

# Gitleaks - detección de secretos
if ! command -v gitleaks &> /dev/null; then
    GITLEAKS_VERSION="8.18.1"
    curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
        | tar -xz -C /usr/local/bin gitleaks
    chmod +x /usr/local/bin/gitleaks
    echo "  ✅ Gitleaks v${GITLEAKS_VERSION} instalado"
fi

# 5. Herramientas adicionales útiles
echo "🧰 Instalando herramientas adicionales..."

# yq - procesador YAML
if ! command -v yq &> /dev/null; then
    curl -fsSL https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 \
        -o /usr/local/bin/yq
    chmod +x /usr/local/bin/yq
    echo "  ✅ yq instalado"
fi

# bat - cat mejorado
if ! command -v bat &> /dev/null; then
    BAT_VERSION="0.24.0"
    curl -fsSL "https://github.com/sharkdp/bat/releases/download/v${BAT_VERSION}/bat-v${BAT_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
        | tar -xz --strip-components=1 -C /usr/local/bin "bat-v${BAT_VERSION}-x86_64-unknown-linux-musl/bat"
    echo "  ✅ bat v${BAT_VERSION} instalado"
fi

# fd - find mejorado  
if ! command -v fd &> /dev/null; then
    FD_VERSION="8.7.1"
    curl -fsSL "https://github.com/sharkdp/fd/releases/download/v${FD_VERSION}/fd-v${FD_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
        | tar -xz --strip-components=1 -C /usr/local/bin "fd-v${FD_VERSION}-x86_64-unknown-linux-musl/fd"
    echo "  ✅ fd v${FD_VERSION} instalado"
fi

# 6. Instalar herramientas de desarrollo adicionales
echo "⚙️ Instalando herramientas de desarrollo adicionales..."
DEV_TOOLS=(
    # Para análisis de código C/C++
    libc6-dev gcc-multilib g++-multilib
    # Para análisis de binarios
    binutils file
    # Para análisis de redes
    netcat-openbsd tcpdump
)

apt-get install -y -qq "${DEV_TOOLS[@]}"

# 7. Verificación final
echo "✅ Verificando instalaciones..."

declare -A TOOLS
TOOLS=(
    ["cppcheck"]="cppcheck --version"
    ["flawfinder"]="flawfinder --version"
    ["clang-tidy"]="clang-tidy --version"
    ["semgrep"]="semgrep --version | head -1"
    ["bandit"]="bandit --version"
    ["trivy"]="trivy --version | head -1"
    ["hadolint"]="hadolint --version | head -1"
    ["gitleaks"]="gitleaks version"
    ["checkov"]="checkov --version"
    ["node"]="node --version"
    ["npm"]="npm --version"
)

echo ""
echo "📊 RESUMEN DE HERRAMIENTAS INSTALADAS:"
echo "======================================"

for tool in "${!TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        version=$(${TOOLS[$tool]} 2>/dev/null | head -1)
        echo "  ✅ $tool: ${version:-'Disponible'}"
    else
        echo "  ❌ $tool: No instalado"
    fi
done

# Verificar Python tools
echo ""
echo "🐍 HERRAMIENTAS PYTHON INSTALADAS:"
echo "=================================="
PYTHON_TOOLS_LIST=("bandit" "semgrep" "safety" "pylint" "checkov" "trufflehog")
for tool in "${PYTHON_TOOLS_LIST[@]}"; do
    if python3 -c "import $tool" 2>/dev/null; then
        echo "  ✅ $tool: Disponible"
    else
        echo "  ❌ $tool: No disponible"
    fi
done

# 8. Configurar alias útiles
echo ""
echo "🎨 Configurando alias útiles..."
cat << 'EOF' >> /home/vagrant/.bash_aliases

# Alias para herramientas SAST
alias sast-scan='echo "Herramientas disponibles: semgrep, bandit, trivy, hadolint, gitleaks"'
alias semgrep-scan='semgrep scan --config auto'
alias bandit-scan='bandit -r .'
alias trivy-scan='trivy fs .'
alias hadolint-scan='hadolint Dockerfile'

# Alias para desarrollo
alias ll='ls -la'
alias lh='ls -lah'
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

# Alias para Docker
alias docker-clean='docker system prune -af --volumes'
alias docker-stats='docker stats --no-stream'
alias docker-ls='docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Alias para git
alias gs='git status'
alias gl='git log --oneline --graph --decorate'
alias gaa='git add -A'
EOF

# Aplicar alias inmediatamente
if [ -f /home/vagrant/.bash_aliases ]; then
    source /home/vagrant/.bash_aliases
fi

echo ""
echo "🎉 TODAS LAS HERRAMIENTAS SAST INSTALADAS Y CONFIGURADAS"
echo "💡 Usa 'sast-scan' para ver los comandos disponibles"