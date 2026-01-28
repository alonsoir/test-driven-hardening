# engine-prototype/knowledge_base/README.md
cat > knowledge_base/README.md << 'EOF'
# TDH Engine - Knowledge Base

Este directorio contiene ejemplos de vulnerabilidades y sus soluciones para entrenar y probar el TDH Engine.

## Estructura

Cada CWE (Common Weakness Enumeration) tiene su propio directorio:
knowledge_base/
├── CWE-120/ # Buffer Overflow
│ ├── example1.c # Ejemplo vulnerable
│ ├── example1_fixed.c # Solución
│ └── test_poc.c # Test de PoC
├── CWE-89/ # SQL Injection
├── CWE-416/ # Use After Free
├── CWE-79/ # XSS (Cross-Site Scripting)
└── CWE-22/ # Path Traversal


## Cómo contribuir

1. Elige un CWE de la lista de MITRE
2. Crea un ejemplo mínimo reproducible de la vulnerabilidad
3. Implementa una solución segura
4. Añade un test de PoC que demuestre la vulnerabilidad
5. Documenta en un archivo README dentro del directorio del CWE

## Formato recomendado

Para cada ejemplo:

- `vulnerable.[ext]`: Código con la vulnerabilidad
- `fixed.[ext]`: Versión corregida
- `test_poc.[ext]`: Test que reproduce la vulnerabilidad
- `README.md`: Explicación técnica

## Recursos útiles

- [MITRE CWE List](https://cwe.mitre.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SANS Top 25](https://www.sans.org/top25-software-errors/)
EOF