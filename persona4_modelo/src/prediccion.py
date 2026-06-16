"""
prediccion.py
=============

Persona 4 - Generación de predicciones para el dashboard (Persona 5).

Reentrena (carga) el modelo ganador y produce un pronóstico de tránsitos
mensuales para los próximos 12 meses (horizonte 2026-01 → 2026-12).

Como el modelo usa features autorregresivos (`lag_1`, `media_movil_3`), el
pronóstico se genera de forma **recursiva**: cada mes predicho alimenta el
cálculo de los lags del mes siguiente. El `lag_12` del horizonte 2026 usa los
tránsitos reales de 2025 (conocidos). Los exógenos de precio se proyectan con
el último valor observado (supuesto plano, documentado en METODOLOGIA.md).

Salida: `output/predicciones_2026.csv` con columnas
`fecha, transitos_predichos, anio, mes`, lista para el dashboard.
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

HORIZONTE_MESES = 12


def _cargar_modelo() -> dict:
    ruta = MODELS / "modelo_transitos.pkl"
    if not ruta.exists():
        raise FileNotFoundError(
            "No existe el modelo entrenado. Ejecuta primero entrenamiento.py."
        )
    with open(ruta, "rb") as fh:
        return pickle.load(fh)


def pronosticar(horizonte: int = HORIZONTE_MESES) -> pd.DataFrame:
    """Genera el pronóstico recursivo a `horizonte` meses."""
    paquete = _cargar_modelo()
    modelo, feats = paquete["modelo"], paquete["features"]
    log.info("Modelo cargado: %s", paquete["nombre"])

    # Historia completa con features y target (incluye filas con lag_12 válido).
    hist = prep.construir_features(prep.cargar_serie())

    # Serie de tránsitos como historia viva para calcular lags recursivos.
    serie = hist[["fecha", prep.TARGET]].dropna().copy()
    transitos = list(serie[prep.TARGET].to_numpy(dtype=float))
    fechas = list(serie["fecha"])

    # Supuesto plano para los exógenos de precio (último valor observado).
    ultimo_precio = float(hist["precio_barril_usd"].ffill().iloc[-1])
    ultimo_precio_ma3 = float(hist["precio_barril_usd_ma3"].ffill().iloc[-1])

    # Índice de tendencia continúa donde terminó la serie observada.
    indice_base = len(hist)

    filas = []
    for h in range(1, horizonte + 1):
        fecha = fechas[-1] + pd.DateOffset(months=1)
        mes = fecha.month

        registro = {
            "mes_sin": np.sin(2 * np.pi * mes / 12),
            "mes_cos": np.cos(2 * np.pi * mes / 12),
            "indice_tendencia": indice_base + h - 1,
            "periodo_sequia": 0,  # 2026 fuera del régimen de sequía
            "periodo_recuperacion": 1,  # 2026 sigue en régimen post-2025
            "lag_1": transitos[-1],
            "lag_12": transitos[-12],
            "media_movil_3": float(np.mean(transitos[-3:])),
            "precio_barril_usd": ultimo_precio,
            "precio_barril_usd_ma3": ultimo_precio_ma3,
        }

        X = pd.DataFrame([registro])[feats]
        pred = float(modelo.predict(X)[0])
        pred = max(pred, 0.0)  # no-negatividad

        filas.append({
            "fecha": fecha,
            "transitos_predichos": round(pred, 0),
            "anio": fecha.year,
            "mes": mes,
        })

        # Alimentar la historia con el valor predicho (recursión).
        transitos.append(pred)
        fechas.append(fecha)

    df_pred = pd.DataFrame(filas)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    destino = OUTPUT / "predicciones_2026.csv"
    df_pred.to_csv(destino, index=False)
    log.info("Pronóstico %d meses guardado en %s", horizonte, destino)
    log.info("Total proyectado %d: %d tránsitos",
             df_pred["anio"].iloc[0], int(df_pred["transitos_predichos"].sum()))

    return df_pred


def ejecutar() -> pd.DataFrame:
    return pronosticar()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    pronosticar()
