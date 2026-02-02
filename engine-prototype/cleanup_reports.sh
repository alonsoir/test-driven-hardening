#!/bin/bash
# Limpia reportes antiguos manteniendo los más recientes

echo "🧹 LIMPIANDO REPORTES ANTIGUOS"
echo "============================="

# Opciones
KEEP_LAST=5  # Mantener los últimos 5 reportes por repositorio

if [ "$1" == "--dry-run" ]; then
    echo "🔍 MODO SIMULACIÓN (no borra)"
    DRY_RUN=true
else
    DRY_RUN=false
fi

# Limpiar JSON
echo ""
echo "📄 Reportes JSON:"
for repo in $(ls tdh_report_*.json 2>/dev/null | cut -d'_' -f3 | sort -u); do
    count=$(ls tdh_report_${repo}_*.json 2>/dev/null | wc -l)
    if [ $count -gt $KEEP_LAST ]; then
        to_delete=$((count - KEEP_LAST))
        echo "  $repo: $count reportes (eliminar $to_delete más antiguos)"
        
        # Ordenar por fecha (más antiguos primero) y eliminar
        files_to_delete=$(ls -tr tdh_report_${repo}_*.json 2>/dev/null | head -$to_delete)
        for file in $files_to_delete; do
            if [ "$DRY_RUN" = true ]; then
                echo "    🗑️  [SIM] Eliminaría: $file"
            else
                echo "    🗑️  Eliminando: $file"
                rm "$file"
            fi
        done
    else
        echo "  $repo: $count reportes (mantener todos)"
    fi
done

# Limpiar HTML
echo ""
echo "🌐 Reportes HTML:"
for repo in $(ls tdh_report_*.html 2>/dev/null | cut -d'_' -f3 | sort -u); do
    count=$(ls tdh_report_${repo}_*.html 2>/dev/null | wc -l)
    if [ $count -gt $KEEP_LAST ]; then
        to_delete=$((count - KEEP_LAST))
        echo "  $repo: $count reportes (eliminar $to_delete más antiguos)"
        
        files_to_delete=$(ls -tr tdh_report_${repo}_*.html 2>/dev/null | head -$to_delete)
        for file in $files_to_delete; do
            if [ "$DRY_RUN" = true ]; then
                echo "    🗑️  [SIM] Eliminaría: $file"
            else
                echo "    🗑️  Eliminando: $file"
                rm "$file"
            fi
        done
    else
        echo "  $repo: $count reportes (mantener todos)"
    fi
done

echo ""
echo "📊 ESTADO FINAL:"
echo "JSON: $(ls tdh_report_*.json 2>/dev/null | wc -l) archivos"
echo "HTML: $(ls tdh_report_*.html 2>/dev/null | wc -l) archivos"
