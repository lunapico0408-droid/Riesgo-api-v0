"""
riesgo-api-v0 — Servicio de puntuación de siniestros.
Aseguradora Santo Tomás · prototipo interno.
"""
import pickle
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

import config
from dominio import EvaluadorRiesgo, RepositorioHistorial, buscar_siniestro, cargar_siniestros

BASE = Path(__file__).parent
modelo_cache = {}
repositorio_historial = RepositorioHistorial()


def obtener_modelo():
    """Devuelve el modelo cargado, cargándolo si aún no está en caché.

    En producción, lifespan lo carga una sola vez al iniciar el servidor.
    Este resguardo cubre además el caso de pruebas que instancian el
    TestClient sin activar el ciclo de vida (sin usar `with`).
    """
    if "modelo" not in modelo_cache:
        with open(BASE / config.RUTA_MODELO, "rb") as fh:
            modelo_cache["modelo"] = pickle.load(fh)
    return modelo_cache["modelo"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    obtener_modelo()
    yield
    modelo_cache.clear()


app = FastAPI(title="Riesgo API", version="0.1.0", lifespan=lifespan)


class ScorePayload(BaseModel):
    """Datos de entrada para puntuar una póliza."""

    poliza: str = Field(..., min_length=1, description="Identificador de la póliza")
    monto: float = Field(..., gt=0, description="Monto asegurado, debe ser positivo")
    antiguedad: int = Field(..., ge=0, description="Antigüedad de la póliza en años")
    siniestros_previos: int = Field(..., ge=0, description="Número de siniestros previos")

    @field_validator("poliza")
    @classmethod
    def poliza_no_vacia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("la póliza no puede estar vacía ni contener solo espacios")
        return v


class ScoreResponse(BaseModel):
    poliza: str
    puntaje: float
    alto_riesgo: bool


@app.post("/score", response_model=ScoreResponse)
async def score(payload: ScorePayload):
    modelo = obtener_modelo()
    evaluador = EvaluadorRiesgo(payload.poliza, repositorio=repositorio_historial)
    puntaje = evaluador.puntuar(modelo, payload.model_dump())
    evaluador.anotar(puntaje)
    return ScoreResponse(
        poliza=payload.poliza,
        puntaje=puntaje,
        alto_riesgo=evaluador.es_alto_riesgo(puntaje),
    )


@app.get("/historial")
async def historial():
    return {"evaluaciones": repositorio_historial.todos()}


@app.get("/siniestros/{id_siniestro}")
async def siniestro(id_siniestro: int):
    fila = buscar_siniestro(id_siniestro)
    if fila is None:
        raise HTTPException(status_code=404, detail=f"no existe el siniestro {id_siniestro}")
    return fila


@app.get("/exportar")
async def exportar():
    datos = cargar_siniestros()
    return datos


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