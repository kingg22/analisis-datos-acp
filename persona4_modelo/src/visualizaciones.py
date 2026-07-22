"""
visualizaciones.py
==================

Persona 4 - Figuras del modelo predictivo para el dashboard (Persona 5).

Genera PNG en `figures/`:
  1. comparativa_modelos.png    — MAE (LOYO) por modelo, baseline destacado
  2. ajuste_loo.png             — total anual real vs predicho (Leave-One-Year-Out)
  3. importancia_features.png   — importancia de features del modelo ganador
  4. pronostico_anual.png       — histórico anual + pronóstico FY2026
  5. ajuste_por_segmento.png    — real vs predicho por segmento (dispersión)
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import preparacion_datos as prep

log = logging.getLogger("persona4.visualizaciones")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
FIGURES = BASE / "figures"

plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": 0.3, "font.size": 10})

AZUL = "#1f4e79"
NARANJA = "#e07b39"
VERDE = "#2e8b57"
GRIS = "#9aa5b1"


def _serie_anual_historica() -> pd.DataFrame:
    """Total anual observado, sumando los segmentos del panel."""
    df = prep.cargar_panel()
    return (
        df.groupby("anio_fiscal")[prep.TARGET].sum().reset_index()
        .rename(columns={prep.TARGET: "transitos_totales"})
    )


def _fig_comparativa_modelos() -> Path:
    df = pd.read_csv(OUTPUT / "metricas_modelos.csv").sort_values("MAE")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colores = [
        GRIS if m == "Media_Historica" else (VERDE if i == 0 else AZUL)
        for i, m in enumerate(df["modelo"])
    ]
    ax.barh(df["modelo"], df["MAE"], color=colores)
    ax.invert_yaxis()
    ax.set_xlabel("MAE (tránsitos) en Leave-One-Year-Out — menor es mejor")
    ax.set_title("Comparativa de modelos · error de validación\n(gris = baseline sin aprendizaje)")
    for y, v in enumerate(df["MAE"]):
        ax.text(v + max(df["MAE"]) * 0.01, y, f"{v:.0f}", va="center", fontsize=9)
    fig.tight_layout()
    destino = FIGURES / "01_comparativa_modelos.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _fig_ajuste_loo() -> Path:
    df = pd.read_csv(OUTPUT / "predicciones_test.csv")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["anio_fiscal"], df["transitos_reales"], marker="o", color=AZUL, label="Reales")
    ax.plot(df["anio_fiscal"], df["transitos_predichos"], marker="s", ls="--",
            color=NARANJA, label="Predichos (LOYO)")
    ax.set_ylabel("Tránsitos anuales totales")
    ax.set_xlabel("Año fiscal")
    ax.set_title("Ajuste del modelo · validación Leave-One-Year-Out")
    ax.set_xticks(list(df["anio_fiscal"]))
    ax.legend()
    fig.tight_layout()
    destino = FIGURES / "02_ajuste_loo.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _fig_importancia() -> Path | None:
    ruta = OUTPUT / "importancia_features.csv"
    if not ruta.exists():
        return None
    df = pd.read_csv(ruta)
    valor = df.columns[1]
    df = df.sort_values(valor, ascending=False).head(12).sort_values(valor)
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
    hist = _serie_anual_historica()
    pred = pd.read_csv(OUTPUT / "predicciones_2026.csv")

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(hist["anio_fiscal"], hist["transitos_totales"], color=AZUL, marker="o",
            label="Histórico (observado)")
    enlace = pd.concat([
        hist.tail(1).rename(columns={"transitos_totales": "transitos_predichos"})[
            ["anio_fiscal", "transitos_predichos"]],
        pred[["anio_fiscal", "transitos_predichos"]],
    ])
    ax.plot(enlace["anio_fiscal"], enlace["transitos_predichos"], color=NARANJA,
            marker="s", ls="--", label="Pronóstico")
    for _, r in pred.iterrows():
        ax.annotate(f"{int(r['transitos_predichos']):,}",
                    (r["anio_fiscal"], r["transitos_predichos"]),
                    textcoords="offset points", xytext=(0, 10), ha="center",
                    fontsize=9, color=NARANJA)
    ax.set_ylabel("Tránsitos anuales")
    ax.set_xlabel("Año fiscal")
    ax.set_title("Tránsitos del Canal de Panamá · histórico + pronóstico")
    ax.set_xticks(list(hist["anio_fiscal"]) + list(pred["anio_fiscal"]))
    ax.legend()
    fig.tight_layout()
    destino = FIGURES / "04_pronostico_anual.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def _fig_ajuste_por_segmento() -> Path | None:
    ruta = OUTPUT / "predicciones_test_por_segmento.csv"
    if not ruta.exists():
        return None
    df = pd.read_csv(ruta)

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    for seg, g in df.groupby("segmento"):
        ax.scatter(g["transitos_reales"], g["transitos_predichos"], label=seg, s=45, alpha=0.85)
    lim = max(df["transitos_reales"].max(), df["transitos_predichos"].max()) * 1.05
    ax.plot([0, lim], [0, lim], ls="--", color=GRIS, lw=1, label="Predicción perfecta")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Tránsitos reales")
    ax.set_ylabel("Tránsitos predichos (LOYO)")
    ax.set_title("Ajuste por segmento de mercado")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    destino = FIGURES / "05_ajuste_por_segmento.png"
    fig.savefig(destino)
    plt.close(fig)
    return destino


def ejecutar() -> list[Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    figuras = [
        _fig_comparativa_modelos(),
        _fig_ajuste_loo(),
        _fig_importancia(),
        _fig_pronostico(),
        _fig_ajuste_por_segmento(),
    ]
    figuras = [f for f in figuras if f is not None]
    log.info("%d figuras generadas en %s", len(figuras), FIGURES)
    return figuras


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    ejecutar()
