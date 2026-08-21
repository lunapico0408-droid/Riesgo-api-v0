# Hallazgos — Parte A

**Grupo:** < DA8A> · **Integrantes:** < Luna Pico>, < Nicole López>

| ID | Síntoma observable | Causa | Módulo · Sección | SHA donde se observa | Comando de evidencia | Salida obtenida | Corrección aplicada |
|----|--------------------|-------|-------------------|-----------------------|------------------------|--------------------|------------------------|
| H1 | `GET /exportar` responde con `content-type: application/octet-stream` en vez de JSON | El endpoint serializa el histórico con `pickle.dumps()` antes de enviarlo al cliente | M2 · 3. JSON frente a Pickle | `6a91db1` | `curl.exe -s -D - -o NUL http://localhost:8000/exportar` | `content-type: application/octet-stream` (content-length: 22481) | Cambiar a `JSONResponse` con datos serializados a tipos nativos, no pickle |
| H2 | `POST /score` con payload inválido responde `200 OK` con el error en el cuerpo, no en un código 4xx | El handler valida manualmente con `if`/`assert`, sin usar el sistema de estados HTTP para errores | M2 · 2. El protocolo HTTP y la autenticación | `6a91db1` | `curl.exe -i -X POST http://localhost:8000/score -H "Content-Type: application/json" --data-binary "@payload.json"` (payload.json = {"monto": 100}) | `HTTP/1.1 200 OK` / `{"error":"falta el campo poliza"}` | Validar con `BaseModel`; `ValidationError` → 422 automático; reglas de negocio → `HTTPException(422, ...)` |
| H3 | `GET /health` responde `404 Not Found` | El endpoint no existe en el servicio | M5 · 8. Resumen y mejores prácticas | `6a91db1` | `curl.exe -sI http://localhost:8000/health` | `HTTP/1.1 404 Not Found` | Crear el endpoint `/health` que devuelva 200 |
| H4 | `POST /score` sin `siniestros_previos` responde `200 OK` con `puntaje: null` y `alto_riesgo: false`, en vez de fallar | El decorador `con_registro` atrapa el `KeyError` de `dominio.puntuar()` y devuelve `None` silenciosamente, ocultando el error | M1 · 6. Decoradores como guardianes | `6a91db1` | `curl.exe -i -X POST http://localhost:8000/score -H "Content-Type: application/json" --data-binary "@payload2.json"` (payload2.json = {"poliza":"POL-2026-0001","monto":100,"antiguedad":2}) | `HTTP/1.1 200 OK` / `{"poliza":"POL-2026-0001","puntaje":null,"alto_riesgo":false}` | Validar con Pydantic (falla 422 antes de llegar al handler) y corregir el decorador para no tragar excepciones silenciosamente |
| H5 | `config.py` contiene `API_KEY` y `CLAVE_FIRMA` en texto plano, versionadas en Git | Secretos en el repositorio en vez de variables de entorno | M1 · 5. Git y GitHub para investigadores | `6a91db1` | `Get-Content config.py` | `# TODO: sacar esto a variables de entorno antes de subir a producción` / `API_KEY = "sk-riesgo-2026-9f3a1c7b4e21"` / `CLAVE_FIRMA = "aseguradora-santo-tomas-2026"` | Mover a `.env` + `os.environ`, añadir `.env` a `.gitignore` |
| H6 | `requirements.txt` no fija versión en ninguna de sus 7 dependencias | Entorno no reproducible entre máquinas | M2 · 5. requirements.txt y la reproducibilidad | `6a91db1` | `Get-Content requirements.txt` | `fastapi` / `uvicorn` / `pydantic` / `scikit-learn` / `numpy` / `pytest` / `httpx` (sin versión en ninguna) | Fijar versiones con `pip freeze > requirements.txt` |
| H7 | El README documenta `--reload` como apto para producción, y `main.py` arranca con `reload=True` | Recarga en caliente no es apropiada para producción | M5 · 8. Resumen y mejores prácticas | `6a91db1` | `Select-String -Path README.md -Pattern "reload"` / `Select-String -Path main.py -Pattern "reload"` | `README.md:21: El mismo comando sirve en el servidor de producción. --reload es cómodo` / `main.py:90: uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)` | Arranque de producción con `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`, sin `--reload` |
| H8 | Dos instancias distintas de `EvaluadorRiesgo` comparten el mismo historial | `historial = []` es atributo de clase, no de instancia — estado mutable global | M3 · 3. Componentes: atributos de clase | `6a91db1` | `python -c "from dominio import EvaluadorRiesgo; a=EvaluadorRiesgo('POL-1'); b=EvaluadorRiesgo('POL-2'); a.anotar(0.5); print(b.historial)"` | `[{'poliza': 'POL-1', 'puntaje': 0.5}]` | Mover `historial` a `__init__` como atributo de instancia (`self.historial = []`) |
| H9 | El modelo `.pkl` se carga con `pickle.load()` dentro del handler, en cada petición | Debería cargarse una sola vez al iniciar el servicio | M5 · 8. Resumen y mejores prácticas | `6a91db1` | `Select-String -Path main.py -Pattern "pickle.load" -Context 2,3` | `main.py:28: with open(BASE / config.RUTA_MODELO, "rb") as fh:` / `main.py:29: modelo = pickle.load(fh)` (dentro de `score()`) | Cargar el modelo una vez al iniciar (evento `startup`) y reutilizarlo |

## Parte C

### `/ping`
*(pendiente: clasificación + decisión + interpretación de los tiempos obtenidos)*

### `/consulta-archivo`
*(pendiente: clasificación + decisión + interpretación de los tiempos obtenidos)*

### `/servicio-externo`
*(pendiente: clasificación + decisión + interpretación de los tiempos obtenidos)*

### `/calculo-pesado`
*(pendiente: clasificación + decisión + interpretación de los tiempos obtenidos)*

