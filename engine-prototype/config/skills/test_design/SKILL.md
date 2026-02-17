
### 📝 Archivo: `config/skills/test_design/SKILL.md`

```markdown
# SKILL: Diseño de tests de seguridad

Tu tarea es crear un test que reproduzca fielmente la vulnerabilidad indicada.

## Contexto proporcionado

- **Vulnerabilidad**: {vulnerability}
- **Archivo vulnerable**: {repo_path}/{vuln_file}
- **Línea aproximada**: {line}
- **Contenido actual del archivo**:
```cpp
{file_content}
Reglas OBLIGATORIAS

1. El test DEBE usar el archivo vulnerable real. No crees nuevos archivos fuente a menos que sea para un programa que ejecute el código vulnerable (por ejemplo, un driver de prueba). Si necesitas compilar, hazlo sobre el archivo existente.
2. No generes código que reemplace el archivo original. El test solo debe verificar la vulnerabilidad, no modificarla.
3. Formato de salida exacto:

[test]

# código del test (puede ser bash, python, C, etc.)

[command]

comando para ejecutar el test

4. El comando debe ser ejecutable en el contenedor. Las herramientas disponibles incluyen gcc, g++, make, python3, bash, etc.

Estrategias según el tipo de vulnerabilidad

Error de sintaxis (como syntaxError)

Compila el archivo y verifica que se produce un error de compilación.
Ejemplo (basado en logs reales):
[test]
#!/bin/bash
g++ -c /workspace/firewall-acl-agent/src/core/ipset_wrapper.cpp 2>&1 | grep -q "error"
exit $?

[command]

bash test.sh

Violación de reglas (One Definition Rule)

Compila con flags que muestren advertencias y verifica el mensaje específico.
Ejemplo:
[test]

#!/bin/bash
g++ -Wall -Wextra -c /workspace/contrib/qwen/pca_pipeline/synthetic_data_generator.cpp 2>&1 | grep -q "multiple definition"
exit $?

[command]

bash test.sh

Desbordamiento de búfer

Compila el archivo (si es necesario) y ejecuta con entrada larga.
Ejemplo:
[test]

#include <stdlib.h>
int main() { return system("./vulnerable_program AAAAAAAAAAAAAAAAAAAAAAAAAAAAA"); }

[command]

gcc -o test test.c && ./test

Inyección de comandos

Ejecuta el programa con una entrada que contenga comandos y verifica el efecto.
Ciclo de retroalimentación

Si el test falla, recibirás la salida del comando. Por ejemplo:

Test output:
g++: error: ipset_wrapper.cpp: No such file or directory
g++: fatal error: no input files

En ese caso, revisa la ruta y el contenido del archivo. Ajusta el test para que use la ruta correcta o maneje el error adecuadamente. Nunca desistas de usar el archivo real.

