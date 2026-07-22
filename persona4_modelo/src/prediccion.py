"""
prediccion.py
=============

Persona 4 - Generación del pronóstico para el dashboard (Persona 5).

Carga el modelo ganador y predice los tránsitos de **cada segmento de mercado**
para el año fiscal 2026; el volumen total del Canal es la suma de los segmentos.

Supuestos del escenario base (explícitos, no ocultos)
-----------------------------------------------------
  - `precio_barril_usd_prom`: se arrastra el último valor observado (FY2025).
    Es el supuesto estándar de "caminata aleatoria" para el precio del crudo:
    sin un modelo propio del petróleo, el mejor estimador del precio futuro es
    el precio actual.
  - `sequia = 0`: se asume operación normal, sin el racionamiento de calado que
    caracterizó a FY2024. Coherente con la recuperación observada en FY2025.

Horizonte: **solo FY2026**. El modelo explica los tránsitos por segmento,
régimen operativo y precio del crudo, pero NO incorpora una tendencia temporal
(ver `preparacion_datos.py`). Por eso, bajo supuestos constantes, produciría un
valor idéntico para FY2027: extender el horizonte daría una falsa sensación de
información. Para pronosticar más lejos habría que modelar antes la evolución
del exógeno.

Salidas:
  - `output/predicciones_2026.csv`              (total anual, para el dashboard)
  - `output/predicciones_2026_por_segmento.csv` (detalle por segmento)
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import pandas as pd

import preparacion_datos as prep

log = logging.getLogger("persona4.prediccion")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
MODELS = BASE / "models"

ANIO_PRONOSTICO = 2026


def _cargar_modelo() -> dict:
    ruta = MODELS / "modelo_transitos.pkl"
    if not ruta.exists():
        raise FileNotFoundError(
            "No existe el modelo entrenado. Ejecuta primero entrenamiento.py."
        )
    with open(ruta, "rb") as fh:
        return pickle.load(fh)


def _escenario(hist: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Construye el panel de features del año a pronosticar (un fila por segmento)."""
    ultimo_anio = int(hist["anio_fiscal"].max())
    precio = float(
        hist.loc[hist["anio_fiscal"] == ultimo_anio, "precio_barril_usd_prom"].iloc[0]
    )
    log.info("Escenario FY%d: precio crudo = %.2f USD/barril (arrastrado de FY%d), sin sequía",
             anio, precio, ultimo_anio)

    return pd.DataFrame({
        "segmento": sorted(hist["segmento"].unique()),
        "anio_fiscal": anio,
        "precio_barril_usd_prom": precio,
        "sequia": 0,
    })


def pronosticar(anio: int = ANIO_PRONOSTICO) -> pd.DataFrame:
    """Genera el pronóstico de tránsitos por segmento y el total anual."""
    paquete = _cargar_modelo()
    modelo, feats = paquete["modelo"], paquete["features"]
    log.info("Modelo cargado: %s", paquete["nombre"])

    hist = prep.construir_features(prep.cargar_panel())
    futuro = _escenario(hist, anio)

    X = prep.matriz_features(futuro, columnas_ref=feats)
    futuro["transitos_predichos"] = modelo.predict(X).clip(min=0).round(0)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    detalle = futuro[["anio_fiscal", "segmento", "transitos_predichos"]]
    detalle.to_csv(OUTPUT / "predicciones_2026_por_segmento.csv", index=False)

    total = (
        detalle.groupby("anio_fiscal")["transitos_predichos"].sum().reset_index()
    )
    total.to_csv(OUTPUT / "predicciones_2026.csv", index=False)

    log.info("Pronóstico FY%d: %d tránsitos totales", anio, int(total["transitos_predichos"].iloc[0]))
    for _, r in detalle.sort_values("transitos_predichos", ascending=False).iterrows():
        log.info("   %-22s %6d", r["segmento"], int(r["transitos_predichos"]))

    return total


def ejecutar() -> pd.DataFrame:
    return pronosticar()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    pronosticar()
