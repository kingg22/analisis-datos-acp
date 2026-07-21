"""
visualizaciones.py
==================

Persona 3 - Visualizaciones ANUALES para el dashboard (Persona 5)
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Genera figuras (PNG) a partir del dataset unificado anual:

  1. Serie anual de tránsitos totales (resalta sequía FY2024 y recuperación FY2025).
  2. Composición por segmento (% apilada por año fiscal).
  3. Ranking de segmentos (barras horizontales).
  4. Comparativa sequía vs baseline vs recuperación (barras agrupadas).
  5. Heatmap de correlación entre variables numéricas.
  6. Tendencia anual con recta de ajuste (CAGR).
  7. Relación entre precio de combustible y tránsitos (anual).
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend no interactivo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RUTA_BASE = Path(__file__).resolve().parents[1]
RUTA_PROCESSED = RUTA_BASE / "data" / "processed"
RUTA_FIG = RUTA_BASE / "figures"

RUTA_UNIFICADO = RUTA_PROCESSED / "canal_unificado.csv"

sns.set_theme(style="whitegrid", context="talk")
COLOR_SEQUIA = "#d62728"
COLOR_RECUPERACION = "#2ca02c"
COLOR_BASELINE = "#1f77b4"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("visualizaciones")


def cargar() -> pd.DataFrame:
    if not RUTA_UNIFICADO.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_UNIFICADO}. Ejecuta primero src/preprocesamiento.py"
        )
    df = pd.read_csv(RUTA_UNIFICADO)
    log.info("Dataset unificado cargado: %d filas", df.shape[0])
    return df


def _guardar(fig: plt.Figure, nombre: str) -> Path:
    ruta = RUTA_FIG / nombre
    fig.tight_layout()
    fig.savefig(ruta, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("Figura guardada: %s", ruta)
    return ruta


# ---------------------------------------------------------------------------
# 1. Serie anual con resaltado de eventos
# ---------------------------------------------------------------------------
def fig_serie_anual(df: pd.DataFrame) -> Path:
    log.info("Generando figura: serie anual")
    serie = df.groupby("anio_fiscal")["transitos"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(serie.index, serie.values, color=COLOR_BASELINE, linewidth=2.5,
            marker="o", markersize=8, label="Tránsitos totales")
    # Resaltar el año de sequía y el de recuperación
    if 2024 in serie.index:
        ax.scatter([2024], [serie.loc[2024]], color=COLOR_SEQUIA, s=160, zorder=5,
                   label="Sequía (FY2024)")
    if 2025 in serie.index:
        ax.scatter([2025], [serie.loc[2025]], color=COLOR_RECUPERACION, s=160, zorder=5,
                   label="Recuperación (FY2025)")
    for x, y in serie.items():
        ax.annotate(f"{int(y):,}", (x, y), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=10)
    ax.set_title("Tránsitos anuales del Canal de Panamá (todos los segmentos)")
    ax.set_ylabel("Tránsitos por año fiscal")
    ax.set_xlabel("Año fiscal")
    ax.set_xticks(list(serie.index))
    ax.legend(loc="best")
    return _guardar(fig, "01_serie_anual.png")


# ---------------------------------------------------------------------------
# 2. Composición por segmento (% apilada)
# ---------------------------------------------------------------------------
def fig_composicion_segmento(df: pd.DataFrame) -> Path:
    log.info("Generando figura: composición por segmento")
    base = df.groupby(["anio_fiscal", "segmento"])["transitos"].sum().reset_index()
    totales = base.groupby("anio_fiscal")["transitos"].transform("sum")
    base["pct"] = base["transitos"] / totales * 100
    pivot = base.pivot(index="anio_fiscal", columns="segmento", values="pct").fillna(0)
    orden = pivot.mean().sort_values(ascending=False).index
    pivot = pivot[orden]

    fig, ax = plt.subplots(figsize=(14, 6))
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20", width=0.85)
    ax.set_title("Composición porcentual de tránsitos por segmento y año fiscal")
    ax.set_xlabel("Año fiscal")
    ax.set_ylabel("% de tránsitos")
    ax.legend(title="Segmento", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    return _guardar(fig, "02_composicion_por_segmento.png")


# ---------------------------------------------------------------------------
# 3. Ranking de segmentos (barras horizontales)
# ---------------------------------------------------------------------------
def fig_ranking_segmentos(df: pd.DataFrame) -> Path:
    log.info("Generando figura: ranking de segmentos")
    base = df.groupby("segmento")["transitos"].sum().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(base.index, base.values, color=COLOR_BASELINE)
    ax.set_title("Ranking de segmentos por tránsitos totales")
    ax.set_xlabel("Tránsitos (período completo)")
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height() / 2, f" {int(width):,}",
                va="center", fontsize=10)
    return _guardar(fig, "03_ranking_segmentos.png")


# ---------------------------------------------------------------------------
# 4. Comparativa sequía / baseline / recuperación
# ---------------------------------------------------------------------------
def fig_comparativa_periodos(df: pd.DataFrame) -> Path:
    log.info("Generando figura: comparativa de períodos")
    df = df.copy()
    df["periodo"] = np.select(
        [df["periodo_sequia"] == 1, df["periodo_recuperacion"] == 1],
        ["sequia", "recuperacion"],
        default="baseline",
    )
    base = df.groupby(["periodo", "segmento"])["transitos"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.barplot(data=base, x="segmento", y="transitos", hue="periodo",
                hue_order=["baseline", "sequia", "recuperacion"],
                palette={"baseline": COLOR_BASELINE, "sequia": COLOR_SEQUIA,
                         "recuperacion": COLOR_RECUPERACION}, ax=ax)
    ax.set_title("Tránsitos promedio por año fiscal: baseline vs sequía vs recuperación")
    ax.set_xlabel("Segmento")
    ax.set_ylabel("Tránsitos promedio por año")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.legend(title="Período")
    return _guardar(fig, "04_comparativa_periodos.png")


# ---------------------------------------------------------------------------
# 5. Heatmap de correlación
# ---------------------------------------------------------------------------
def fig_heatmap_correlacion(df: pd.DataFrame) -> Path:
    log.info("Generando figura: heatmap de correlación")
    cols = ["transitos", "calado_promedio_pies", "toneladas_cp_suez", "peajes_usd",
            "precio_barril_usd_prom", "ratio_toneladas_por_transito", "peaje_por_tonelada_usd"]
    disponibles = [c for c in cols if c in df.columns and df[c].notna().any()]
    num = df[disponibles].copy()
    corr = num.corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True,
                ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlación entre variables numéricas (Pearson)")
    return _guardar(fig, "05_heatmap_correlacion.png")


# ---------------------------------------------------------------------------
# 6. Tendencia anual con recta de ajuste
# ---------------------------------------------------------------------------
def fig_tendencia_anual(df: pd.DataFrame) -> Path:
    log.info("Generando figura: tendencia anual")
    anual = df.groupby("anio_fiscal")["transitos"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(anual["anio_fiscal"], anual["transitos"], marker="o",
            color=COLOR_BASELINE, linewidth=2, markersize=8)
    z = np.polyfit(anual["anio_fiscal"], anual["transitos"], 1)
    p = np.poly1d(z)
    ax.plot(anual["anio_fiscal"], p(anual["anio_fiscal"]), "--", color="#ff7f0e",
            label=f"Tendencia lineal (pendiente={z[0]:.0f} tr/año)")
    ax.set_title("Tránsitos por año fiscal (todos los segmentos)")
    ax.set_xlabel("Año fiscal")
    ax.set_ylabel("Tránsitos")
    ax.set_xticks(list(anual["anio_fiscal"]))
    ax.legend()
    return _guardar(fig, "06_tendencia_anual.png")


# ---------------------------------------------------------------------------
# 7. Relación precio combustible vs tránsitos (anual)
# ---------------------------------------------------------------------------
def fig_precio_vs_transitos(df: pd.DataFrame) -> Path:
    log.info("Generando figura: precio vs tránsitos")
    serie = (
        df.groupby("anio_fiscal")
        .agg(transitos=("transitos", "sum"),
             precio_barril_usd_prom=("precio_barril_usd_prom", "mean"))
        .reset_index()
    )

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(serie["anio_fiscal"], serie["transitos"], color=COLOR_BASELINE,
             linewidth=2, marker="o", label="Tránsitos")
    ax1.set_xlabel("Año fiscal")
    ax1.set_ylabel("Tránsitos anuales", color=COLOR_BASELINE)
    ax1.tick_params(axis="y", labelcolor=COLOR_BASELINE)
    ax1.set_xticks(list(serie["anio_fiscal"]))

    ax2 = ax1.twinx()
    ax2.plot(serie["anio_fiscal"], serie["precio_barril_usd_prom"], color="#ff7f0e",
             linewidth=2, marker="s", alpha=0.85, label="Precio crudo (USD/barril)")
    ax2.set_ylabel("USD por barril", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")
    ax1.set_title("Tránsitos vs precio de combustible (promedio por año fiscal)")
    return _guardar(fig, "07_precio_vs_transitos.png")


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def ejecutar() -> list[Path]:
    log.info("=== INICIO VISUALIZACIONES PERSONA 3 ===")
    RUTA_FIG.mkdir(parents=True, exist_ok=True)

    df = cargar()
    figuras = [
        fig_serie_anual(df),
        fig_composicion_segmento(df),
        fig_ranking_segmentos(df),
        fig_comparativa_periodos(df),
        fig_heatmap_correlacion(df),
        fig_tendencia_anual(df),
        fig_precio_vs_transitos(df),
    ]
    log.info("=== %d FIGURAS GENERADAS ===", len(figuras))
    return figuras


if __name__ == "__main__":
    ejecutar()
