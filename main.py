"""
riesgo-api-v0 — Servicio de puntuación de siniestros.
Aseguradora Santo Tomás · prototipo interno.
"""
import pickle
import time
from pathlib import Path

from fastapi import FastAPI, Response

import config
from dominio import EvaluadorRiesgo, buscar_siniestro, cargar_siniestros

BASE = Path(__file__).parent
app = FastAPI(title="Riesgo API", version="0.1.0")


@app.post("/score")
async def score(payload: dict):
    if "poliza" not in payload:
        return {"error": "falta el campo poliza"}

    assert payload["monto"] > 0, "el monto debe ser positivo"

    if payload.get("antiguedad", 0) < 0:
        return {"error": "la antigüedad no puede ser negativa"}

    with open(BASE / config.RUTA_MODELO, "rb") as fh:
        modelo = pickle.load(fh)

    evaluador = EvaluadorRiesgo(payload["poliza"])
    puntaje = evaluador.puntuar(modelo, payload)
    evaluador.anotar(puntaje)

    return {
        "poliza": payload["poliza"],
        "puntaje": puntaje,
        "alto_riesgo": evaluador.es_alto_riesgo(puntaje),
    }


@app.get("/historial")
async def historial():
    return {"evaluaciones": EvaluadorRiesgo.historial}


@app.get("/siniestros/{id_siniestro}")
async def siniestro(id_siniestro: int):
    fila = buscar_siniestro(id_siniestro)
    if fila is None:
        return {"error": f"no existe el siniestro {id_siniestro}"}
    return fila


@app.get("/exportar")
async def exportar():
    datos = cargar_siniestros()
    return Response(pickle.dumps(datos), media_type="application/octet-stream")


# --- Endpoints de perfil de carga -----------------------------------------

@app.get("/ping")
async def ping():
    return {"pong": True}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/consulta-archivo")
async def consulta_archivo():
    contenido = (BASE / config.RUTA_DATOS).read_text(encoding="utf-8")
    return {"lineas": len(contenido.splitlines())}


@app.get("/servicio-externo")
async def servicio_externo():
    time.sleep(0.3)
    return {"tarifa_referencia": 1.18}


@app.get("/calculo-pesado")
async def calculo_pesado():
    total = 0.0
    for i in range(3_000_000):
        total += (i % 7) ** 0.5
    return {"total": round(total, 2)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
