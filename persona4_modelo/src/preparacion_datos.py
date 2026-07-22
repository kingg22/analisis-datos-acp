"""
preparacion_datos.py
====================

Persona 4 - Preparación de datos para el modelo predictivo.

Construye un **panel segmento × año fiscal** a partir de los datos oficiales de
la ACP (Persona 1) enriquecidos con el precio del crudo (Persona 2).

¿Por qué a nivel de segmento y no del total anual?
--------------------------------------------------
La serie de totales anuales tiene solo 6 puntos (FY2020–FY2025): con esa muestra
ningún modelo puede aprender y un simple promedio gana por defecto. La ACP, sin
embargo, publica el desglose **por segmento de mercado**, lo que multiplica por
10 la información disponible (10 segmentos × 6 años = 60 observaciones reales,
sin inventar ni interpolar ningún dato).

Esto además es más informativo para el negocio: la sequía de FY2024 no afectó a
todos los segmentos por igual (el GNL cayó ~72 % mientras los portacontenedores
apenas se movieron), y un modelo por segmento puede aprender justamente eso.
El volumen anual total se obtiene sumando la predicción de los 10 segmentos.

Features
--------
  - segmento (one-hot):        identidad del segmento de mercado
  - precio_barril_usd_prom:    exógeno macro (segunda fuente, promedio anual)
  - sequia:                    régimen operativo (1 en FY2024, 0 el resto)

Se excluye deliberadamente el año fiscal como variable numérica: los modelos de
árboles no pueden extrapolar a un año no visto y su inclusión degradó el error
en validación (ver `docs/METODOLOGIA.md §3`).

Target: `transitos` (tránsitos del segmento en ese año fiscal).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger("persona4.preparacion")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE_SEGMENTOS = (
    RAIZ / "persona1_ingesta" / "data" / "raw" / "acp_transitos_por_segmento_af.csv"
)
FUENTE_PRECIO = (
    RAIZ / "persona2_pipeline" / "data" / "processed" / "dataset_unificado.csv"
)
SALIDA_PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"

TARGET = "transitos"
EXOGENAS = ["precio_barril_usd_prom", "sequia"]

# Años fiscales con restricciones de calado por la sequía del lago Gatún.
# FY2024 es el año del racionamiento severo (ver persona3_analisis/docs/HALLAZGOS.md).
ANIOS_SEQUIA = (2024,)


def cargar_panel() -> pd.DataFrame:
    """Carga el panel segmento × año fiscal con el precio del crudo anexado."""
    if not FUENTE_SEGMENTOS.exists():
        raise FileNotFoundError(
            f"No se encontró {FUENTE_SEGMENTOS.name}. Ejecuta primero "
            "`python persona1_ingesta/src/construir_datos_acp.py`."
        )
    if not FUENTE_PRECIO.exists():
        raise FileNotFoundError(
            f"No se encontró {FUENTE_PRECIO.name}. Ejecuta primero "
            "`python persona2_pipeline/src/pipeline.py`."
        )

    seg = pd.read_csv(FUENTE_SEGMENTOS)
    precio = pd.read_csv(FUENTE_PRECIO)[["anio_fiscal", "precio_barril_usd_prom"]]

    df = seg.merge(precio, on="anio_fiscal", how="left")
    df = df.sort_values(["segmento", "anio_fiscal"]).reset_index(drop=True)

    log.info(
        "Panel cargado: %d observaciones (%d segmentos × %d años fiscales, FY%d→FY%d)",
        len(df),
        df["segmento"].nunique(),
        df["anio_fiscal"].nunique(),
        int(df["anio_fiscal"].min()),
        int(df["anio_fiscal"].max()),
    )
    return df


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Añade el indicador de régimen y completa el exógeno de precio."""
    df = df.copy()
    df["sequia"] = df["anio_fiscal"].isin(ANIOS_SEQUIA).astype(int)
    df["precio_barril_usd_prom"] = df["precio_barril_usd_prom"].ffill().bfill()
    return df


def matriz_features(df: pd.DataFrame, columnas_ref: list[str] | None = None) -> pd.DataFrame:
    """
    Convierte el panel en la matriz X (one-hot de segmento + exógenas).

    `columnas_ref` fuerza el mismo orden/conjunto de columnas que en el
    entrenamiento; es imprescindible al predecir años futuros.
    """
    X = pd.get_dummies(df[["segmento"] + EXOGENAS], columns=["segmento"])
    if columnas_ref is not None:
        X = X.reindex(columns=columnas_ref, fill_value=0)
    return X


def preparar(persistir: bool = True) -> pd.DataFrame:
    """Pipeline completo de preparación. Devuelve el panel modelable."""
    df = construir_features(cargar_panel())
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
