#!/bin/bash
echo "🔧 Configurando Docker Desktop 4.59.1 para TDH Engine"
echo "="*60

# 1. Matar procesos de Docker si existen
echo "1. Deteniendo procesos Docker..."
killall Docker 2>/dev/null || true
killall "Docker Desktop" 2>/dev/null || true

# 2. Remover socket viejo
echo "2. Limpiando socket viejo..."
rm -f ~/.docker/run/docker.sock 2>/dev/null || true

# 3. Iniciar Docker Desktop
echo "3. Iniciando Docker Desktop..."
open -a Docker

# 4. Esperar
echo "4. Esperando 60 segundos..."
for i in {1..60}; do
    echo -n "."
    sleep 1
done
echo ""

# 5. Verificar
echo "5. Verificando Docker..."
if docker ps >/dev/null 2>&1; then
    echo "✅ Docker está funcionando"
else
    echo "❌ Docker no responde"
    echo ""
    echo "💡 Pasos manuales:"
    echo "1. Abre Docker Desktop manualmente"
    echo "2. Ve a Settings → General"
    echo "3. Marca 'Expose daemon on tcp://localhost:2375 without TLS'"
    echo "4. Haz click en 'Apply & Restart'"
    echo "5. Espera 60 segundos"
    exit 1
fi

echo ""
echo "🎉 Configuración completada"
echo "Ejecuta: python tdh_unified.py sast-orchestrated <repo_url>"
