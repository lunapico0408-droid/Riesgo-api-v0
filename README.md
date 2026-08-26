# riesgo-api-v0

Servicio de puntuación de siniestros de la Aseguradora Santo Tomás.
Recibe los datos de una póliza y devuelve la probabilidad de que el siniestro
declarado termine en un pago alto.

## Instalación
​```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
​```

Crea un archivo `.env` en la raíz del proyecto con las claves necesarias:

​```
API_KEY=sk-riesgo-2026-9f3a1c7b4e21
CLAVE_FIRMA=aseguradora-santo-tomas-2026
​```

El modelo entrenado (`modelo.pkl`) viene en el repositorio.

## Puesta en marcha

**Desarrollo** (con recarga automática, no usar en producción):
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Producción:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```
Sin `--reload`: la recarga en caliente añade overhead y no es apropiada para un entorno estable. `--workers 4` permite atender varias peticiones en paralelo usando múltiples procesos.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/score` | Puntúa una póliza |
| GET | `/historial` | Evaluaciones hechas |
| GET | `/siniestros/{id}` | Consulta un siniestro |
| GET | `/exportar` | Exporta el histórico para el equipo de actuaría |
| GET | `/ping` | Comprobación rápida |
| GET | `/consulta-archivo` | Cuenta los registros del archivo de siniestros |
| GET | `/servicio-externo` | Consulta la tarifa de referencia del reasegurador |
| GET | `/calculo-pesado` | Recalcula la reserva agregada |

### Ejemplo

```bash
curl -X POST localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"poliza": "POL-2026-0413", "monto": 4200000, "antiguedad": 3, "siniestros_previos": 1}'
```

```json
{"poliza": "POL-2026-0413", "puntaje": 0.61, "alto_riesgo": false}
```

## Notas
- Las claves de la API viven en variables de entorno (`.env`), no en el código — ver sección de Instalación.
- El histórico se exporta en JSON nativo.
