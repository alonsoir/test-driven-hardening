
### 📝 Archivo: `config/skills/fix_design/SKILL.md`

```markdown
# SKILL: Diseño de fixes de seguridad

Tu tarea es corregir la vulnerabilidad modificando el archivo afectado.

## Contexto proporcionado

- **Vulnerabilidad**: {vulnerability}
- **Archivo a modificar**: {repo_path}/{vuln_file}
- **Línea aproximada**: {line}
- **Contenido actual del archivo**:
```cpp
{file_content}

Test que reproduce la vulnerabilidad:

{test_code}

Comando para ejecutar el test: {test_command}

Reglas OBLIGATORIAS

1. El fix debe aplicarse directamente al archivo vulnerable. Debes generar el contenido completo del archivo después de la corrección.
2. Formato de salida exacto:

[fix]
// código completo del archivo corregido
[command]
comando para verificar el fix (normalmente el mismo test)

3. El fix debe eliminar la vulnerabilidad sin romper la funcionalidad. Si el test original pasaba con la vulnerabilidad, tras el fix el test debe fallar (si el test busca la vulnerabilidad) o pasar (si el test busca que no haya error). En nuestro caso, el test busca la vulnerabilidad, por lo que tras el fix debería fallar (código de salida distinto de cero) o no detectar el error.
4. No incluyas texto fuera de los bloques.
Estrategias según el tipo de vulnerabilidad

Error de sintaxis

* Corrige la línea donde falla la sintaxis. Por ejemplo, si falta un punto y coma, añádelo.
* Ejemplo (simulado):
[fix]

#include <ipset_wrapper.h>
// ... resto del archivo ...
int main() { return 0; }  // Línea 73 corregida

[command]

g++ -c /workspace/firewall-acl-agent/src/core/ipset_wrapper.cpp

# One Definition Rule

Asegura que las definiciones no se repitan. Puede requerir mover definiciones a un archivo .cpp y dejar solo declaraciones en el .h.

# Desbordamiento de búfer

Usa funciones seguras como strncpy en lugar de strcpy, o añade comprobaciones de límites.

# Ciclo de retroalimentación

Después de aplicar el fix, se ejecutará el test. Si el test aún detecta la vulnerabilidad (es decir, el test falla porque encuentra el error), recibirás un mensaje como:

Fix failed. Output:
... (salida del test)

Entonces debes iterar, mejorando el fix. Si el test ya no detecta la vulnerabilidad (es decir, el test pasa), el fix será considerado exitoso.


