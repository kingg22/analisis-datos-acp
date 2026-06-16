"""
preparacion_datos.py
====================

Persona 4 - Preparación de datos para el modelo predictivo.

Carga el dataset unificado de Persona 2 (`dataset_unificado.csv`: serie mensual
de tránsitos totales + precio del barril) y construye la matriz de features
para predecir el volumen mensual de tránsitos del Canal de Panamá.

Features generados:
  - Calendario:   mes_sin, mes_cos (estacionalidad cíclica), indice_tendencia
  - Régimen:      periodo_sequia, periodo_recuperacion (derivados de la fecha,
                  según las definiciones de HALLAZGOS.md de Persona 3)
  - Autorregresivos: lag_1, lag_12 (tránsitos de hace 1 y 12 meses), media_movil_3
  - Exógenos:     precio_barril_usd, precio_barril_usd_ma3

El target es `transitos_totales`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("persona4.preparacion")

# --- Rutas ------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[2]
# Fuente principal: dataset unificado de Persona 2 (serie mensual total).
FUENTE_P2 = RAIZ / "persona2_pipeline" / "data" / "processed" / "dataset_unificado.csv"
# Respaldo: agregado de serie total de Persona 3 (sólo tránsitos, sin precio).
FUENTE_P3 = RAIZ / "persona3_analisis" / "data" / "processed" / "agregado_serie_total.csv"

SALIDA_PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

# --- Definición de regímenes (alineado con Persona 3 / HALLAZGOS.md) --------
SEQUIA_INICIO = pd.Timestamp("2023-06-01")
SEQUIA_FIN = pd.Timestamp("2024-05-01")
RECUPERACION_INICIO = pd.Timestamp("2025-01-01")

TARGET = "transitos_totales"


def cargar_serie() -> pd.DataFrame:
    """Carga la serie mensual de tránsitos + precio del barril.

    Usa el dataset de Persona 2 si existe; si no, recae en el agregado de
    Persona 3 (sin precio) para no bloquear el desarrollo.
    """
    if FUENTE_P2.exists():
        log.info("Cargando fuente principal (Persona 2): %s", FUENTE_P2.name)
        df = pd.read_csv(FUENTE_P2, parse_dates=["fecha"])
    elif FUENTE_P3.exists():
        log.warning("Fuente de Persona 2 no encontrada; usando respaldo de Persona 3.")
        df = pd.read_csv(FUENTE_P3, parse_dates=["fecha"])
        # Homologar nombre de la columna de tránsitos.
        for col in ("transitos", "transitos_totales", "total_transitos"):
            if col in df.columns:
                df = df.rename(columns={col: TARGET})
                break
        df["precio_barril_usd"] = np.nan
        df["precio_barril_usd_ma3"] = np.nan
    else:
        raise FileNotFoundError(
            "No se encontró ninguna fuente. Ejecuta primero el pipeline de "
            "Persona 2 (python persona2_pipeline/src/pipeline.py)."
        )

    df = df.sort_values("fecha").reset_index(drop=True)
    if "anio" not in df.columns:
        df["anio"] = df["fecha"].dt.year
    if "mes" not in df.columns:
        df["mes"] = df["fecha"].dt.month
    log.info("Serie cargada: %d meses (%s → %s)",
             len(df), df["fecha"].min().date(), df["fecha"].max().date())
    return df


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Añade features de calendario, régimen y autorregresivos."""
    df = df.copy()

    # --- Calendario / estacionalidad cíclica -------------------------------
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    # Índice de tendencia: 0, 1, 2, ... (número de mes desde el inicio).
    df["indice_tendencia"] = np.arange(len(df))

    # --- Regímenes (sequía / recuperación) ---------------------------------
    df["periodo_sequia"] = (
        (df["fecha"] >= SEQUIA_INICIO) & (df["fecha"] <= SEQUIA_FIN)
    ).astype(int)
    df["periodo_recuperacion"] = (df["fecha"] >= RECUPERACION_INICIO).astype(int)

    # --- Autorregresivos ----------------------------------------------------
    df["lag_1"] = df[TARGET].shift(1)
    df["lag_12"] = df[TARGET].shift(12)
    df["media_movil_3"] = df[TARGET].shift(1).rolling(window=3).mean()

    # --- Exógenos (precio) --------------------------------------------------
    # Si la fuente de Persona 2 no trae precio, se rellena hacia adelante/atrás.
    for col in ("precio_barril_usd", "precio_barril_usd_ma3"):
        if col not in df.columns:
            df[col] = np.nan
        df[col] = df[col].ffill().bfill()

    return df


# Orden canónico de features usado por el modelo.
COLUMNAS_FEATURES = [
    "mes_sin",
    "mes_cos",
    "indice_tendencia",
    "periodo_sequia",
    "periodo_recuperacion",
    "lag_1",
    "lag_12",
    "media_movil_3",
    "precio_barril_usd",
    "precio_barril_usd_ma3",
]


def preparar(persistir: bool = True) -> pd.DataFrame:
    """Pipeline completo de preparación. Devuelve el dataframe modelable.

    Elimina las filas iniciales sin `lag_12` (primeros 12 meses), que no son
    utilizables para entrenamiento.
    """
    df = cargar_serie()
    df = construir_features(df)

    n_antes = len(df)
    df = df.dropna(subset=["lag_12", "media_movil_3"]).reset_index(drop=True)
    log.info("Filas modelables: %d (se descartaron %d sin lag_12/media_movil)",
             len(df), n_antes - len(df))

    if persistir:
        SALIDA_PROCESSED.mkdir(parents=True, exist_ok=True)
        destino = SALIDA_PROCESSED / "dataset_modelo.csv"
        df.to_csv(destino, index=False)
        log.info("Dataset modelable guardado en %s", destino)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    preparar()
