"""
run_pipeline.py
===============

Persona 3 - Orquestador del módulo de análisis.
Ejecuta preprocesamiento -> análisis -> visualizaciones en secuencia.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Permitir imports relativos
sys.path.insert(0, str(Path(__file__).resolve().parent))

import preprocesamiento  # noqa: E402
import analisis_tendencias  # noqa: E402
import visualizaciones  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("persona3_pipeline")


def main() -> None:
    t0 = time.time()
    log.info("################################################")
    log.info("#  PERSONA 3 - PIPELINE DE ANÁLISIS             #")
    log.info("################################################")

    log.info(">>> [1/3] Preprocesamiento")
    preprocesamiento.ejecutar()

    log.info(">>> [2/3] Análisis de tendencias")
    analisis_tendencias.ejecutar()

    log.info(">>> [3/3] Visualizaciones")
    figs = visualizaciones.ejecutar()

    log.info("################################################")
    log.info(f"#  PIPELINE COMPLETADO en {time.time() - t0:.1f}s       #")
    log.info(f"#  {len(figs)} figuras generadas en persona3_analisis/figures/   #")
    log.info("################################################")


if __name__ == "__main__":
    main()
