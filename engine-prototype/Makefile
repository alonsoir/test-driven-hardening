# engine-prototype/Makefile
.PHONY: setup setup-deps build-base test clean check

setup: setup-deps
	@echo "📁 Creando estructura de directorios..."
	mkdir -p src/{core,llm_integration,sast_integration,utils}
	mkdir -p docker config tests results
	touch src/core/__init__.py src/llm_integration/__init__.py src/sast_integration/__init__.py src/utils/__init__.py
	@echo "✅ Configuración completada."

setup-deps:
	@echo "🔧 Configurando entorno virtual y dependencias..."
	@if [ ! -d "venv" ]; then \
		python3.13 -m venv venv || python3.12 -m venv venv || python3 -m venv venv; \
	fi
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencias instaladas."

check:
	@echo "🔍 Verificando dependencias..."
	venv/bin/python check_deps.py

build-base:
	@echo "🐳 Construyendo imagen base Docker..."
	docker build -f docker/Dockerfile.base -t tdh-base:latest .
	@echo "✅ Imagen base construida."

test:
	@echo "🧪 Ejecutando prueba completa..."
	venv/bin/python tdh_unified.py test

clean:
	@echo "🧹 Limpiando..."
	-venv/bin/python tdh_unified.py docker-cleanup 2>/dev/null || true
	-rm -rf results/* test-results/*
	@echo "✅ Limpieza completada."

# Comando rápido para instalar solo aiofiles
install-aiofiles:
	venv/bin/pip install aiofiles>=23.2.0
	@echo "✅ aiofiles instalado."