"""
pipeline.py
===========
Orquestador del pipeline de datos del Canal de Panamá.

Responsable: PERSONA 2 - Ingesta de Datos (Fuente 2) + Pipeline
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Secuencia de ejecución:
  Paso 1 — Verifica/ejecuta la ingesta de Persona 1 (Fuente 1: tránsitos ACP).
  Paso 2 — Ejecuta la ingesta de Fuente 2 (precios petróleo, FMI PCPS).
  Paso 3 — Une canal_serie_mensual.csv + Fuente 2 por fecha → dataset_unificado.csv
  Paso 4 — Une canal_limpio.csv (por segmento) + Fuente 2 → dataset_unificado_completo.csv
  Paso 5 — Exporta ambos CSVs a persona2_pipeline/data/processed/

Salidas para el resto del equipo:
  dataset_unificado.csv         → Persona 4 (serie mensual con feature de precio)
  dataset_unificado_completo.csv → Persona 3 (segmento × mes × precio)
  persona3_analisis/data/raw/fuente2_combustibles.csv → Persona 3 (via ingesta_fuente2)

Diseño:
  Pipeline orquestado con scripts secuenciales en Python puro.
  No se usa Airflow ni Prefect: la complejidad no está justificada para
  el alcance de este proyecto académico. Si el equipo crece, los pasos
  están claramente delimitados y son fácilmente portables a un DAG de Prefect.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Agregar src/ al path para importar ingesta_fuente2
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ingesta_fuente2 import main as ingestar_fuente2  # noqa: E402

# -------------------------------------------------------------------------
# Rutas
# -------------------------------------------------------------------------
RUTA_BASE = Path(__file__).resolve().parents[1]
RUTA_PROCESSED = RUTA_BASE / "data" / "processed"

RUTA_PERSONA1 = Path(__file__).resolve().parents[2] / "persona1_ingesta"
RUTA_CANAL_SERIE = RUTA_PERSONA1 / "data" / "processed" / "canal_serie_mensual.csv"
RUTA_CANAL_LIMPIO = RUTA_PERSONA1 / "data" / "processed" / "canal_limpio.csv"

RUTA_UNIFICADO = RUTA_PROCESSED / "dataset_unificado.csv"
RUTA_UNIFICADO_COMPLETO = RUTA_PROCESSED / "dataset_unificado_completo.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("pipeline")


# -------------------------------------------------------------------------
# Paso 1 — Asegurar datos de Persona 1
# -------------------------------------------------------------------------
def asegurar_fuente1(modo_ingesta: str = "muestra") -> None:
    """
    Verifica que los archivos de Persona 1 existan en disco.
    Si no existen, ejecuta ingesta_canal.py en el modo indicado.
    """
    if RUTA_CANAL_SERIE.exists() and RUTA_CANAL_LIMPIO.exists():
        log.info("Fuente 1 encontrada en disco. Saltando ingesta de Persona 1.")
        return

    script = RUTA_PERSONA1 / "src" / "ingesta_canal.py"
    if not script.exists():
        raise FileNotFoundError(
            f"Script de Persona 1 no encontrado: {script}\n"
            "Asegúrate de que la carpeta persona1_ingesta esté en el repositorio."
        )

    log.info(
        "Fuente 1 no encontrada. Ejecutando persona1_ingesta (modo=%s)...",
        modo_ingesta,
    )
    resultado = subprocess.run(
        [sys.executable, str(script), "--modo", modo_ingesta],
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Ingesta de Persona 1 falló (código {resultado.returncode}):\n"
            f"{resultado.stderr}"
        )
    log.info("Ingesta de Persona 1 completada.")


# -------------------------------------------------------------------------
# Paso 2 — Ingesta Fuente 2
# -------------------------------------------------------------------------
def ejecutar_ingesta_fuente2(modo: str = "api") -> pd.DataFrame:
    """Delega en ingesta_fuente2.main() y retorna el DataFrame limpio."""
    log.info("--- Paso 2: Ingesta Fuente 2 (modo=%s) ---", modo)
    return ingestar_fuente2(modo=modo)


# -------------------------------------------------------------------------
# Paso 3 — Join serie mensual (para Persona 4)
# -------------------------------------------------------------------------
def unir_serie_mensual(df_fuente2: pd.DataFrame) -> pd.DataFrame:
    """
    Une canal_serie_mensual.csv con los precios de Fuente 2 por fecha.
    Resultado: una fila por mes con tránsitos totales + precio del barril.
    Esta es la tabla que alimenta directamente el modelo predictivo de Persona 4.
    """
    log.info("--- Paso 3: Join serie mensual (canal × precio) ---")

    df_canal = pd.read_csv(RUTA_CANAL_SERIE, parse_dates=["fecha"])
    df_canal = df_canal.sort_values("fecha").reset_index(drop=True)

    cols_f2 = ["fecha", "precio_barril_usd", "var_mensual_pct", "precio_barril_usd_ma3"]
    df_f2 = df_fuente2[cols_f2].copy()

    df_unido = pd.merge(df_canal, df_f2, on="fecha", how="left")

    nulos = int(df_unido["precio_barril_usd"].isna().sum())
    if nulos > 0:
        log.warning(
            "%d fila(s) sin precio de petróleo tras el join "
            "(fechas fuera del rango de Fuente 2). Se interpolan linealmente.",
            nulos,
        )
        for col in ["precio_barril_usd", "var_mensual_pct", "precio_barril_usd_ma3"]:
            df_unido[col] = df_unido[col].interpolate(method="linear")

    df_unido["anio"] = df_unido["fecha"].dt.year
    df_unido["mes"] = df_unido["fecha"].dt.month

    log.info(
        "Serie mensual unificada: %d filas, %d columnas.",
        len(df_unido),
        df_unido.shape[1],
    )
    return df_unido


# -------------------------------------------------------------------------
# Paso 4 — Join nivel segmento (para Persona 3)
# -------------------------------------------------------------------------
def unir_por_segmento(df_fuente2: pd.DataFrame) -> pd.DataFrame:
    """
    Une canal_limpio.csv (una fila por mes × segmento) con los precios de Fuente 2.
    Resultado: tabla completa que Persona 3 usa para el análisis por tipo de buque.
    """
    log.info("--- Paso 4: Join por segmento (canal_limpio × precio) ---")

    df_canal = pd.read_csv(RUTA_CANAL_LIMPIO, parse_dates=["fecha"])
    df_f2 = df_fuente2[["fecha", "precio_barril_usd", "precio_barril_usd_ma3"]].copy()

    df_unido = pd.merge(df_canal, df_f2, on="fecha", how="left")

    for col in ["precio_barril_usd", "precio_barril_usd_ma3"]:
        df_unido[col] = df_unido[col].interpolate(method="linear")

    log.info(
        "Dataset por segmento unificado: %d filas, %d columnas.",
        len(df_unido),
        df_unido.shape[1],
    )
    return df_unido


# -------------------------------------------------------------------------
# Paso 5 — Persistencia de salidas
# -------------------------------------------------------------------------
def guardar_resultados(df_serie: pd.DataFrame, df_completo: pd.DataFrame) -> None:
    """Exporta los datasets finales a persona2_pipeline/data/processed/."""
    RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)

    df_serie.to_csv(RUTA_UNIFICADO, index=False, encoding="utf-8")
    log.info(
        "Dataset unificado (serie mensual) → %s  (%d filas)",
        RUTA_UNIFICADO,
        len(df_serie),
    )

    df_completo.to_csv(RUTA_UNIFICADO_COMPLETO, index=False, encoding="utf-8")
    log.info(
        "Dataset unificado (por segmento)  → %s  (%d filas)",
        RUTA_UNIFICADO_COMPLETO,
        len(df_completo),
    )


# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
def main(modo_fuente1: str = "muestra", modo_fuente2: str = "api") -> None:
    log.info("=" * 65)
    log.info("PIPELINE  —  Grupo 8: Análisis de Datos del Canal de Panamá")
    log.info("=" * 65)

    asegurar_fuente1(modo_ingesta=modo_fuente1)          # Paso 1
    df_fuente2 = ejecutar_ingesta_fuente2(modo_fuente2)  # Paso 2
    df_serie = unir_serie_mensual(df_fuente2)            # Paso 3
    df_completo = unir_por_segmento(df_fuente2)          # Paso 4
    guardar_resultados(df_serie, df_completo)            # Paso 5

    log.info("=" * 65)
    log.info("PIPELINE COMPLETADO. Archivos disponibles para el equipo:")
    log.info("  Persona 3 → %s", RUTA_UNIFICADO_COMPLETO)
    log.info("  Persona 4 → %s", RUTA_UNIFICADO)
    log.info("  Persona 3 → persona3_analisis/data/raw/fuente2_combustibles.csv")
    log.info("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline de datos del Canal de Panamá — Grupo 8"
    )
    parser.add_argument(
        "--modo-fuente1",
        choices=["muestra", "url", "local"],
        default="muestra",
        help="Modo de ingesta para Fuente 1 (tránsitos ACP). Default: muestra.",
    )
    parser.add_argument(
        "--modo-fuente2",
        choices=["api", "muestra"],
        default="api",
        help="Modo de ingesta para Fuente 2 (precios FMI). Default: api.",
    )
    args = parser.parse_args()
    main(modo_fuente1=args.modo_fuente1, modo_fuente2=args.modo_fuente2)
