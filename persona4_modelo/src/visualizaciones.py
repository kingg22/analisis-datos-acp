"""
visualizaciones.py
==================

Persona 4 - Figuras del modelo predictivo para el dashboard (Persona 5).

Genera 4 PNG en `figures/`:
  1. comparativa_modelos.png    — MAPE por modelo (barras)
  2. ajuste_test.png            — reales vs predichos en el hold-out
  3. importancia_features.png   — peso de cada feature en el modelo ganador
  4. pronostico_2026.png        — serie histórica + pronóstico 12 meses
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin display, para entornos headless
import matplotlib.pyplot as plt
import pandas as pd

import preparacion_datos as prep

log = logging.getLogger("persona4.visualizaciones")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
FIGURES = BASE / "figures"

plt.rcParams.update({
    "figure.dpi": 110,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 10,
})

AZUL = "#1f4e79"
NARANJA = "#e07b39"
VERDE = "#2e8b57"


def _fig_comparativa_modelos() -> Path:
    df = pd.read_csv(OUTPUT / "metricas_modelos.csv").sort_values("MAPE")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colores = [VERDE if i == 0 else AZUL for i in range(len(df))]
    ax.barh(df["modelo"], df["MAPE"], color=colores)
    ax.invert_yaxis()
    ax.set_xlabel("MAPE (%) — menor es mejor")
    ax.set_title("Comparativa de modelos · error en el hold-out de prueba")
    for y, v in enumerate(df["MAPE"]):
        ax.text(v + 0.1, y, f"{v:.2f}%", va="center", fontsize=9)
    fig.tight_layout()
    destino = FIGURES / "01_comparativa_modelos.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _fig_ajuste_test() -> Path:
    df = pd.read_csv(OUTPUT / "predicciones_test.csv", parse_dates=["fecha"])
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["fecha"], df["transitos_reales"], marker="o", color=AZUL, label="Reales")
    ax.plot(df["fecha"], df["transitos_predichos"], marker="s", ls="--",
            color=NARANJA, label="Predichos")
    ax.set_ylabel("Tránsitos mensuales")
    ax.set_title("Ajuste del modelo en el conjunto de prueba (2024-10 → 2025-12)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    destino = FIGURES / "02_ajuste_test.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _fig_importancia() -> Path | None:
    ruta = OUTPUT / "importancia_features.csv"
    if not ruta.exists():
        return None
    df = pd.read_csv(ruta)
    valor = df.columns[1]  # "importancia" o "coef_abs"
    df = df.sort_values(valor)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df["feature"], df[valor], color=AZUL)
    ax.set_xlabel(valor)
    ax.set_title("Importancia de features · modelo ganador")
    fig.tight_layout()
    destino = FIGURES / "03_importancia_features.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _fig_pronostico() -> Path:
    hist = prep.cargar_serie()[["fecha", prep.TARGET]]
    pred = pd.read_csv(OUTPUT / "predicciones_2026.csv", parse_dates=["fecha"])

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(hist["fecha"], hist[prep.TARGET], color=AZUL, label="Histórico (observado)")
    # Conectar el último punto observado con el pronóstico.
    enlace = pd.concat([
        hist.tail(1).rename(columns={prep.TARGET: "transitos_predichos"})[["fecha", "transitos_predichos"]],
        pred[["fecha", "transitos_predichos"]],
    ])
    ax.plot(enlace["fecha"], enlace["transitos_predichos"], color=NARANJA,
            marker="o", ls="--", label="Pronóstico 2026")
    ax.set_ylabel("Tránsitos mensuales")
    ax.set_title("Tránsitos del Canal de Panamá · histórico + pronóstico a 12 meses")
    ax.legend()
    fig.tight_layout()
    destino = FIGURES / "04_pronostico_2026.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def ejecutar() -> list[Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    figuras = [
        _fig_comparativa_modelos(),
        _fig_ajuste_test(),
        _fig_importancia(),
        _fig_pronostico(),
    ]
    figuras = [f for f in figuras if f is not None]
    log.info("%d figuras generadas en %s", len(figuras), FIGURES)
    return figuras


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    ejecutar()
