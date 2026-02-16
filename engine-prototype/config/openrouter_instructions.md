# Instrucciones universales para todos los modelos OpenRouter

Debes seguir **estrictamente** el formato de bloques de código indicado. No incluyas texto explicativo fuera de los bloques. Cada respuesta debe contener **exactamente** los bloques requeridos según la fase.

## Formato general para cualquier respuesta

- Los bloques se indican con `[etiqueta]` en una línea aparte, seguido de un bloque de código con triple backticks y el lenguaje apropiado.
- Ejemplo de bloque de test:
  [test]
  ```python
  print("test")
  
Ejemplo de bloque de comando:
[command]

bash
python test.py
Fase de diseño de test (test_designing)

Debes generar dos bloques:

[test] con el código del test (puede ser script bash, programa C, Python, etc.).
[command] con el comando exacto para ejecutar el test.
El test debe demostrar la vulnerabilidad en el archivo indicado. Si la vulnerabilidad es de compilación, el test puede ser un script que compile el archivo y verifique que se produce el error esperado.

Fase de diseño de fix (fix_designing)

Debes generar dos bloques:

[fix] con el código completo del archivo a modificar después de aplicar la corrección.
[command] con el comando para verificar el fix (normalmente el mismo comando del test).
El fix debe eliminar la vulnerabilidad sin romper la funcionalidad.

Recordatorios importantes

No añadas comentarios adicionales fuera de los bloques.
Si el test falla, recibirás feedback y deberás iterar.
Usa el lenguaje apropiado para el bloque de código (c, cpp, bash, python, etc.).
Asegúrate de que el comando sea ejecutable dentro del contenedor (las herramientas necesarias están instaladas).