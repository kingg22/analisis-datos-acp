"""
preprocesamiento.py
===================

Persona 3 - Preprocesamiento y Análisis de Tendencias
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Granularidad: ANUAL (año fiscal de la ACP). Une los datasets de las fuentes
(canal por segmento + precio del petróleo por año fiscal), normaliza tipos,
maneja nulos y deriva features para el análisis exploratorio y el dashboard.

Si la segunda fuente no existe en disco, se genera un proxy anual de precios de
combustible para que el join sea demostrable sin bloquear el avance del equipo.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RUTA_PERSONA1 = Path(__file__).resolve().parents[2] / "persona1_ingesta" / "data" / "processed"
RUTA_BASE = Path(__file__).resolve().parents[1]
RUTA_RAW = RUTA_BASE / "data" / "raw"
RUTA_PROCESSED = RUTA_BASE / "data" / "processed"
RUTA_OUTPUT = RUTA_BASE / "output"

RUTA_CANAL_LIMPIO = RUTA_PERSONA1 / "canal_limpio.csv"
RUTA_CANAL_SERIE = RUTA_PERSONA1 / "canal_serie_anual.csv"
RUTA_FUENTE2 = RUTA_RAW / "fuente2_combustibles.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("preprocesamiento")


# ---------------------------------------------------------------------------
# 1. Carga de la Fuente 1 (Canal de Panamá) — anual por segmento
# ---------------------------------------------------------------------------
def cargar_canal() -> pd.DataFrame:
    """Lee canal_limpio.csv (anual por segmento) del módulo de Persona 1."""
    if not RUTA_CANAL_LIMPIO.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_CANAL_LIMPIO}. "
            "Ejecuta primero: python persona1_ingesta/src/ingesta_canal.py --modo oficial"
        )
    log.info("Cargando canal: %s", RUTA_CANAL_LIMPIO)
    df = pd.read_csv(RUTA_CANAL_LIMPIO)
    log.info("Canal cargado: %d filas, %d columnas", df.shape[0], df.shape[1])
    return df


# ---------------------------------------------------------------------------
# 2. Carga / generación de la Fuente 2 (precio del petróleo por año fiscal)
# ---------------------------------------------------------------------------
def _generar_fuente2_muestra(anios_fiscales: list[int]) -> pd.DataFrame:
    """Genera un proxy anual de precio del barril (respaldo, no datos reales)."""
    log.info("Fuente 2 no encontrada. Generando MUESTRA anual (proxy de precio).")
    # Promedios anuales aproximados por año fiscal (respaldo si no está la fuente real).
    referencia = {2020: 42, 2021: 55, 2022: 95, 2023: 82, 2024: 81, 2025: 76}
    filas = [
        {"anio_fiscal": af, "precio_barril_usd_prom": float(referencia.get(af, 70))}
        for af in anios_fiscales
    ]
    return pd.DataFrame(filas)


def cargar_fuente2(anios_fiscales: list[int]) -> tuple[pd.DataFrame, str]:
    """
    Carga la segunda fuente desde data/raw/fuente2_combustibles.csv.
    Si no existe, genera una muestra anual y la persiste.
    Devuelve el DataFrame y el origen ('real' | 'muestra').
    """
    if RUTA_FUENTE2.exists():
        log.info("Cargando Fuente 2 REAL: %s", RUTA_FUENTE2)
        df = pd.read_csv(RUTA_FUENTE2)
        origen = "real"
    else:
        df = _generar_fuente2_muestra(anios_fiscales)
        RUTA_RAW.mkdir(parents=True, exist_ok=True)
        df.to_csv(RUTA_FUENTE2, index=False, encoding="utf-8")
        log.info("Muestra de Fuente 2 persistida en: %s", RUTA_FUENTE2)
        origen = "muestra"

    df["anio_fiscal"] = pd.to_numeric(df["anio_fiscal"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["anio_fiscal"]).drop_duplicates(subset=["anio_fiscal"])
    df = df.sort_values("anio_fiscal").reset_index(drop=True)
    return df, origen


# ---------------------------------------------------------------------------
# 3. Normalización y manejo de nulos (Fuente 1)
# ---------------------------------------------------------------------------
def normalizar_canal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos, rellena nulos y deriva columnas útiles.

    Columnas derivadas:
      - periodo_sequia: 1 en el año fiscal de la sequía (FY2024).
      - periodo_recuperacion: 1 en el año fiscal de recuperación (FY2025).
      - ratio_toneladas_por_transito: toneladas_cp_suez / transitos.
      - peaje_por_tonelada_usd: peajes_usd / toneladas_cp_suez.
    """
    log.info("Normalizando dataset del canal")
    df = df.copy()

    for col in ("anio_fiscal", "transitos", "calado_promedio_pies",
                "toneladas_cp_suez", "peajes_usd"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    num_cols = df.select_dtypes(include=[np.number]).columns
    columnas_rellenables = num_cols.difference(["calado_promedio_pies"])
    nulos = int(df[columnas_rellenables].isna().sum().sum())
    if nulos:
        log.info("Rellenando %d nulos numéricos con 0", nulos)
        df[columnas_rellenables] = df[columnas_rellenables].fillna(0)

    # Flags de eventos macro (por año fiscal).
    df["periodo_sequia"] = (df["anio_fiscal"] == 2024).astype(int)
    df["periodo_recuperacion"] = (df["anio_fiscal"] == 2025).astype(int)

    df["ratio_toneladas_por_transito"] = np.where(
        df["transitos"] > 0, df["toneladas_cp_suez"] / df["transitos"], 0.0
    )
    df["peaje_por_tonelada_usd"] = np.where(
        df["toneladas_cp_suez"] > 0, df["peajes_usd"] / df["toneladas_cp_suez"], 0.0
    )
    return df


# ---------------------------------------------------------------------------
# 4. Join entre fuentes
# ---------------------------------------------------------------------------
def unir_fuentes(df_canal: pd.DataFrame, df_fuente2: pd.DataFrame) -> pd.DataFrame:
    """Left-join por anio_fiscal para añadir el contexto macro (precio del barril)."""
    log.info("Uniendo canal con Fuente 2 por anio_fiscal")
    df_f2 = df_fuente2[["anio_fiscal", "precio_barril_usd_prom"]].copy()
    df_f2["anio_fiscal"] = df_f2["anio_fiscal"].astype(int)
    df = df_canal.merge(df_f2, on="anio_fiscal", how="left")
    nulos = int(df["precio_barril_usd_prom"].isna().sum())
    if nulos:
        log.warning("%d filas sin precio (ffill/bfill)", nulos)
        df["precio_barril_usd_prom"] = df["precio_barril_usd_prom"].ffill().bfill()
    return df.sort_values(["anio_fiscal", "segmento"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 5. Agregaciones listas para el dashboard (Persona 5)
# ---------------------------------------------------------------------------
def agregaciones_para_dashboard(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Genera agregaciones anuales que Persona 5 puede consumir directamente."""
    log.info("Construyendo agregaciones para dashboard")

    # Serie anual total (todos los segmentos)
    serie_total = (
        df.groupby("anio_fiscal", as_index=False)
        .agg(
            transitos_totales=("transitos", "sum"),
            toneladas_totales=("toneladas_cp_suez", "sum"),
            peajes_totales_usd=("peajes_usd", "sum"),
            calado_promedio_pies=("calado_promedio_pies", "mean"),
            precio_barril_usd_prom=("precio_barril_usd_prom", "mean"),
        )
        .sort_values("anio_fiscal")
        .reset_index(drop=True)
    )

    # Composición por segmento (normalizado a %)
    por_segmento_anio = (
        df.groupby(["anio_fiscal", "segmento"], as_index=False)["transitos"].sum()
    )
    totales_anio = por_segmento_anio.groupby("anio_fiscal")["transitos"].transform("sum")
    por_segmento_anio["participacion_pct"] = (
        por_segmento_anio["transitos"] / totales_anio * 100
    ).round(2)

    # Comparativa sequía vs recuperación vs baseline
    df = df.copy()
    df["periodo"] = np.select(
        [df["periodo_sequia"] == 1, df["periodo_recuperacion"] == 1],
        ["sequia", "recuperacion"],
        default="baseline",
    )
    por_periodo = (
        df.groupby(["periodo", "segmento"], as_index=False)
        .agg(
            transitos_promedio=("transitos", "mean"),
            toneladas_promedio=("toneladas_cp_suez", "mean"),
            peajes_promedio_usd=("peajes_usd", "mean"),
        )
    )

    return {
        "serie_total": serie_total,
        "por_segmento_anio": por_segmento_anio,
        "por_periodo": por_periodo,
    }


# ---------------------------------------------------------------------------
# 6. Orquestación
# ---------------------------------------------------------------------------
def ejecutar() -> dict[str, pd.DataFrame]:
    """Ejecuta el flujo completo de preprocesamiento. Persiste CSVs en disco."""
    log.info("=== INICIO PREPROCESAMIENTO PERSONA 3 ===")
    RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)
    RUTA_OUTPUT.mkdir(parents=True, exist_ok=True)

    df_canal = cargar_canal()
    df_canal = normalizar_canal(df_canal)

    anios = sorted(df_canal["anio_fiscal"].unique().tolist())
    df_fuente2, origen = cargar_fuente2(anios)
    log.info("Fuente 2 origen: %s | %d filas", origen, df_fuente2.shape[0])

    df_unificado = unir_fuentes(df_canal, df_fuente2)

    ruta_unificado = RUTA_PROCESSED / "canal_unificado.csv"
    df_unificado.to_csv(ruta_unificado, index=False, encoding="utf-8")
    log.info("Dataset unificado guardado: %s (%d filas)", ruta_unificado, df_unificado.shape[0])

    aggs = agregaciones_para_dashboard(df_unificado)
    for nombre, tabla in aggs.items():
        ruta = RUTA_PROCESSED / f"agregado_{nombre}.csv"
        tabla.to_csv(ruta, index=False, encoding="utf-8")
        log.info("Agregado guardado: %s (%d filas)", ruta, tabla.shape[0])

    log.info("=== PREPROCESAMIENTO COMPLETADO ===")
    return {"canal_limpio": df_canal, "fuente2": df_fuente2, "unificado": df_unificado, **aggs}


if __name__ == "__main__":
    ejecutar()
