# Bitácora de uso de IA

**Grupo:** DA8A · **Integrantes:** Luna Pico, Nicole López
**Herramientas usadas:** Claude, ChatGPT, Qwen

## Prompts

A lo largo del taller usamos Claude como guía principal para diagnosticar, refactorizar y auditar el servicio, trabajando de forma iterativa: pedíamos una corrección, la aplicábamos, verificábamos con comandos reales, y solo avanzábamos cuando la evidencia confirmaba que funcionaba. Ejemplos de los tipos de prompts usados:

- Solicitudes de diagnóstico: "ayúdame a encontrar los defectos del repositorio y documentarlos con evidencia real"
- Solicitudes de corrección guiada, restricción por restricción (B1 a B9), pidiendo siempre el código exacto a pegar y el comando para verificar el efecto
- Solicitudes de depuración cuando algo fallaba: pegar tracebacks completos y pedir la causa exacta antes de aplicar cualquier arreglo
- Solicitudes de medición y clasificación para la Parte C, pidiendo que las conclusiones se basaran en los números obtenidos, no en la teoría general
- Solicitud de auditoría de `ia_propuesta.py`, pidiendo evidencia ejecutable para cada defecto antes de darlo por confirmado
- Solicitudes de verificación del arranque limpio en varios computadores distintos, siguiendo únicamente el README

## Aceptado

- El diseño de `RepositorioHistorial` inyectado como colaborador opcional de `EvaluadorRiesgo`, en vez de simplemente mover `historial` a `self.historial` sin más — necesario porque el endpoint `/historial` requiere persistencia entre peticiones distintas, y una lista de instancia sola se habría perdido en cada request.
- El patrón de `modelo_cache` + `lifespan` para B6, con la función `obtener_modelo()` de respaldo para cubrir el caso de los tests, que instancian `TestClient` sin activar el ciclo de vida completo.
- El uso de `functools.wraps` y `raise` (en vez de `return None`) en el decorador `con_registro` para B9.
- El diseño del `BaseModel` de Pydantic para B2/B5, incluyendo el validador de campo `poliza_no_vacia`.
- Dejar `umbral` como atributo de clase en `EvaluadorRiesgo` (no moverlo a instancia): es un valor de configuración compartido y de solo lectura, no estado mutable — el problema original nunca fue "atributo de clase" en general, sino específicamente una lista mutable compartida.
- Las correcciones de los 3 defectos de `ia_propuesta.py` (validador sin `return`, `time.sleep` bloqueante, regex de correo demasiado restrictivo).
- La sugerencia de agregar una sección "Requisitos previos" (Python, Git) al README, tras detectar que dos computadores nuevos no los tenían instalados.
- La corrección final del comando para crear `.env`, separando instrucciones específicas para PowerShell (`Out-File -Encoding ascii`) y para Bash, una vez identificado el problema de codificación (ver Rechazado).

## Rechazado

- **Comandos de evidencia con resultados falsos, detectados a tiempo.** Al verificar el defecto de `/exportar` (pickle), el primer comando propuesto (`curl.exe -sI`) usaba una petición HEAD, que dio `405 Method Not Allowed` en vez del comportamiento real del endpoint — no reflejaba el defecto que buscábamos. Se rechazó esa evidencia y se repitió con una petición GET real (`curl.exe -s -D - -o NUL`), que sí mostró el `content-type: application/octet-stream` correcto.
- **Evidencia contaminada por el escapado de comillas de PowerShell.** Al probar `/score` con un payload inválido, dos intentos seguidos con comillas escapadas manualmente en la línea de comandos, propuestos por la IA, dieron `422` — pero por un `JSON decode error` (comillas mal formadas), no por el defecto real que se quería demostrar (200 con error en el cuerpo). Se rechazó esa evidencia y se cambió de estrategia: escribir el payload en un archivo `.json` con `Out-File` y pasarlo con `--data-binary "@archivo.json"`, evitando el problema de raíz.
- **Hipótesis inicial imprecisa sobre el Defecto 3 de `ia_propuesta.py`.** La primera hipótesis de la IA fue que el regex del correo solo rechazaba TLDs de 4+ letras (`.info`, `.coop`). Al comprobarlo con un correo institucional real (`ana@usta.edu.co`), la causa resultó ser distinta y más amplia: el patrón solo permite un único punto después del `@`, rechazando cualquier dominio con subdominio. Se corrigió la explicación en `DICTAMEN_IA.md` para reflejar la causa real, comprobada, en vez de la hipótesis inicial sin verificar.
- **No aplicar el "arreglo de manual" a `/consulta-archivo` en la Parte C.** Aunque en teoría el endpoint viola la regla "I/O va con async" (usa `.read_text()` bloqueante dentro de `async def`), medir mostró que su tiempo es prácticamente idéntico al de `/ping` (0.112s vs 0.072s). Se rechazó la sugerencia de moverlo a un executor, porque el overhead de esa complejidad adicional probablemente sería peor que el bloqueo mínimo actual — la decisión se tomó con datos medidos, no siguiendo la regla general a ciegas.
- **Hipótesis fallida sobre la causa del bloqueo al probar arranque limpio en una carpeta nueva.** Cuando `scikit-learn` falló al cargar con un error de "Control de aplicaciones" de Windows, la primera hipótesis de la IA fue que OneDrive corrompía archivos durante la sincronización, y propuso reinstalar `scipy`/`scikit-learn` con `--force-reinstall --no-cache-dir`. Esa reinstalación no cambió el error. Se investigó más a fondo y se encontró la causa real: "Control Inteligente de Aplicaciones" de Windows, activo en esa máquina. Se descartó perseguir esa vía (no se puede desactivar sin reinstalar Windows) y se confirmó el funcionamiento del servicio por otra vía: los 11 tests de `tests/test_contrato.py` pasan, y el servicio corre bien en el entorno principal.
- **Comando de creación de `.env` que la IA propuso sin considerar la codificación de PowerShell.** La IA sugirió `echo "API_KEY=..." > .env` para el README, asumiendo que funcionaría igual en cualquier terminal. Al probarlo en un computador Windows nuevo, causó un `UnicodeDecodeError` al arrancar el servicio, porque PowerShell guarda esa redirección en UTF-16 por defecto, no UTF-8. Se descartó ese comando y se reemplazó por `Out-File -Encoding ascii`, específico para PowerShell.