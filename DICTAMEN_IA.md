# Dictamen sobre `ia_propuesta.py` — Parte D

**Grupo:** DA8A · **Integrantes:** Luna Pico, Nicole López

> Tres defectos. Las cuatro secciones de cada uno son obligatorias y se parsean.
> El peso está en **«Cómo lo comprobamos»**: afirmar que algo está mal no vale;
> demostrarlo, sí.

## Defecto 1

- **Qué está mal:** El validador `redondear_monto` calcula `round(v, 2)` pero nunca retorna el resultado. Al no tener `return`, la función devuelve `None` implícitamente, y Pydantic asigna ese `None` como nuevo valor de `monto` — el campo queda silenciosamente corrompido en cada solicitud válida.
- **Por qué es un defecto** (citando módulo · sección): M4 · 6. Validadores de campo — un validador de campo debe transformar y **retornar** el valor validado; si no retorna nada, el framework interpreta el `None` implícito como el nuevo valor del campo, sin lanzar ningún error.
- **Cómo lo comprobamos:**
```powershell
python -c "from ia_propuesta import SolicitudPuntuacion; s = SolicitudPuntuacion(poliza='POL-20260001', correo_analista='ana@usta.co', monto=1234.567, antiguedad=3, siniestros_previos=1); print(s.monto)"
```

Salida obtenida: `None` (se esperaba `1234.57`)
- **Corrección:** Agregar `return round(v, 2)` al final del validador.

## Defecto 2

- **Qué está mal:** `_puntuar` usa `time.sleep(0.2)` (bloqueante) dentro de una función `async def`, en vez de `await asyncio.sleep(0.2)`. Esto bloquea el event loop durante cada llamada, anulando el propósito de `evaluar_lote`, que usa `asyncio.gather` para evaluar el lote "concurrentemente" (como pedía el prompt original).
- **Por qué es un defecto** (citando módulo · sección): M5 · 6. Síncrono frente a asíncrono — una función `async def` que bloquea con una llamada síncrona en su interior impide que el event loop atienda otras tareas mientras espera, eliminando el beneficio de la concurrencia cooperativa que ofrece `asyncio`.
- **Cómo lo comprobamos:**
```powershell
python -c "
import asyncio, time
from ia_propuesta import evaluar_lote, SolicitudPuntuacion
sols = [SolicitudPuntuacion(poliza='POL-20260001', correo_analista='ana@usta.co', monto=100.0, antiguedad=2, siniestros_previos=0) for _ in range(5)]
t0 = time.perf_counter()
asyncio.run(evaluar_lote(sols))
print(round(time.perf_counter() - t0, 2), 'segundos')
"
```

Salida obtenida: `1.01 segundos` para 5 solicitudes (≈5 × 0.2s, es decir, secuencial). Si fuera concurrente de verdad, el lote completo tardaría ≈0.2s.
- **Corrección:** Cambiar `time.sleep(0.2)` por `await asyncio.sleep(0.2)`.

## Defecto 3

- **Qué está mal:** El patrón regex de `correo_analista`, `^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,3}$`, solo permite un único punto después del `@` (dominio + un TLD de 2-3 letras). Rechaza cualquier correo con subdominio, como los institucionales de la forma `usuario@universidad.edu.co`.
- **Por qué es un defecto** (citando módulo · sección): M4 · 4. El poder de Field — una restricción de formato (`pattern`) debe cubrir el espacio real de valores válidos del dominio; aquí el patrón es más estricto que el formato real de un correo, y rechaza entradas legítimas en vez de solo las inválidas.
- **Cómo lo comprobamos:**

```python -c "
from ia_propuesta import SolicitudPuntuacion; SolicitudPuntuacion(poliza='POL-20260001', correo_analista='ana@usta.edu.co', monto=100.0, antiguedad=2, siniestros_previos=0)"
```

Salida obtenida: `ValidationError: String should match pattern...` para `ana@usta.edu.co`, un correo institucional válido.
- **Corrección:** Ajustar el patrón para aceptar múltiples subdominios, por ejemplo: `^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$`