"""
ingesta_fuente2.py
==================
Ingesta de la segunda fuente de datos: precios mensuales del petróleo crudo.

Responsable: PERSONA 2 - Ingesta de Datos (Fuente 2) + Pipeline
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

FUENTE PÚBLICA:
  International Monetary Fund (IMF) — Primary Commodity Price System (PCPS).
  API SDMX JSON, sin clave de acceso requerida.
  Indicador: POILAPSP (Crude Oil, average spot price, USD/barril).
  URL: https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/
       PCPS/M.W0.POILAPSP.USD?startPeriod=2019-10&endPeriod=2025-12

Relación precio del petróleo ↔ Canal de Panamá:
  - Precio alto → mayor costo de combustible → las navieras priorizan rutas
    cortas (como el Canal) para reducir millas navegadas → presión alcista en
    demanda de tránsitos.
  - El pico de 2022 (guerra Ucrania) coincide con repunte de tránsitos.
  - La sequía 2023-2024 añadió restricciones de calado sobre esa demanda.
  Esta variable es un insumo clave para el modelo predictivo de Persona 4.

Modos de ejecución:
  --modo api     : Descarga datos reales desde la API del FMI (recomendado).
  --modo muestra : Genera datos sintéticos si la API no está disponible.
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

# Ruta donde Persona 3 espera la segunda fuente (preprocesamiento.py l.39)
RUTA_PERSONA3_RAW = (
    Path(__file__).resolve().parents[2]
    / "persona3_analisis"
    / "data"
    / "raw"
)

# Rango temporal idéntico al de canal_serie_mensual.csv de Persona 1
FECHA_INICIO = "2019-10-01"
FECHA_FIN = "2025-12-01"

# IMF PCPS — SDMX JSON endpoint (sin clave)
IMF_URL = (
    "https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData"
    "/PCPS/M.W0.POILAPSP.USD"
    "?startPeriod=2019-10&endPeriod=2025-12"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("ingesta_fuente2")


# -------------------------------------------------------------------------
# 1. Descarga desde la API SDMX del FMI
# -------------------------------------------------------------------------
def descargar_desde_imf(timeout: int = 30) -> pd.DataFrame:
    """
    Llama a la API SDMX JSON del FMI y retorna los precios mensuales
    del petróleo crudo promedio (POILAPSP) en USD/barril.
    """
    log.info("Consultando API FMI PCPS: %s", IMF_URL)
    respuesta = requests.get(
        IMF_URL,
        timeout=timeout,
        headers={"Accept": "application/json"},
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    # La estructura SDMX JSON es:
    # CompactData → DataSet → Series → Obs (lista de {"@TIME_PERIOD": "YYYY-MM", "@OBS_VALUE": "XX.XX"})
    try:
        dataset = datos["CompactData"]["DataSet"]
        serie = dataset["Series"]
        # Series puede ser una lista (varios indicadores) o un dict único
        if isinstance(serie, list):
            serie = serie[0]
        obs_raw = serie["Obs"]
        # Obs puede ser dict único si solo hay una observación
        if isinstance(obs_raw, dict):
            obs_raw = [obs_raw]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"Estructura JSON inesperada de la API FMI. Detalle: {exc}"
        ) from exc

    filas = []
    for obs in obs_raw:
        periodo = obs.get("@TIME_PERIOD", "")  # "2019-10"
        valor = obs.get("@OBS_VALUE", None)
        if not periodo or valor is None:
            continue
        try:
            fecha = pd.to_datetime(periodo + "-01")
            filas.append({"fecha": fecha, "precio_barril_usd": float(valor)})
        except (ValueError, TypeError):
            log.warning("Observación omitida (formato inválido): %s", obs)

    if not filas:
        raise ValueError(
            "La API del FMI devolvió cero observaciones válidas. "
            "Prueba --modo muestra o verifica la conectividad."
        )

    df = pd.DataFrame(filas).sort_values("fecha").reset_index(drop=True)
    log.info("API FMI: %d observaciones descargadas (oct-2019 a dic-2025).", len(df))
    return df


# -------------------------------------------------------------------------
# 2. Modo muestra (datos sintéticos coherentes con la realidad)
# -------------------------------------------------------------------------
def data_muestra() -> pd.DataFrame:
    """
    Genera precios mensuales de petróleo crudo (proxy Brent) como muestra.

    Dinámica macro real reflejada:
      oct-2019 : ~60 USD/barril (punto de partida)
      2020      : caída COVID — colapso a ~20 USD (abr-2020), recuperación
      2021      : recuperación progresiva hasta ~80 USD
      ene-jun 2022 : pico guerra Ucrania (~120 USD en jun)
      jul-dic 2022 : corrección (-15 %)
      2023-2024 : estabilización 75-85 USD
      2025      : ligera tendencia a la baja, 70-78 USD
    """
    log.info("Generando datos de MUESTRA de precios de petróleo (Brent proxy).")
    rng = np.random.default_rng(42)

    fechas = pd.date_range(start=FECHA_INICIO, end=FECHA_FIN, freq="MS")
    filas = []
    precio = 60.0

    for fecha in fechas:
        y, m = fecha.year, fecha.month
        if y == 2020 and m <= 4:
            mu, sigma = 0.870, 0.035   # caída COVID
        elif y == 2020 and m > 4:
            mu, sigma = 1.020, 0.020   # rebote post-mínimo
        elif y == 2021:
            mu, sigma = 1.025, 0.015   # recuperación
        elif y == 2022 and m <= 6:
            mu, sigma = 1.040, 0.025   # shock Ucrania
        elif y == 2022 and m > 6:
            mu, sigma = 0.975, 0.018   # corrección
        elif y in (2023, 2024):
            mu, sigma = 0.998, 0.012   # estabilización
        else:                           # 2025
            mu, sigma = 0.993, 0.010

        precio = float(np.clip(precio * rng.normal(mu, sigma), 20.0, 130.0))
        filas.append({"fecha": fecha, "precio_barril_usd": round(precio, 2)})

    df = pd.DataFrame(filas)
    log.info("Muestra generada: %d filas.", len(df))
    return df


# -------------------------------------------------------------------------
# 3. Limpieza y enriquecimiento
# -------------------------------------------------------------------------
def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos, elimina duplicados, filtra al rango de Persona 1
    y deriva columnas analíticas útiles para Personas 3 y 4.
    """
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha", "precio_barril_usd"])
    df = df.drop_duplicates(subset=["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)

    # Alinear con el rango temporal de Persona 1
    mask = (df["fecha"] >= FECHA_INICIO) & (df["fecha"] <= FECHA_FIN)
    df = df.loc[mask].reset_index(drop=True)

    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    # Variación mensual porcentual (útil como feature para ML en Persona 4)
    df["var_mensual_pct"] = df["precio_barril_usd"].pct_change().round(4)

    # Media móvil de 3 meses (suaviza ruido para análisis de tendencias)
    df["precio_barril_usd_ma3"] = (
        df["precio_barril_usd"].rolling(3, min_periods=1).mean().round(2)
    )

    # Columna de origen
    return df[[
        "fecha", "anio", "mes",
        "precio_barril_usd", "var_mensual_pct", "precio_barril_usd_ma3",
    ]]


# -------------------------------------------------------------------------
# 4. Persistencia
# -------------------------------------------------------------------------
def guardar(df: pd.DataFrame) -> None:
    """
    Persiste los datos en dos ubicaciones:
      - persona2_pipeline/data/raw/fuente2_raw.csv  (copia completa local)
      - persona3_analisis/data/raw/fuente2_combustibles.csv
        (formato esperado por preprocesamiento.py de Persona 3)
    """
    RUTA_RAW.mkdir(parents=True, exist_ok=True)
    RUTA_PERSONA3_RAW.mkdir(parents=True, exist_ok=True)

    ruta_raw = RUTA_RAW / "fuente2_raw.csv"
    df.to_csv(ruta_raw, index=False, encoding="utf-8")
    log.info("Guardado raw local: %s (%d filas)", ruta_raw, len(df))

    # Persona 3 solo necesita: fecha, anio, mes, precio_barril_usd
    df_p3 = df[["fecha", "anio", "mes", "precio_barril_usd"]].copy()
    ruta_p3 = RUTA_PERSONA3_RAW / "fuente2_combustibles.csv"
    df_p3.to_csv(ruta_p3, index=False, encoding="utf-8")
    log.info("Guardado para Persona 3: %s", ruta_p3)


# -------------------------------------------------------------------------
# 5. Entry point
# -------------------------------------------------------------------------
def main(modo: str = "api") -> pd.DataFrame:
    log.info("=== PERSONA 2 — Ingesta Fuente 2 | modo: %s ===", modo)

    if modo == "api":
        try:
            df_raw = descargar_desde_imf()
        except Exception as exc:
            log.warning("API FMI no disponible (%s). Cambiando a modo muestra.", exc)
            df_raw = data_muestra()
    else:
        df_raw = data_muestra()

    df = limpiar(df_raw)
    guardar(df)
    log.info("=== Ingesta Fuente 2 completada: %d registros ===", len(df))
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingesta Fuente 2 — Precios de Petróleo Crudo (FMI PCPS)"
    )
    parser.add_argument(
        "--modo",
        choices=["api", "muestra"],
        default="api",
        help=(
            "'api' descarga datos reales del FMI (sin clave, requiere internet). "
            "'muestra' genera datos sintéticos coherentes con la realidad."
        ),
    )
    args = parser.parse_args()
    main(modo=args.modo)
