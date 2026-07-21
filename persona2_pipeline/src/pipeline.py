"""
pipeline.py
===========
Orquestador del pipeline de datos del Canal de Panamá.

Responsable: PERSONA 2 - Ingesta de Datos (Fuente 2) + Pipeline
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Granularidad: ANUAL (año fiscal de la ACP). Ambas fuentes se unen por `anio_fiscal`.

Secuencia de ejecución:
  Paso 1 — Verifica/ejecuta la ingesta de Persona 1 (Fuente 1: tránsitos ACP).
  Paso 2 — Ejecuta la ingesta de Fuente 2 (precios petróleo FMI, promedio anual).
  Paso 3 — Une canal_serie_anual.csv + Fuente 2 por anio_fiscal → dataset_unificado.csv
  Paso 4 — Une canal_limpio.csv (por segmento) + Fuente 2 → dataset_unificado_completo.csv
  Paso 5 — Exporta ambos CSVs a persona2_pipeline/data/processed/

Salidas para el resto del equipo:
  dataset_unificado.csv          → Persona 4 (serie anual con feature de precio)
  dataset_unificado_completo.csv → Persona 3 (segmento × año fiscal × precio)
  persona3_analisis/data/raw/fuente2_combustibles.csv → Persona 3 (via ingesta_fuente2)
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
RUTA_CANAL_SERIE = RUTA_PERSONA1 / "data" / "processed" / "canal_serie_anual.csv"
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
def asegurar_fuente1(modo_ingesta: str = "oficial") -> None:
    """Verifica que existan los archivos de Persona 1; si no, ejecuta su ingesta."""
    if RUTA_CANAL_SERIE.exists() and RUTA_CANAL_LIMPIO.exists():
        log.info("Fuente 1 encontrada en disco. Saltando ingesta de Persona 1.")
        return

    script = RUTA_PERSONA1 / "src" / "ingesta_canal.py"
    if not script.exists():
        raise FileNotFoundError(f"Script de Persona 1 no encontrado: {script}")

    log.info("Fuente 1 no encontrada. Ejecutando persona1_ingesta (modo=%s)...", modo_ingesta)
    resultado = subprocess.run(
        [sys.executable, str(script), "--modo", modo_ingesta],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Ingesta de Persona 1 falló (código {resultado.returncode}):\n{resultado.stderr}"
        )
    log.info("Ingesta de Persona 1 completada.")


# -------------------------------------------------------------------------
# Paso 2 — Ingesta Fuente 2
# -------------------------------------------------------------------------
def ejecutar_ingesta_fuente2(modo: str = "api") -> pd.DataFrame:
    """Delega en ingesta_fuente2.main() y retorna el DataFrame anual."""
    log.info("--- Paso 2: Ingesta Fuente 2 (modo=%s) ---", modo)
    return ingestar_fuente2(modo=modo)


# -------------------------------------------------------------------------
# Paso 3 — Join serie anual (para Persona 4)
# -------------------------------------------------------------------------
def unir_serie_anual(df_fuente2: pd.DataFrame) -> pd.DataFrame:
    """
    Une canal_serie_anual.csv con el precio del barril (promedio anual) por
    anio_fiscal. Resultado: una fila por año fiscal con tránsitos totales +
    precio. Alimenta el modelo de Persona 4.
    """
    log.info("--- Paso 3: Join serie anual (canal × precio) ---")
    df_canal = pd.read_csv(RUTA_CANAL_SERIE)
    df_f2 = df_fuente2[["anio_fiscal", "precio_barril_usd_prom", "var_anual_pct"]].copy()

    df_unido = pd.merge(df_canal, df_f2, on="anio_fiscal", how="left")
    nulos = int(df_unido["precio_barril_usd_prom"].isna().sum())
    if nulos:
        log.warning("%d año(s) sin precio tras el join. Se interpolan/rellenan.", nulos)
        for col in ["precio_barril_usd_prom", "var_anual_pct"]:
            df_unido[col] = df_unido[col].interpolate().ffill().bfill()

    df_unido = df_unido.sort_values("anio_fiscal").reset_index(drop=True)
    log.info("Serie anual unificada: %d filas, %d columnas.", len(df_unido), df_unido.shape[1])
    return df_unido


# -------------------------------------------------------------------------
# Paso 4 — Join nivel segmento (para Persona 3)
# -------------------------------------------------------------------------
def unir_por_segmento(df_fuente2: pd.DataFrame) -> pd.DataFrame:
    """
    Une canal_limpio.csv (una fila por año fiscal × segmento) con el precio del
    barril por anio_fiscal. Tabla que Persona 3 usa para el análisis por segmento.
    """
    log.info("--- Paso 4: Join por segmento (canal_limpio × precio) ---")
    df_canal = pd.read_csv(RUTA_CANAL_LIMPIO)
    df_f2 = df_fuente2[["anio_fiscal", "precio_barril_usd_prom"]].copy()

    df_unido = pd.merge(df_canal, df_f2, on="anio_fiscal", how="left")
    df_unido["precio_barril_usd_prom"] = (
        df_unido["precio_barril_usd_prom"].interpolate().ffill().bfill()
    )
    log.info("Dataset por segmento unificado: %d filas, %d columnas.", len(df_unido), df_unido.shape[1])
    return df_unido


# -------------------------------------------------------------------------
# Paso 5 — Persistencia de salidas
# -------------------------------------------------------------------------
def guardar_resultados(df_serie: pd.DataFrame, df_completo: pd.DataFrame) -> None:
    RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_serie.to_csv(RUTA_UNIFICADO, index=False, encoding="utf-8")
    log.info("Dataset unificado (serie anual) → %s  (%d filas)", RUTA_UNIFICADO, len(df_serie))
    df_completo.to_csv(RUTA_UNIFICADO_COMPLETO, index=False, encoding="utf-8")
    log.info("Dataset unificado (por segmento)  → %s  (%d filas)", RUTA_UNIFICADO_COMPLETO, len(df_completo))


# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
def main(modo_fuente1: str = "oficial", modo_fuente2: str = "api") -> None:
    log.info("=" * 65)
    log.info("PIPELINE  —  Grupo 8: Análisis de Datos del Canal de Panamá (anual)")
    log.info("=" * 65)

    asegurar_fuente1(modo_ingesta=modo_fuente1)          # Paso 1
    df_fuente2 = ejecutar_ingesta_fuente2(modo_fuente2)  # Paso 2
    df_serie = unir_serie_anual(df_fuente2)              # Paso 3
    df_completo = unir_por_segmento(df_fuente2)          # Paso 4
    guardar_resultados(df_serie, df_completo)            # Paso 5

    log.info("=" * 65)
    log.info("PIPELINE COMPLETADO. Archivos disponibles para el equipo:")
    log.info("  Persona 3 → %s", RUTA_UNIFICADO_COMPLETO)
    log.info("  Persona 4 → %s", RUTA_UNIFICADO)
    log.info("  Persona 3 → persona3_analisis/data/raw/fuente2_combustibles.csv")
    log.info("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de datos del Canal de Panamá — Grupo 8")
    parser.add_argument(
        "--modo-fuente1", choices=["oficial", "local"], default="oficial",
        help="Modo de ingesta para Fuente 1 (tránsitos ACP). Default: oficial.",
    )
    parser.add_argument(
        "--modo-fuente2", choices=["api", "muestra"], default="api",
        help="Modo de ingesta para Fuente 2 (precios FMI). Default: api.",
    )
    args = parser.parse_args()
    main(modo_fuente1=args.modo_fuente1, modo_fuente2=args.modo_fuente2)
