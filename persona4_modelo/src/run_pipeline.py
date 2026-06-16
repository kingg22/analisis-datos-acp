"""
run_pipeline.py
===============

Persona 4 - Orquestador del módulo de modelo predictivo.
Ejecuta entrenamiento -> predicción -> visualizaciones en secuencia.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Permitir imports relativos
sys.path.insert(0, str(Path(__file__).resolve().parent))

import entrenamiento  # noqa: E402
import prediccion  # noqa: E402
import visualizaciones  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("persona4_pipeline")


def main() -> None:
    t0 = time.time()
    log.info("################################################")
    log.info("#  PERSONA 4 - PIPELINE DE MODELO PREDICTIVO    #")
    log.info("################################################")

    log.info(">>> [1/3] Entrenamiento y evaluación")
    resumen = entrenamiento.ejecutar()

    log.info(">>> [2/3] Generación de predicciones (horizonte 12 meses)")
    prediccion.ejecutar()

    log.info(">>> [3/3] Visualizaciones")
    figs = visualizaciones.ejecutar()

    g = resumen["modelo_ganador"]
    cv = resumen["cross_validation"][g]
    ho = resumen["metricas"][g]
    log.info("################################################")
    log.info(f"#  PIPELINE COMPLETADO en {time.time() - t0:.1f}s")
    log.info(f"#  Modelo ganador: {g}")
    log.info(f"#  [CV temporal] MAPE={cv['MAPE_cv']:.2f}% (±{cv['MAPE_cv_std']:.2f})  MAE={cv['MAE_cv']:.1f}")
    log.info(f"#  [Hold-out 2025] MAPE={ho['MAPE']:.2f}%  R2={ho['R2']:.3f} (stress test)")
    log.info(f"#  {len(figs)} figuras en persona4_modelo/figures/")
    log.info("################################################")


if __name__ == "__main__":
    main()
