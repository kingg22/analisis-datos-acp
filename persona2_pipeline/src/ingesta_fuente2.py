"""
ingesta_fuente2.py
==================
Ingesta de la segunda fuente de datos: precios del petróleo crudo, agregados a
promedio por AÑO FISCAL de la ACP (oct–sep).

Responsable: PERSONA 2 - Ingesta de Datos (Fuente 2) + Pipeline
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

FUENTE PÚBLICA:
  International Monetary Fund (IMF) — Primary Commodity Price System (PCPS).
  API SDMX JSON, sin clave de acceso requerida.
  Indicador: POILAPSP (Crude Oil, average spot price, USD/barril).

Granularidad: la API entrega datos mensuales; aquí se promedian por año fiscal
de la ACP para alinearlos con la Fuente 1 (tránsitos anuales del Canal).

Relación precio del petróleo ↔ Canal de Panamá:
  - Precio alto → mayor costo de combustible → las navieras priorizan rutas
    cortas (como el Canal) → presión sobre la demanda de tránsitos.
  Esta variable es un insumo (exógeno) para el modelo predictivo de Persona 4.

Modos de ejecución:
  --modo api     : Datos reales. Intenta la API del FMI y, si falla, FRED
                   (Brent, Federal Reserve de St. Louis). Recomendado.
  --modo muestra : Genera datos sintéticos si no hay conexión.
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# -------------------------------------------------------------------------
# Rutas
# -------------------------------------------------------------------------
RUTA_BASE = Path(__file__).resolve().parents[1]
RUTA_RAW = RUTA_BASE / "data" / "raw"
RUTA_PROCESSED = RUTA_BASE / "data" / "processed"

# Ruta donde Persona 3 espera la segunda fuente
RUTA_PERSONA3_RAW = (
    Path(__file__).resolve().parents[2] / "persona3_analisis" / "data" / "raw"
)

# Años fiscales cubiertos por la Fuente 1 (tránsitos ACP).
ANIOS_FISCALES = list(range(2020, 2026))  # FY2020 (oct-2019) ... FY2025 (sep-2025)

# Rango mensual que cubre esos años fiscales (oct-2019 a sep-2025).
FECHA_INICIO = "2019-10-01"
FECHA_FIN = "2025-09-01"

# IMF PCPS — SDMX JSON endpoint (sin clave). Se piden los meses que cubren
# todos los años fiscales del proyecto (oct-2019 a sep-2025).
IMF_URL = (
    "https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData"
    "/PCPS/M.W0.POILAPSP.USD"
    "?startPeriod=2019-10&endPeriod=2025-09"
)

# FRED (Federal Reserve St. Louis) — Brent Crude mensual (fallback real)
# POILBREUSDM: Europe Brent Spot Price FOB (USD/barril), sin clave de API
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=POILBREUSDM"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("ingesta_fuente2")


def a_anio_fiscal(fecha: pd.Timestamp) -> int:
    """Año fiscal ACP: oct–sep. Oct-2024..Sep-2025 -> FY2025."""
    return fecha.year + 1 if fecha.month >= 10 else fecha.year


# -------------------------------------------------------------------------
# 1. Descarga desde la API SDMX del FMI (mensual)
# -------------------------------------------------------------------------
def descargar_desde_imf(timeout: int = 30) -> pd.DataFrame:
    """Llama a la API del FMI y retorna precios mensuales del crudo (USD/barril)."""
    log.info("Consultando API FMI PCPS: %s", IMF_URL)
    respuesta = requests.get(IMF_URL, timeout=timeout, headers={"Accept": "application/json"})
    respuesta.raise_for_status()
    datos = respuesta.json()

    try:
        dataset = datos["CompactData"]["DataSet"]
        serie = dataset["Series"]
        if isinstance(serie, list):
            serie = serie[0]
        obs_raw = serie["Obs"]
        if isinstance(obs_raw, dict):
            obs_raw = [obs_raw]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Estructura JSON inesperada de la API FMI. Detalle: {exc}") from exc

    filas = []
    for obs in obs_raw:
        periodo = obs.get("@TIME_PERIOD", "")
        valor = obs.get("@OBS_VALUE", None)
        if not periodo or valor is None:
            continue
        try:
            fecha = pd.to_datetime(periodo + "-01")
            filas.append({"fecha": fecha, "precio_barril_usd": float(valor)})
        except (ValueError, TypeError):
            log.warning("Observación omitida (formato inválido): %s", obs)

    if not filas:
        raise ValueError("La API del FMI devolvió cero observaciones válidas.")

    df = pd.DataFrame(filas).sort_values("fecha").reset_index(drop=True)
    log.info("API FMI: %d observaciones mensuales descargadas.", len(df))
    return df


# -------------------------------------------------------------------------
# 1b. Descarga desde FRED (fallback real cuando IMF no está disponible)
# -------------------------------------------------------------------------
def descargar_desde_fred(timeout: int = 30) -> pd.DataFrame:
    """
    Descarga precios mensuales del petróleo Brent desde FRED
    (Federal Reserve Bank of St. Louis). No requiere clave de API.
    Serie: POILBREUSDM — Europe Brent Spot Price FOB, USD/barril.
    """
    log.info("Consultando FRED (fallback real): %s", FRED_URL)
    respuesta = requests.get(
        FRED_URL,
        timeout=timeout,
        headers={"Accept": "text/csv"},
    )
    respuesta.raise_for_status()

    from io import StringIO
    df_raw = pd.read_csv(StringIO(respuesta.text), parse_dates=["observation_date"])
    df_raw = df_raw.rename(
        columns={"observation_date": "fecha", "POILBREUSDM": "precio_barril_usd"}
    )
    df_raw["precio_barril_usd"] = pd.to_numeric(
        df_raw["precio_barril_usd"], errors="coerce"
    )
    df_raw = df_raw.dropna(subset=["precio_barril_usd"])
    df_raw = df_raw[
        (df_raw["fecha"] >= FECHA_INICIO) & (df_raw["fecha"] <= FECHA_FIN)
    ].reset_index(drop=True)

    if df_raw.empty:
        raise ValueError("FRED devolvió cero observaciones en el rango requerido.")

    log.info("FRED: %d observaciones descargadas.", len(df_raw))
    return df_raw[["fecha", "precio_barril_usd"]]


# -------------------------------------------------------------------------
# 2. Modo muestra (datos sintéticos, respaldo)
# -------------------------------------------------------------------------
def data_muestra() -> pd.DataFrame:
    """
    Genera precios mensuales de petróleo crudo (proxy) como respaldo.
    Refleja la dinámica macro real: caída COVID 2020, pico Ucrania 2022,
    estabilización 2023-2024, ligera baja 2025.
    """
    log.info("Generando datos de MUESTRA de precios de petróleo (respaldo).")
    rng = np.random.default_rng(42)
    fechas = pd.date_range(start="2019-10-01", end="2025-09-01", freq="MS")
    filas = []
    precio = 60.0
    for fecha in fechas:
        y, m = fecha.year, fecha.month
        if y == 2020 and m <= 4:
            mu, sigma = 0.870, 0.035
        elif y == 2020 and m > 4:
            mu, sigma = 1.020, 0.020
        elif y == 2021:
            mu, sigma = 1.025, 0.015
        elif y == 2022 and m <= 6:
            mu, sigma = 1.040, 0.025
        elif y == 2022 and m > 6:
            mu, sigma = 0.975, 0.018
        elif y in (2023, 2024):
            mu, sigma = 0.998, 0.012
        else:
            mu, sigma = 0.993, 0.010
        precio = float(np.clip(precio * rng.normal(mu, sigma), 20.0, 130.0))
        filas.append({"fecha": fecha, "precio_barril_usd": round(precio, 2)})
    df = pd.DataFrame(filas)
    log.info("Muestra generada: %d filas mensuales.", len(df))
    return df


# -------------------------------------------------------------------------
# 3. Agregación a año fiscal
# -------------------------------------------------------------------------
def agregar_anual(df_mensual: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte la serie mensual en un promedio por año fiscal de la ACP.
    Devuelve columnas: anio_fiscal, precio_barril_usd_prom, var_anual_pct.
    """
    df = df_mensual.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha", "precio_barril_usd"]).drop_duplicates(subset=["fecha"])
    df["anio_fiscal"] = df["fecha"].apply(a_anio_fiscal)

    # Sólo años fiscales completos cubiertos por la Fuente 1.
    df = df[df["anio_fiscal"].isin(ANIOS_FISCALES)]

    anual = (
        df.groupby("anio_fiscal", as_index=False)["precio_barril_usd"]
        .mean()
        .rename(columns={"precio_barril_usd": "precio_barril_usd_prom"})
        .sort_values("anio_fiscal")
        .reset_index(drop=True)
    )
    anual["precio_barril_usd_prom"] = anual["precio_barril_usd_prom"].round(2)
    anual["var_anual_pct"] = (anual["precio_barril_usd_prom"].pct_change() * 100).round(2)
    log.info("Precios agregados a %d años fiscales.", len(anual))
    return anual


# -------------------------------------------------------------------------
# 4. Persistencia
# -------------------------------------------------------------------------
def guardar(df: pd.DataFrame) -> None:
    """Persiste la fuente anual en persona2 (raw) y en persona3 (raw)."""
    RUTA_RAW.mkdir(parents=True, exist_ok=True)
    RUTA_PERSONA3_RAW.mkdir(parents=True, exist_ok=True)

    ruta_raw = RUTA_RAW / "fuente2_raw.csv"
    df.to_csv(ruta_raw, index=False, encoding="utf-8")
    log.info("Guardado raw local: %s (%d filas)", ruta_raw, len(df))

    ruta_p3 = RUTA_PERSONA3_RAW / "fuente2_combustibles.csv"
    df[["anio_fiscal", "precio_barril_usd_prom"]].to_csv(ruta_p3, index=False, encoding="utf-8")
    log.info("Guardado para Persona 3: %s", ruta_p3)


# -------------------------------------------------------------------------
# 5. Entry point
# -------------------------------------------------------------------------
def main(modo: str = "api") -> pd.DataFrame:
    log.info("=== PERSONA 2 — Ingesta Fuente 2 (anual) | modo: %s ===", modo)

    if modo == "api":
        df_mensual = None
        try:
            df_mensual = descargar_desde_imf()
        except Exception as exc:
            log.warning("API FMI no disponible (%s). Intentando FRED (fallback real).", exc)
        if df_mensual is None:
            try:
                df_mensual = descargar_desde_fred()
            except Exception as exc2:
                log.warning("FRED tampoco disponible (%s). Cambiando a modo muestra.", exc2)
                df_mensual = data_muestra()
    else:
        df_mensual = data_muestra()

    df = agregar_anual(df_mensual)
    guardar(df)
    log.info("=== Ingesta Fuente 2 completada: %d años fiscales ===", len(df))
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingesta Fuente 2 — Precios de Petróleo Crudo (FMI PCPS), anual"
    )
    parser.add_argument(
        "--modo",
        choices=["api", "muestra"],
        default="api",
        help="'api' descarga datos reales del FMI; 'muestra' genera un respaldo sintético.",
    )
    args = parser.parse_args()
    main(modo=args.modo)
