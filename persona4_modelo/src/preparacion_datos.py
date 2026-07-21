"""
preparacion_datos.py
====================

Persona 4 - Preparación de datos para el modelo predictivo (ANUAL).

Carga el dataset unificado de Persona 2 (`dataset_unificado.csv`: serie anual de
tránsitos totales + precio promedio del barril por año fiscal) y construye la
matriz de features para predecir el volumen ANUAL de tránsitos del Canal.

Contexto: la ACP publica el desglose por segmento a nivel anual, por lo que la
serie tiene pocos puntos (un año fiscal por observación). En consecuencia el
modelo es simple e interpretable (tendencia lineal + precio), y se valida con
Leave-One-Out (validación adecuada para muestras pequeñas).

Features:
  - indice_tendencia:        0, 1, 2, ... (posición del año fiscal en la serie)
  - precio_barril_usd_prom:  exógeno (segunda fuente, promedio anual)

Target: `transitos_totales`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("persona4.preparacion")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE_P2 = RAIZ / "persona2_pipeline" / "data" / "processed" / "dataset_unificado.csv"
FUENTE_P3 = RAIZ / "persona3_analisis" / "data" / "processed" / "agregado_serie_total.csv"
SALIDA_PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

TARGET = "transitos_totales"
COLUMNAS_FEATURES = ["indice_tendencia", "precio_barril_usd_prom"]


def cargar_serie() -> pd.DataFrame:
    """Carga la serie anual de tránsitos + precio del barril por año fiscal."""
    if FUENTE_P2.exists():
        log.info("Cargando fuente principal (Persona 2): %s", FUENTE_P2.name)
        df = pd.read_csv(FUENTE_P2)
    elif FUENTE_P3.exists():
        log.warning("Fuente de Persona 2 no encontrada; usando respaldo de Persona 3.")
        df = pd.read_csv(FUENTE_P3)
        for col in ("transitos", "transitos_totales", "total_transitos"):
            if col in df.columns:
                df = df.rename(columns={col: TARGET})
                break
        if "precio_barril_usd_prom" not in df.columns:
            df["precio_barril_usd_prom"] = np.nan
    else:
        raise FileNotFoundError(
            "No se encontró ninguna fuente. Ejecuta primero el pipeline de "
            "Persona 2 (python persona2_pipeline/src/pipeline.py)."
        )

    df = df.sort_values("anio_fiscal").reset_index(drop=True)
    log.info("Serie cargada: %d años fiscales (%d → %d)",
             len(df), int(df["anio_fiscal"].min()), int(df["anio_fiscal"].max()))
    return df


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Añade el índice de tendencia y asegura el exógeno de precio."""
    df = df.copy()
    df["indice_tendencia"] = np.arange(len(df))
    if "precio_barril_usd_prom" not in df.columns:
        df["precio_barril_usd_prom"] = np.nan
    df["precio_barril_usd_prom"] = df["precio_barril_usd_prom"].ffill().bfill()
    return df


def preparar(persistir: bool = True) -> pd.DataFrame:
    """Pipeline completo de preparación. Devuelve el dataframe modelable."""
    df = construir_features(cargar_serie())
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)
    log.info("Filas modelables: %d", len(df))

    if persistir:
        SALIDA_PROCESSED.mkdir(parents=True, exist_ok=True)
        destino = SALIDA_PROCESSED / "dataset_modelo.csv"
        df.to_csv(destino, index=False)
        log.info("Dataset modelable guardado en %s", destino)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    preparar()
