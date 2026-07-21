"""
prediccion.py
=============

Persona 4 - Generación de predicciones para el dashboard (Persona 5).

Carga el modelo ganador y produce un pronóstico de tránsitos ANUALES para los
próximos años fiscales (FY2026 y FY2027).

El índice de tendencia continúa donde terminó la serie observada. El exógeno de
precio del crudo se proyecta con el último valor observado (supuesto plano).

Salida: `output/predicciones_2026.csv` con columnas
`anio_fiscal, transitos_predichos`, lista para el dashboard.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

import preparacion_datos as prep

log = logging.getLogger("persona4.prediccion")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
MODELS = BASE / "models"

HORIZONTE_ANIOS = 2


def _cargar_modelo() -> dict:
    ruta = MODELS / "modelo_transitos.pkl"
    if not ruta.exists():
        raise FileNotFoundError("No existe el modelo entrenado. Ejecuta primero entrenamiento.py.")
    with open(ruta, "rb") as fh:
        return pickle.load(fh)


def pronosticar(horizonte: int = HORIZONTE_ANIOS) -> pd.DataFrame:
    """Genera el pronóstico anual a `horizonte` años fiscales."""
    paquete = _cargar_modelo()
    modelo, feats = paquete["modelo"], paquete["features"]
    log.info("Modelo cargado: %s", paquete["nombre"])

    hist = prep.construir_features(prep.cargar_serie())
    ultimo_anio = int(hist["anio_fiscal"].max())
    indice_base = len(hist)
    ultimo_precio = float(hist["precio_barril_usd_prom"].ffill().iloc[-1])

    filas = []
    for h in range(1, horizonte + 1):
        registro = {
            "indice_tendencia": indice_base + h - 1,
            "precio_barril_usd_prom": ultimo_precio,  # supuesto plano
        }
        X = pd.DataFrame([registro])[feats].to_numpy()
        pred = max(float(modelo.predict(X)[0]), 0.0)
        filas.append({"anio_fiscal": ultimo_anio + h, "transitos_predichos": round(pred, 0)})

    df_pred = pd.DataFrame(filas)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destino = OUTPUT / "predicciones_2026.csv"
    df_pred.to_csv(destino, index=False)
    log.info("Pronóstico %d años guardado en %s", horizonte, destino)
    for _, r in df_pred.iterrows():
        log.info("  FY%d: %d tránsitos proyectados", int(r["anio_fiscal"]), int(r["transitos_predichos"]))
    return df_pred


def ejecutar() -> pd.DataFrame:
    return pronosticar()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    pronosticar()
