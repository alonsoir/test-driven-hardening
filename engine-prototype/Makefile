# engine-prototype/Makefile
.PHONY: help setup test clean check

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

help:
	@echo "🏗️  TDH Engine - Comandos disponibles:"
	@echo ""
	@echo "  make setup     - Configurar entorno virtual"
	@echo "  make test      - Ejecutar pruebas del SAST Orchestrator"
	@echo "  make check     - Verificar estructura del proyecto"
	@echo "  make clean     - Limpiar archivos temporales"
	@echo "  make run       - Ejecutar SAST en directorio actual"
	@echo ""

setup:
	@echo "🔧 Configurando entorno virtual..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Entorno configurado. Ejecuta: source $(VENV)/bin/activate"

test:
	@echo "🧪 Ejecutando pruebas..."
	$(PYTHON) scripts/test_sast.py .

run:
	@echo "🚀 Ejecutando SAST Orchestrator..."
	$(PYTHON) -m src.core.sast_orchestrator .

check:
	@echo "🔍 Verificando estructura del proyecto..."
	@bash scripts/check_structure.sh

clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete
	rm -rf reports/*.json reports/*.html
	@echo "✅ Limpieza completada"