"""
preprocesamiento.py
===================

Persona 3 - Preprocesamiento y Análisis de Tendencias
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Une los datasets de las distintas fuentes (canal + segunda fuente opcional),
normaliza tipos, maneja nulos y deriva features para el análisis exploratorio
y el dashboard de Persona 5.

Si la segunda fuente no existe en disco, se genera un proxy de precios de
combustible (Brent) para que el join sea demostrable end-to-end sin bloquear
el avance del equipo.
"""

from __future__ import annotations

import logging
import os
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
RUTA_CANAL_SERIE = RUTA_PERSONA1 / "canal_serie_mensual.csv"
RUTA_FUENTE2 = RUTA_RAW / "fuente2_combustibles.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("preprocesamiento")


# ---------------------------------------------------------------------------
# 1. Carga de la Fuente 1 (Canal de Panamá)
# ---------------------------------------------------------------------------
def cargar_canal() -> pd.DataFrame:
    """Lee canal_limpio.csv desde el módulo de Persona 1."""
    if not RUTA_CANAL_LIMPIO.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_CANAL_LIMPIO}. "
            "Ejecuta primero: python persona1_ingesta/src/ingesta_canal.py --modo muestra"
        )
    log.info("Cargando canal: %s", RUTA_CANAL_LIMPIO)
    df = pd.read_csv(RUTA_CANAL_LIMPIO, parse_dates=["fecha"])
    log.info("Canal cargado: %d filas, %d columnas", df.shape[0], df.shape[1])
    return df


# ---------------------------------------------------------------------------
# 2. Carga / generación de la Fuente 2 (segunda fuente del pipeline)
# ---------------------------------------------------------------------------
def _generar_fuente2_muestra(fechas_canal: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Genera un proxy de precios mensuales de Brent como segunda fuente.
    Mismo rango temporal que el canal; correlacionado con la dinámica macro
    (caída 2020, subida 2022, normalización 2023-2024, recuperación 2025).
    """
    log.info("Fuente 2 no encontrada. Generando MUESTRA (Brent proxy).")
    rng = np.random.default_rng(7)
    filas = []
    precio = 60.0  # USD/barril inicial (oct-2019)
    for fecha in fechas_canal:
        # Tendencia macro realista
        if fecha.year == 2020:
            precio *= rng.normal(0.985, 0.02)  # caída COVID
        elif fecha.year == 2021:
            precio *= rng.normal(1.020, 0.015)  # recuperación
        elif fecha.year == 2022 and fecha.month <= 6:
            precio *= rng.normal(1.030, 0.020)  # shock Ucrania
        elif fecha.year == 2022 and fecha.month > 6:
            precio *= rng.normal(0.985, 0.015)
        elif fecha.year in (2023, 2024):
            precio *= rng.normal(1.000, 0.012)  # estabilización
        elif fecha.year >= 2025:
            precio *= rng.normal(0.995, 0.010)  # normalización
        precio = float(np.clip(precio, 25, 140))
        filas.append(
            {
                "fecha": fecha,
                "anio": fecha.year,
                "mes": fecha.month,
                "precio_barril_usd": round(precio, 2),
            }
        )
    return pd.DataFrame(filas)


def cargar_fuente2(fechas_canal: pd.DatetimeIndex) -> tuple[pd.DataFrame, str]:
    """
    Carga la segunda fuente desde data/raw/fuente2_combustibles.csv.
    Si no existe, genera una muestra y la persiste para reproducibilidad.
    Devuelve el DataFrame y un string indicando el origen ('real' | 'muestra').
    """
    if RUTA_FUENTE2.exists():
        log.info("Cargando Fuente 2 REAL: %s", RUTA_FUENTE2)
        df = pd.read_csv(RUTA_FUENTE2, parse_dates=["fecha"])
        origen = "real"
    else:
        df = _generar_fuente2_muestra(fechas_canal)
        RUTA_RAW.mkdir(parents=True, exist_ok=True)
        df.to_csv(RUTA_FUENTE2, index=False, encoding="utf-8")
        log.info("Muestra de Fuente 2 persistida en: %s", RUTA_FUENTE2)
        origen = "muestra"

    # Normalizar tipos mínimos
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    df = df.drop_duplicates(subset=["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    return df, origen


# ---------------------------------------------------------------------------
# 3. Normalización y manejo de nulos (Fuente 1)
# ---------------------------------------------------------------------------
def normalizar_canal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos, valida rangos, rellena nulos y deriva columnas útiles.

    Columnas derivadas:
      - anio, mes, anio_fiscal: ya presentes en canal_limpio.csv (se validan).
      - fase_fiscal: mes dentro del año fiscal ACP (oct=1 .. sep=12).
      - periodo_sequia: flag 1 durante la sequía 2023–may-2024.
      - periodo_recuperacion: flag 1 durante 2025+.
      - ratio_toneladas_por_transito: toneladas_cp_suez / transitos.
      - peaje_por_tonelada_usd: peajes_usd / toneladas_cp_suez.
    """
    log.info("Normalizando dataset del canal")
    df = df.copy()

    # Tipos
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    for col in ("anio", "mes", "anio_fiscal", "transitos",
                "calado_promedio_pies", "toneladas_cp_suez", "peajes_usd"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Nulos numéricos -> 0 (ya lo hace Persona 1, se reasegura)
    num_cols = df.select_dtypes(include=[np.number]).columns
    nulos = int(df[num_cols].isna().sum().sum())
    if nulos:
        log.info("Rellenando %d nulos numéricos con 0", nulos)
        df[num_cols] = df[num_cols].fillna(0)

    # Fase del año fiscal (oct=1 ... sep=12)
    df["fase_fiscal"] = ((df["mes"] - 10) % 12) + 1
    df["fase_fiscal"] = df["fase_fiscal"].astype(int)

    # Flags de eventos macro
    df["periodo_sequia"] = (
        ((df["anio"] == 2023) & (df["mes"] >= 6)) |
        ((df["anio"] == 2024) & (df["mes"] <= 5))
    ).astype(int)
    df["periodo_recuperacion"] = (df["anio"] >= 2025).astype(int)

    # Features derivados
    df["ratio_toneladas_por_transito"] = np.where(
        df["transitos"] > 0,
        df["toneladas_cp_suez"] / df["transitos"],
        0.0,
    )
    df["peaje_por_tonelada_usd"] = np.where(
        df["toneladas_cp_suez"] > 0,
        df["peajes_usd"] / df["toneladas_cp_suez"],
        0.0,
    )

    return df


# ---------------------------------------------------------------------------
# 4. Join entre fuentes
# ---------------------------------------------------------------------------
def unir_fuentes(df_canal: pd.DataFrame, df_fuente2: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join por (anio, mes) para enriquecer cada observación del canal
    con el contexto macro de la segunda fuente. Si la segunda fuente tiene
    un rango menor, los meses faltantes quedan con NaN y se rellenan.
    """
    log.info("Uniendo canal con Fuente 2 por (anio, mes)")
    df = df_canal.merge(
        df_fuente2[["anio", "mes", "precio_barril_usd"]],
        on=["anio", "mes"],
        how="left",
    )
    nulos_precio = int(df["precio_barril_usd"].isna().sum())
    if nulos_precio:
        log.warning("%d filas sin precio_barril_usd (forward-fill)", nulos_precio)
        df["precio_barril_usd"] = df["precio_barril_usd"].ffill().bfill()
    # Variación mensual del precio (proxy de presión sobre fletes)
    df = df.sort_values(["segmento", "fecha"]).reset_index(drop=True)
    df["precio_var_mensual_pct"] = (
        df.groupby("segmento")["precio_barril_usd"]
        .pct_change()
        .fillna(0)
        * 100
    )
    return df


# ---------------------------------------------------------------------------
# 5. Agregaciones listas para el dashboard (Persona 5)
# ---------------------------------------------------------------------------
def agregaciones_para_dashboard(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Genera agregaciones que Persona 5 puede consumir directamente."""
    log.info("Construyendo agregaciones para dashboard")

    # Serie mensual total (todos los segmentos)
    serie_total = (
        df.groupby("fecha", as_index=False)
        .agg(
            anio=("anio", "first"),
            mes=("mes", "first"),
            anio_fiscal=("anio_fiscal", "first"),
            transitos_totales=("transitos", "sum"),
            toneladas_totales=("toneladas_cp_suez", "sum"),
            peajes_totales_usd=("peajes_usd", "sum"),
            calado_promedio_pies=("calado_promedio_pies", "mean"),
            precio_barril_usd=("precio_barril_usd", "mean"),
        )
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    # Composición por segmento (top-N, normalizado a %)
    por_segmento_anio = (
        df.groupby(["anio", "segmento"], as_index=False)["transitos"].sum()
    )
    totales_anio = por_segmento_anio.groupby("anio")["transitos"].transform("sum")
    por_segmento_anio["participacion_pct"] = (
        por_segmento_anio["transitos"] / totales_anio * 100
    )

    # Por fase fiscal (estacionalidad)
    por_fase = (
        df.groupby(["fase_fiscal", "segmento"], as_index=False)["transitos"]
        .mean()
        .rename(columns={"transitos": "transitos_promedio"})
    )

    # Comparativa sequía vs recuperación vs baseline
    df["periodo"] = np.select(
        [
            df["periodo_sequia"] == 1,
            df["periodo_recuperacion"] == 1,
        ],
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
        "por_fase_fiscal": por_fase,
        "por_periodo": por_periodo,
    }


# ---------------------------------------------------------------------------
# 6. Orquestación
# ---------------------------------------------------------------------------
def ejecutar(origen_fuente2: str | None = None) -> dict[str, pd.DataFrame]:
    """
    Ejecuta el flujo completo de preprocesamiento.
    Devuelve un dict con los DataFrames clave; persiste CSVs en disco.
    """
    log.info("=== INICIO PREPROCESAMIENTO PERSONA 3 ===")
    RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)
    RUTA_OUTPUT.mkdir(parents=True, exist_ok=True)

    df_canal = cargar_canal()
    df_canal = normalizar_canal(df_canal)

    fechas_canal = pd.date_range(
        start=df_canal["fecha"].min(),
        end=df_canal["fecha"].max(),
        freq="MS",
    )
    df_fuente2, origen = cargar_fuente2(fechas_canal)
    log.info("Fuente 2 origen: %s | %d filas", origen, df_fuente2.shape[0])

    df_unificado = unir_fuentes(df_canal, df_fuente2)

    # Persistir dataset unificado
    ruta_unificado = RUTA_PROCESSED / "canal_unificado.csv"
    df_unificado.to_csv(ruta_unificado, index=False, encoding="utf-8")
    log.info("Dataset unificado guardado: %s (%d filas)", ruta_unificado, df_unificado.shape[0])

    aggs = agregaciones_para_dashboard(df_unificado)
    for nombre, tabla in aggs.items():
        ruta = RUTA_PROCESSED / f"agregado_{nombre}.csv"
        tabla.to_csv(ruta, index=False, encoding="utf-8")
        log.info("Agregado guardado: %s (%d filas)", ruta, tabla.shape[0])

    log.info("=== PREPROCESAMIENTO COMPLETADO ===")
    return {
        "canal_limpio": df_canal,
        "fuente2": df_fuente2,
        "unificado": df_unificado,
        **aggs,
    }


if __name__ == "__main__":
    ejecutar()
