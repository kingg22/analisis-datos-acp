"""
visualizaciones.py
==================

Persona 3 - Generación de visualizaciones para el dashboard
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Genera figuras (PNG) listas para integrar en el dashboard de Persona 5:

  1. Serie mensual de tránsitos totales (con áreas sombreadas para sequía y
     recuperación).
  2. Descomposición estacional (observado, tendencia, estacionalidad, residuo).
  3. Subserie estacional por mes calendario.
  4. Composición por segmento (% apilada por año).
  5. Ranking de segmentos (barras horizontales).
  6. Comparativa sequía vs baseline vs recuperación (barras agrupadas).
  7. Heatmap de correlación entre variables numéricas.
  8. Estacionalidad por fase fiscal ACP (oct→sep).
  9. Tendencia anual con bandas (CAGR).
 10. Relación entre precio de combustible y tránsitos.
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
RUTA_OUTPUT = RUTA_BASE / "output"
RUTA_FIG = RUTA_BASE / "figures"

RUTA_UNIFICADO = RUTA_PROCESSED / "canal_unificado.csv"

# Estilo
sns.set_theme(style="whitegrid", context="talk")
PALETTE = sns.color_palette("tab10", n_colors=12)
COLOR_SEQUIA = "#d62728"     # rojo
COLOR_RECUPERACION = "#2ca02c"  # verde
COLOR_BASELINE = "#1f77b4"   # azul

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
    df = pd.read_csv(RUTA_UNIFICADO, parse_dates=["fecha"])
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
# 1. Serie mensual con sombreados
# ---------------------------------------------------------------------------
def fig_serie_mensual(df: pd.DataFrame) -> Path:
    log.info("Generando figura: serie mensual")
    serie = df.groupby("fecha")["transitos"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(serie.index, serie.values, color=COLOR_BASELINE, linewidth=2, label="Tránsitos totales")
    ax.fill_between(serie.index, serie.values, alpha=0.15, color=COLOR_BASELINE)

    # Sombrear sequía
    seq = df[df["periodo_sequia"] == 1]
    if not seq.empty:
        ax.axvspan(seq["fecha"].min(), seq["fecha"].max(),
                   color=COLOR_SEQUIA, alpha=0.12, label="Sequía 2023–may-2024")

    # Sombrear recuperación
    rec = df[df["periodo_recuperacion"] == 1]
    if not rec.empty:
        ax.axvspan(rec["fecha"].min(), rec["fecha"].max(),
                   color=COLOR_RECUPERACION, alpha=0.10, label="Recuperación 2025+")

    ax.set_title("Tránsitos mensuales del Canal de Panamá (todos los segmentos)")
    ax.set_ylabel("Tránsitos por mes")
    ax.set_xlabel("Fecha")
    ax.legend(loc="best")
    return _guardar(fig, "01_serie_mensual.png")


# ---------------------------------------------------------------------------
# 2. Descomposición estacional
# ---------------------------------------------------------------------------
def fig_descomposicion(df: pd.DataFrame) -> Path:
    log.info("Generando figura: descomposición estacional")
    serie = df.groupby("fecha")["transitos"].sum().sort_index().asfreq("MS")
    periodo = 12
    tendencia = serie.rolling(window=periodo, center=True, min_periods=1).mean()
    detrend = serie - tendencia
    estacional_idx = detrend.index.month
    estacionalidad = detrend.groupby(estacional_idx).mean()
    residuo = serie - tendencia - estacionalidad.reindex(estacional_idx).values

    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    axes[0].plot(serie.index, serie.values, color=COLOR_BASELINE)
    axes[0].set_title("Observado")
    axes[0].set_ylabel("Tránsitos")
    axes[1].plot(tendencia.index, tendencia.values, color="#ff7f0e")
    axes[1].set_title("Tendencia (media móvil 12 meses)")
    axes[1].set_ylabel("Tránsitos")
    axes[2].plot(serie.index, estacionalidad.reindex(estacional_idx).values, color="#2ca02c")
    axes[2].set_title("Estacionalidad")
    axes[2].set_ylabel("Δ tránsitos")
    axes[3].scatter(residuo.index, residuo.values, color="#d62728", s=10)
    axes[3].axhline(0, color="black", linewidth=0.5)
    axes[3].set_title("Residuo")
    axes[3].set_ylabel("Δ tránsitos")
    axes[3].set_xlabel("Fecha")
    return _guardar(fig, "02_descomposicion_estacional.png")


# ---------------------------------------------------------------------------
# 3. Subserie estacional por mes calendario
# ---------------------------------------------------------------------------
def fig_subserie_estacional(df: pd.DataFrame) -> Path:
    log.info("Generando figura: subserie estacional")
    serie = df.groupby("fecha")["transitos"].sum().sort_index().reset_index()
    serie["mes"] = serie["fecha"].dt.month
    serie["anio"] = serie["fecha"].dt.year

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=serie, x="mes", y="transitos", hue="anio",
                 palette="viridis", ax=ax, legend="full")
    ax.set_title("Subserie estacional por mes calendario (cada línea = un año)")
    ax.set_xlabel("Mes calendario")
    ax.set_ylabel("Tránsitos mensuales")
    ax.set_xticks(range(1, 13))
    return _guardar(fig, "03_subserie_estacional.png")


# ---------------------------------------------------------------------------
# 4. Composición por segmento (% apilada)
# ---------------------------------------------------------------------------
def fig_composicion_segmento(df: pd.DataFrame) -> Path:
    log.info("Generando figura: composición por segmento")
    base = (
        df.groupby(["anio", "segmento"])["transitos"].sum().reset_index()
    )
    totales = base.groupby("anio")["transitos"].transform("sum")
    base["pct"] = base["transitos"] / totales * 100
    pivot = base.pivot(index="anio", columns="segmento", values="pct").fillna(0)
    # Ordenar columnas por promedio descendente
    orden = pivot.mean().sort_values(ascending=False).index
    pivot = pivot[orden]

    fig, ax = plt.subplots(figsize=(14, 6))
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20", width=0.85)
    ax.set_title("Composición porcentual de tránsitos por segmento y año")
    ax.set_xlabel("Año")
    ax.set_ylabel("% de tránsitos")
    ax.legend(title="Segmento", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    return _guardar(fig, "04_composicion_por_segmento.png")


# ---------------------------------------------------------------------------
# 5. Ranking de segmentos (barras horizontales)
# ---------------------------------------------------------------------------
def fig_ranking_segmentos(df: pd.DataFrame) -> Path:
    log.info("Generando figura: ranking de segmentos")
    base = (
        df.groupby("segmento")["transitos"].sum().sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(base.index, base.values, color=COLOR_BASELINE)
    ax.set_title("Ranking de segmentos por tránsitos totales")
    ax.set_xlabel("Tránsitos (período completo)")
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height() / 2,
                f" {int(width):,}", va="center", fontsize=10)
    return _guardar(fig, "05_ranking_segmentos.png")


# ---------------------------------------------------------------------------
# 6. Comparativa sequía / baseline / recuperación
# ---------------------------------------------------------------------------
def fig_comparativa_periodos(df: pd.DataFrame) -> Path:
    log.info("Generando figura: comparativa de períodos")
    df = df.copy()
    df["periodo"] = np.select(
        [
            df["periodo_sequia"] == 1,
            df["periodo_recuperacion"] == 1,
        ],
        ["sequia", "recuperacion"],
        default="baseline",
    )
    base = (
        df.groupby(["periodo", "segmento"])["transitos"].mean().reset_index()
    )

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.barplot(data=base, x="segmento", y="transitos", hue="periodo",
                hue_order=["baseline", "sequia", "recuperacion"],
                palette={"baseline": COLOR_BASELINE,
                         "sequia": COLOR_SEQUIA,
                         "recuperacion": COLOR_RECUPERACION},
                ax=ax)
    ax.set_title("Promedio mensual de tránsitos: baseline vs sequía vs recuperación")
    ax.set_xlabel("Segmento")
    ax.set_ylabel("Tránsitos promedio por mes")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.legend(title="Período")
    return _guardar(fig, "06_comparativa_periodos.png")


# ---------------------------------------------------------------------------
# 7. Heatmap de correlación
# ---------------------------------------------------------------------------
def fig_heatmap_correlacion(df: pd.DataFrame) -> Path:
    log.info("Generando figura: heatmap de correlación")
    num = df[
        ["transitos", "calado_promedio_pies", "toneladas_cp_suez", "peajes_usd",
         "precio_barril_usd", "precio_var_mensual_pct",
         "ratio_toneladas_por_transito", "peaje_por_tonelada_usd"]
    ].copy()
    corr = num.corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, square=True, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlación entre variables numéricas (Pearson)")
    return _guardar(fig, "07_heatmap_correlacion.png")


# ---------------------------------------------------------------------------
# 8. Estacionalidad por fase fiscal ACP
# ---------------------------------------------------------------------------
def fig_estacionalidad_fiscal(df: pd.DataFrame) -> Path:
    log.info("Generando figura: estacionalidad por fase fiscal")
    base = (
        df.groupby(["fase_fiscal", "segmento"])["transitos"]
        .mean().reset_index()
    )
    pivot = base.pivot(index="fase_fiscal", columns="segmento", values="transitos").fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(pivot, cmap="YlGnBu", annot=False, ax=ax, cbar_kws={"label": "Tránsitos prom."})
    ax.set_title("Estacionalidad por fase fiscal ACP (1=octubre … 12=septiembre)")
    ax.set_xlabel("Segmento")
    ax.set_ylabel("Fase fiscal")
    return _guardar(fig, "08_estacionalidad_fase_fiscal.png")


# ---------------------------------------------------------------------------
# 9. Tendencia anual con CAGR
# ---------------------------------------------------------------------------
def fig_tendencia_anual(df: pd.DataFrame) -> Path:
    log.info("Generando figura: tendencia anual")
    anual = df.groupby("anio")["transitos"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(anual["anio"], anual["transitos"], marker="o",
            color=COLOR_BASELINE, linewidth=2, markersize=8)
    z = np.polyfit(anual["anio"], anual["transitos"], 1)
    p = np.poly1d(z)
    ax.plot(anual["anio"], p(anual["anio"]), "--", color="#ff7f0e",
            label=f"Tendencia lineal (pendiente={z[0]:.0f} tr/año)")
    ax.set_title("Tránsitos anuales totales (todos los segmentos)")
    ax.set_xlabel("Año")
    ax.set_ylabel("Tránsitos")
    ax.legend()
    return _guardar(fig, "09_tendencia_anual.png")


# ---------------------------------------------------------------------------
# 10. Relación precio combustible vs tránsitos
# ---------------------------------------------------------------------------
def fig_precio_vs_transitos(df: pd.DataFrame) -> Path:
    log.info("Generando figura: precio vs tránsitos")
    serie = (
        df.groupby("fecha")
        .agg(transitos=("transitos", "sum"), precio_barril_usd=("precio_barril_usd", "mean"))
        .reset_index()
    )

    fig, ax1 = plt.subplots(figsize=(13, 5))
    ax1.plot(serie["fecha"], serie["transitos"], color=COLOR_BASELINE,
             linewidth=2, label="Tránsitos")
    ax1.set_xlabel("Fecha")
    ax1.set_ylabel("Tránsitos mensuales", color=COLOR_BASELINE)
    ax1.tick_params(axis="y", labelcolor=COLOR_BASELINE)

    ax2 = ax1.twinx()
    ax2.plot(serie["fecha"], serie["precio_barril_usd"],
             color="#ff7f0e", linewidth=2, alpha=0.8, label="Precio Brent (USD/barril)")
    ax2.set_ylabel("USD por barril", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")

    ax1.set_title("Tránsitos vs precio de combustible (segunda fuente)")
    return _guardar(fig, "10_precio_vs_transitos.png")


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def ejecutar() -> list[Path]:
    log.info("=== INICIO VISUALIZACIONES PERSONA 3 ===")
    RUTA_FIG.mkdir(parents=True, exist_ok=True)

    df = cargar()
    figuras = [
        fig_serie_mensual(df),
        fig_descomposicion(df),
        fig_subserie_estacional(df),
        fig_composicion_segmento(df),
        fig_ranking_segmentos(df),
        fig_comparativa_periodos(df),
        fig_heatmap_correlacion(df),
        fig_estacionalidad_fiscal(df),
        fig_tendencia_anual(df),
        fig_precio_vs_transitos(df),
    ]
    log.info("=== %d FIGURAS GENERADAS ===", len(figuras))
    return figuras


if __name__ == "__main__":
    ejecutar()
