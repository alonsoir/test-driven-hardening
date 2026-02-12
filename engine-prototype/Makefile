# ============================================
# TDH ENGINE - MAKEFILE PRINCIPAL
# Funciona en HOST (macOS) y en GUEST (Vagrant)
# ============================================

VENV_PATH = venv
PYTHON = python3
PIP = pip3
DOCKER = docker
VAGRANT_DIR = vagrant
PROJECT_NAME = tdh-engine

# Detectar si estamos en VM Vagrant
ifneq ($(wildcard /home/vagrant/$(PROJECT_NAME)/.),)
	IS_VAGRANT = true
	PROJECT_ROOT = /home/vagrant/$(PROJECT_NAME)
else
	IS_VAGRANT = false
	PROJECT_ROOT = .
endif

# Colores
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m

# ============================================
# COMANDOS PRINCIPALES
# ============================================

.PHONY: help setup setup-deps build-base test clean install-deps

help:
	@echo "$(BLUE)🤖 TDH ENGINE - COMANDOS DISPONIBLES$(NC)"
	@echo "$(GREEN)===========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)🏗️  CONFIGURACIÓN:$(NC)"
	@echo "  make setup           - Crea directorios y entorno virtual"
	@echo "  make setup-deps      - Instala dependencias desde requirements.txt"
	@echo "  make build-base      - Construye imagen Docker tdh-base:latest"
	@echo ""
	@echo "$(YELLOW)🧪 PRUEBAS:$(NC)"
	@echo "  make test            - Ejecuta prueba end‑to‑end (SAST + orquestación dry-run)"
	@echo "  make check           - Verifica dependencias"
	@echo ""
	@echo "$(YELLOW)🧹 MANTENIMIENTO:$(NC)"
	@echo "  make clean           - Limpia archivos temporales y contenedores legacy"
	@echo ""
	@echo "$(YELLOW)🚀 VAGRANT (desde HOST):$(NC)"
	@echo "  make vagrant-up      - Inicia VM"
	@echo "  make vagrant-ssh     - Conecta a VM"
	@echo "  make vagrant-halt    - Detiene VM"
	@echo "  make vagrant-destroy - Destruye VM"
	@echo "  make vagrant-status  - Estado VM"
	@echo ""
	@echo "$(YELLOW)🔧 DESARROLLO EN VM:$(NC)"
	@echo "  make vm-setup        - Configura entorno dentro de VM (deps + imagen)"
	@echo "  make vm-example      - Ejecuta análisis de ejemplo con orquestación"
	@echo ""
	@echo "$(YELLOW)📊 INFORMACIÓN:$(NC)"
	@echo "  make env-info        - Muestra entorno"
	@echo "  make docker-info     - Estado de Docker"
	@echo "  make list-tools      - Herramientas SAST disponibles"

# ----------------------------------------------------------------------
setup:
	@echo "$(BLUE)📁 Creando estructura de directorios...$(NC)"
	@mkdir -p src/{core,llm_integration,sast_integration,utils}
	@mkdir -p docker config tests results reports logs
	@touch src/core/__init__.py src/llm_integration/__init__.py \
	       src/sast_integration/__init__.py src/utils/__init__.py
	@echo "$(GREEN)✅ Estructura creada.$(NC)"

setup-deps:
	@echo "$(BLUE)🔧 Configurando entorno virtual...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		$(PYTHON) -m venv $(VENV_PATH); \
	fi
	@$(VENV_PATH)/bin/pip install --upgrade pip
	@if [ -f "requirements.txt" ]; then \
		$(VENV_PATH)/bin/pip install -r requirements.txt; \
	else \
		echo "$(YELLOW)⚠️  requirements.txt no encontrado, instalando mínimo...$(NC)"; \
		$(VENV_PATH)/bin/pip install docker aiofiles python-dotenv; \
	fi
	@echo "$(GREEN)✅ Dependencias instaladas.$(NC)"

check:
	@echo "$(BLUE)🔍 Verificando dependencias...$(NC)"
	@$(VENV_PATH)/bin/python -c "import docker, aiofiles, dotenv; print('✅ docker, aiofiles, python-dotenv OK')" \
		|| echo "$(RED)❌ Faltan dependencias$(NC)"

build-base:
	@echo "$(BLUE)🐳 Construyendo imagen base...$(NC)"
	@if [ -f "docker/Dockerfile.base" ]; then \
		$(DOCKER) build -f docker/Dockerfile.base -t tdh-base:latest .; \
		echo "$(GREEN)✅ Imagen tdh-base:latest construida.$(NC)"; \
	else \
		echo "$(RED)❌ No se encontró docker/Dockerfile.base$(NC)"; \
		exit 1; \
	fi

test:
	@echo "$(BLUE)🧪 Ejecutando prueba end‑to‑end...$(NC)"
	@$(VENV_PATH)/bin/python tdh_unified.py test

clean:
	@echo "$(BLUE)🧹 Limpiando...$(NC)"
	@-$(VENV_PATH)/bin/python tdh_unified.py docker-cleanup 2>/dev/null || true
	@-rm -rf results/* test-results/* reports/* logs/*
	@-find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@-find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpieza completada.$(NC)"

# ----------------------------------------------------------------------
# Comandos Vagrant (desde HOST)
vagrant-up:
	@cd $(VAGRANT_DIR) && vagrant up

vagrant-ssh:
	@cd $(VAGRANT_DIR) && vagrant ssh

vagrant-halt:
	@cd $(VAGRANT_DIR) && vagrant halt

vagrant-destroy:
	@cd $(VAGRANT_DIR) && vagrant destroy -f

vagrant-status:
	@cd $(VAGRANT_DIR) && vagrant status

# ----------------------------------------------------------------------
# Comandos dentro de la VM
vm-setup: setup-deps build-base
	@echo "$(GREEN)✅ VM lista.$(NC)"

vm-example:
	@echo "$(BLUE)🎪 Ejemplo: orquestación multi‑SOTA (dry-run)$(NC)"
	@if [ "$(IS_VAGRANT)" != "true" ]; then \
		echo "$(RED)❌ Debes ejecutar esto dentro de la VM$(NC)"; \
		exit 1; \
	fi
	@$(VENV_PATH)/bin/python tdh_unified.py sast-orchestrated \
		https://github.com/alonsoir/test-zeromq-c-.git \
		--dry-run

# ----------------------------------------------------------------------
# Información
env-info:
	@echo "$(BLUE)📊 ENTORNO$(NC)"
	@echo "En VM: $(IS_VAGRANT)"
	@echo "Python: $(shell which python3)"
	@echo "Docker: $(shell which docker)"
	@echo "Vagrant: $(shell which vagrant)"

docker-info:
	@$(DOCKER) info --format '{{.ServerVersion}}' 2>/dev/null \
		&& echo "$(GREEN)✅ Docker OK$(NC)" \
		|| echo "$(RED)❌ Docker no disponible$(NC)"

list-tools:
	@for tool in semgrep bandit trivy cppcheck flawfinder; do \
		if command -v $$tool >/dev/null 2>&1; then \
			echo "✅ $$tool"; \
		else \
			echo "❌ $$tool"; \
		fi; \
	done

# ----------------------------------------------------------------------
# Alias
up: vagrant-up
ssh: vagrant-ssh
halt: vagrant-halt
destroy: vagrant-destroy
status: vagrant-status
example: vm-example