# ============================================
# TDH ENGINE - MAKEFILE VAGRANT COMPATIBLE
# ============================================
# Este Makefile funciona tanto en HOST (macOS) como en GUEST (Vagrant VM)
# Los comandos detectan automáticamente el entorno
# ============================================

# Variables de entorno
VENV_PATH = venv
PYTHON = python3
PIP = pip3
DOCKER = docker
VAGRANT_DIR = vagrant
PROJECT_NAME = tdh-engine

# Detectar si estamos en VM Vagrant (por el directorio /home/vagrant)
ifneq ($(wildcard /home/vagrant/$(PROJECT_NAME)/.),)
	IS_VAGRANT = true
	PROJECT_ROOT = /home/vagrant/$(PROJECT_NAME)
else
	IS_VAGRANT = false
	PROJECT_ROOT = .
endif

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

# ============================================
# COMANDOS PRINCIPALES (funcionan en ambos entornos)
# ============================================

.PHONY: help setup setup-deps build-base test clean check install-aiofiles

help:
	@echo "$(BLUE)🤖 TDH ENGINE - COMANDOS DISPONIBLES$(NC)"
	@echo "$(GREEN)===========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)🏗️  CONFIGURACIÓN:$(NC)"
	@echo "  make setup           - Configura proyecto completo"
	@echo "  make setup-deps      - Instala dependencias Python"
	@echo "  make build-base      - Construye imagen Docker base"
	@echo ""
	@echo "$(YELLOW)🧪 PRUEBAS:$(NC)"
	@echo "  make test            - Ejecuta prueba completa"
	@echo "  make check           - Verifica dependencias"
	@echo ""
	@echo "$(YELLOW)🧹 MANTENIMIENTO:$(NC)"
	@echo "  make clean           - Limpia archivos temporales"
	@echo "  make install-aiofiles - Instala aiofiles solo"
	@echo ""
	@echo "$(YELLOW)🚀 VAGRANT (desde HOST macOS):$(NC)"
	@echo "  make vagrant-up      - Inicia/crea VM"
	@echo "  make vagrant-ssh     - Conecta a VM"
	@echo "  make vagrant-halt    - Detiene VM"
	@echo "  make vagrant-destroy - Destruye VM"
	@echo "  make vagrant-provision - Re-provisiona VM"
	@echo "  make vagrant-status  - Estado VM"
	@echo ""
	@echo "$(YELLOW)🔧 DESARROLLO EN VM:$(NC)"
	@echo "  make vm-setup        - Setup dentro de VM"
	@echo "  make vm-run          - Ejecuta TDH en VM"
	@echo "  make vm-example      - Ejecuta ejemplo en VM"
	@echo ""
	@echo "$(YELLOW)📊 INFORMACIÓN:$(NC)"
	@echo "  make env-info        - Muestra información del entorno"
	@echo "  make docker-info     - Muestra info Docker"
	@echo "  make list-tools      - Lista herramientas SAST"
	@echo ""
	@if [ "$(IS_VAGRANT)" = "true" ]; then \
		echo "$(GREEN)✅ Actualmente en VM Vagrant$(NC)"; \
		echo "  Directorio: $(PROJECT_ROOT)"; \
	else \
		echo "$(BLUE)💻 Actualmente en HOST$(NC)"; \
		echo "  Usa 'make vagrant-up' para iniciar VM"; \
	fi

setup: setup-deps
	@echo "$(BLUE)📁 Creando estructura de directorios...$(NC)"
	@mkdir -p src/{core,llm_integration,sast_integration,utils}
	@mkdir -p docker config tests results reports logs
	@touch src/core/__init__.py src/llm_integration/__init__.py src/sast_integration/__init__.py src/utils/__init__.py
	@echo "$(GREEN)✅ Configuración completada.$(NC)"

setup-deps:
	@echo "$(BLUE)🔧 Configurando entorno virtual y dependencias...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Creando entorno virtual..."; \
		$(PYTHON) -m venv $(VENV_PATH) || $(PYTHON) -m venv $(VENV_PATH) --system-site-packages; \
	fi
	@$(VENV_PATH)/bin/pip install --upgrade pip
	@if [ -f "requirements.txt" ]; then \
		$(VENV_PATH)/bin/pip install -r requirements.txt; \
	else \
		echo "$(YELLOW)⚠️  requirements.txt no encontrado, instalando dependencias básicas...$(NC)"; \
		$(VENV_PATH)/bin/pip install docker aiofiles asyncio; \
	fi
	@echo "$(GREEN)✅ Dependencias instaladas.$(NC)"

check:
	@echo "$(BLUE)🔍 Verificando dependencias...$(NC)"
	@if [ -f "check_deps.py" ]; then \
		$(VENV_PATH)/bin/python check_deps.py; \
	else \
		echo "$(YELLOW)⚠️  check_deps.py no encontrado, verificando manualmente...$(NC)"; \
		$(VENV_PATH)/bin/python -c "import docker; print('✅ Docker SDK:', docker.__version__)"; \
		$(VENV_PATH)/bin/python -c "import aiofiles; print('✅ aiofiles:', aiofiles.__version__)"; \
	fi

build-base:
	@echo "$(BLUE)🐳 Construyendo imagen base Docker...$(NC)"
	@if [ -f "docker/Dockerfile.base" ]; then \
		$(DOCKER) build -f docker/Dockerfile.base -t tdh-base:latest .; \
		echo "$(GREEN)✅ Imagen base construida.$(NC)"; \
		$(DOCKER) images | grep tdh-base; \
	elif [ -f "Dockerfile" ]; then \
		$(DOCKER) build -t tdh-base:latest .; \
		echo "$(GREEN)✅ Imagen base construida desde Dockerfile.$(NC)"; \
	else \
		echo "$(RED)❌ No se encontró Dockerfile.base ni Dockerfile$(NC)"; \
		exit 1; \
	fi

test:
	@echo "$(BLUE)🧪 Ejecutando prueba completa...$(NC)"
	@if [ -f "tdh_unified.py" ]; then \
		$(VENV_PATH)/bin/python tdh_unified.py test; \
	else \
		echo "$(RED)❌ tdh_unified.py no encontrado$(NC)"; \
	fi

clean:
	@echo "$(BLUE)🧹 Limpiando...$(NC)"
	@-$(VENV_PATH)/bin/python tdh_unified.py docker-cleanup 2>/dev/null || true
	@-rm -rf results/* test-results/* reports/* logs/*
	@-find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@-find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpieza completada.$(NC)"

install-aiofiles:
	@echo "$(BLUE)📦 Instalando aiofiles...$(NC)"
	@$(VENV_PATH)/bin/pip install "aiofiles>=23.2.0"
	@echo "$(GREEN)✅ aiofiles instalado.$(NC)"

# ============================================
# COMANDOS VAGRANT (ejecutar desde HOST macOS)
# ============================================

.PHONY: vagrant-up vagrant-ssh vagrant-halt vagrant-destroy vagrant-provision vagrant-status vagrant-rsync

vagrant-up:
	@echo "$(BLUE)🚀 Iniciando VM Vagrant...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant up
	@echo "$(GREEN)✅ VM lista. Usa 'make vagrant-ssh' para conectar.$(NC)"

vagrant-ssh:
	@echo "$(BLUE)🔌 Conectando a VM...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant ssh

vagrant-halt:
	@echo "$(BLUE)⏸️  Deteniendo VM...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant halt

vagrant-destroy:
	@echo "$(RED)💥 Destruyendo VM...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant destroy -f

vagrant-provision:
	@echo "$(BLUE)🔧 Re-provisionando VM...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant provision

vagrant-status:
	@echo "$(BLUE)📊 Estado VM...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant status

vagrant-rsync:
	@echo "$(BLUE)🔄 Sincronizando archivos...$(NC)"
	@cd $(VAGRANT_DIR) && vagrant rsync-reload

# ============================================
# COMANDOS PARA EJECUTAR DENTRO DE VM
# ============================================

.PHONY: vm-setup vm-run vm-example vm-test-full

vm-setup: setup-deps build-base
	@echo "$(GREEN)✅ VM completamente configurada.$(NC)"

vm-run:
	@echo "$(BLUE)🚀 Ejecutando TDH Engine...$(NC)"
	@echo "$(YELLOW)Ejemplo: make vm-example para un análisis completo$(NC)"
	@echo "Uso: python tdh_unified.py <comando> <argumentos>"
	@echo "Comandos disponibles:"
	@$(VENV_PATH)/bin/python tdh_unified.py --help

vm-example:
	@echo "$(BLUE)🎪 Ejecutando ejemplo completo en VM...$(NC)"
	@echo "$(YELLOW)Este comando debe ejecutarse DENTRO de la VM$(NC)"
	@if [ "$(IS_VAGRANT)" = "false" ]; then \
		echo "$(RED)❌ Este comando solo funciona dentro de la VM$(NC)"; \
		echo "  Usa: vagrant ssh"; \
		echo "  Luego: cd /home/vagrant/tdh-engine"; \
		echo "  Luego: make vm-example"; \
		exit 1; \
	fi
	@echo "$(GREEN)1. Activando entorno virtual...$(NC)"
	@source $(VENV_PATH)/bin/activate
	@echo "$(GREEN)2. Verificando Docker...$(NC)"
	@python -c "import docker; print('✅ Docker SDK:', docker.from_env().ping())"
	@echo "$(GREEN)3. Verificando imagen base...$(NC)"
	@if ! $(DOCKER) images | grep -q tdh-base; then \
		echo "$(YELLOW)⚠️  Imagen tdh-base no encontrada, construyendo...$(NC)"; \
		$(MAKE) build-base; \
	fi
	@echo "$(GREEN)4. Ejecutando análisis de prueba...$(NC)"
	@echo "$(YELLOW)Repositorio de prueba: https://github.com/alonsoir/test-zeromq-c-.git$(NC)"
	@python tdh_unified.py sast-orchestrated https://github.com/alonsoir/test-zeromq-c-.git || \
		echo "$(YELLOW)⚠️  Si falla, prueba primero: make build-base$(NC)"
	@echo "$(GREEN)5. Resultados en: ./reports/$(NC)"
	@ls -la reports/ 2>/dev/null || echo "$(YELLOW)No hay reportes aún$(NC)"

vm-test-full: build-base test
	@echo "$(GREEN)✅ Prueba completa ejecutada.$(NC)"

# ============================================
# COMANDOS DE INFORMACIÓN
# ============================================

.PHONY: env-info docker-info list-tools

env-info:
	@echo "$(BLUE)📊 INFORMACIÓN DEL ENTORNO$(NC)"
	@echo "=================================="
	@echo "Directorio actual: $(PWD)"
	@echo "En VM Vagrant: $(IS_VAGRANT)"
	@echo "Python: $(shell which python3)"
	@echo "Python version: $(shell python3 --version 2>/dev/null || echo 'No disponible')"
	@echo "Docker: $(shell which docker || echo 'No disponible')"
	@echo "Docker version: $(shell docker --version 2>/dev/null || echo 'No disponible')"
	@echo "Vagrant: $(shell which vagrant || echo 'No disponible')"
	@echo "VirtualBox: $(shell VBoxManage --version 2>/dev/null || echo 'No disponible')"
	@if [ "$(IS_VAGRANT)" = "true" ]; then \
		echo "💻 VM: Ubuntu 22.04 LTS"; \
		echo "🏠 Directorio proyecto: $(PROJECT_ROOT)"; \
	fi

docker-info:
	@echo "$(BLUE)🐳 INFORMACIÓN DOCKER$(NC)"
	@echo "========================="
	@$(DOCKER) --version 2>/dev/null || echo "$(RED)Docker no disponible$(NC)"
	@$(DOCKER) info --format '{{.ServerVersion}}' 2>/dev/null && \
		echo "$(GREEN)✅ Docker funcionando$(NC)" || \
		echo "$(RED)❌ Docker no responde$(NC)"
	@echo "Imágenes disponibles:"
	@$(DOCKER) images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -10

list-tools:
	@echo "$(BLUE)🛠️  HERRAMIENTAS SAST DISPONIBLES$(NC)"
	@echo "=================================="
	@for tool in semgrep bandit trivy hadolint gitleaks checkov cppcheck flawfinder; do \
		if command -v $$tool >/dev/null 2>&1; then \
			echo "✅ $$tool: $$($$tool --version 2>/dev/null | head -1 || echo 'Disponible')"; \
		else \
			echo "❌ $$tool: No disponible"; \
		fi; \
	done

# ============================================
# FLUJO DE TRABAJO COMPLETO
# ============================================

.PHONY: full-migration quick-start

full-migration:
	@echo "$(BLUE)🔄 MIGRACIÓN COMPLETA A VAGRANT$(NC)"
	@echo "======================================"
	@echo "1. Creando VM desde cero..."
	@$(MAKE) vagrant-destroy
	@$(MAKE) vagrant-up
	@echo ""
	@echo "2. Conectando a VM y configurando..."
	@echo "   Usa: make vagrant-ssh"
	@echo "   Luego dentro de VM:"
	@echo "   cd /home/vagrant/tdh-engine"
	@echo "   make vm-setup"
	@echo ""
	@echo "3. Para ejecutar ejemplo:"
	@echo "   make vm-example"
	@echo "$(GREEN)✅ Migración completa lista.$(NC)"

quick-start:
	@echo "$(BLUE)⚡ INICIO RÁPIDO$(NC)"
	@echo "======================"
	@if [ "$(IS_VAGRANT)" = "true" ]; then \
		echo "$(GREEN)Ya estás en la VM. Ejecuta:$(NC)"; \
		echo "  make vm-example"; \
	else \
		echo "$(BLUE)Desde macOS:$(NC)"; \
		echo "  make vagrant-up      # Crear VM (15-20 min)"; \
		echo "  make vagrant-ssh     # Conectar a VM"; \
		echo ""; \
		echo "$(GREEN)Dentro de la VM:$(NC)"; \
		echo "  cd /home/vagrant/tdh-engine"; \
		echo "  make vm-example      # Ejecutar análisis de ejemplo"; \
	fi

# ============================================
# ALIAS ÚTILES
# ============================================

up: vagrant-up
ssh: vagrant-ssh
down: vagrant-halt
destroy: vagrant-destroy
provision: vagrant-provision
status: vagrant-status
sync: vagrant-rsync
example: vm-example
info: env-info