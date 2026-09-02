"""Lógica de dominio: evaluación de riesgo de pólizas."""
import csv
from pathlib import Path

import config
from utilidades import con_registro

BASE = Path(__file__).parent


class RepositorioHistorial:
    """Guarda el histórico de evaluaciones realizadas por el servicio."""

    def __init__(self):
        self._registros = []

    def agregar(self, registro):
        self._registros.append(registro)

    def todos(self):
        return list(self._registros)


class EvaluadorRiesgo:
    """Evalúa el riesgo de una póliza y guarda lo que ha evaluado."""

    umbral = config.UMBRAL_ALTO_RIESGO

    def __init__(self, poliza, repositorio=None):
        self.poliza = poliza
        self.historial = []
        self.repositorio = repositorio

    @con_registro
    def puntuar(self, modelo, payload):
        rasgos = [[
            payload["monto"],
            payload["antiguedad"],
            payload["siniestros_previos"],
        ]]
        return float(modelo.predict_proba(rasgos)[0][1])

    def anotar(self, puntaje):
        registro = {"poliza": self.poliza, "puntaje": puntaje}
        self.historial.append(registro)
        if self.repositorio is not None:
            self.repositorio.agregar(registro)

    def es_alto_riesgo(self, puntaje):
        return puntaje is not None and puntaje > self.umbral


_siniestros_cache = None


def cargar_siniestros():
    """Carga el CSV desde disco solo la primera vez; las siguientes
    llamadas reutilizan lo que ya está en memoria."""
    global _siniestros_cache
    if _siniestros_cache is None:
        with open(BASE / config.RUTA_DATOS, encoding="utf-8") as fh:
            _siniestros_cache = list(csv.DictReader(fh))
    return _siniestros_cache


def buscar_siniestro(id_siniestro):
    for fila in cargar_siniestros():
        if fila["id"] == str(id_siniestro):
            return fila
    return None
