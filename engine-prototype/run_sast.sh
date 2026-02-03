# engine-prototype/run_sast.sh
#!/bin/bash
# Script para activar entorno virtual y ejecutar SAST

cd "$(dirname "$0")"

# Verificar si estamos en entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Activando entorno virtual..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ No se encontró entorno virtual. Creando uno..."
        python3 -m venv venv
        source venv/bin/activate
        pip install PyYAML xmltodict rich tabulate
    fi
fi

# Ejecutar el script Python
python scripts/test_sast.py "$@"