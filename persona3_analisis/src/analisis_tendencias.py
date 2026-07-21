"""
analisis_tendencias.py
======================

Persona 3 - Análisis Exploratorio de Tendencias de Tránsitos (ANUAL)
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Carga el dataset unificado (anual por segmento) de preprocesamiento.py y produce:
  - Estadísticas descriptivas
  - Análisis por tipo de buque / segmento (ranking)
  - Comparativa sequía (FY2024) vs recuperación (FY2025) vs baseline
  - Tendencia anual y CAGR
  - Ranking de insights clave para el dashboard

Nota: la ACP publica el desglose por segmento a nivel anual, por lo que este
módulo no realiza descomposición estacional mensual (no hay meses).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RUTA_BASE = Path(__file__).resolve().parents[1]
RUTA_PROCESSED = RUTA_BASE / "data" / "processed"
RUTA_OUTPUT = RUTA_BASE / "output"

RUTA_UNIFICADO = RUTA_PROCESSED / "canal_unificado.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("analisis_tendencias")


# ---------------------------------------------------------------------------
# 1. Carga
# ---------------------------------------------------------------------------
def cargar_unificado() -> pd.DataFrame:
    if not RUTA_UNIFICADO.exists():
        raise FileNotFoundError(
            f"No se encontró {RUTA_UNIFICADO}. Ejecuta primero: python src/preprocesamiento.py"
        )
    df = pd.read_csv(RUTA_UNIFICADO)
    log.info("Dataset unificado cargado: %d filas", df.shape[0])
    return df


# ---------------------------------------------------------------------------
# 2. Estadísticas descriptivas
# ---------------------------------------------------------------------------
def estadisticas_descriptivas(df: pd.DataFrame) -> dict:
    """Estadísticas agregadas por segmento y totales."""
    log.info("Calculando estadísticas descriptivas")

    num_cols = ["transitos", "calado_promedio_pies", "toneladas_cp_suez", "peajes_usd"]
    desc_segmento = (
        df.groupby("segmento")[num_cols].agg(["mean", "median", "std", "min", "max"]).round(2)
    )
    desc_total = df[num_cols].describe().round(2)

    anios = sorted(df["anio_fiscal"].unique().tolist())
    resumen = {
        "anio_fiscal_inicio": int(min(anios)),
        "anio_fiscal_fin": int(max(anios)),
        "anios_cubiertos": int(len(anios)),
        "segmentos": int(df["segmento"].nunique()),
        "filas_totales": int(df.shape[0]),
        "transitos_total_periodo": int(df["transitos"].sum()),
        "transitos_promedio_anio": round(df.groupby("anio_fiscal")["transitos"].sum().mean(), 1),
        "toneladas_total_periodo": int(df["toneladas_cp_suez"].sum()),
        "peajes_total_periodo_usd": int(df["peajes_usd"].sum()),
        "calado_promedio_global_pies": round(df["calado_promedio_pies"].mean(), 2),
    }
    return {
        "resumen": resumen,
        "descripcion_por_segmento": desc_segmento,
        "descripcion_total": desc_total,
    }


# ---------------------------------------------------------------------------
# 3. Análisis por tipo de buque / segmento
# ---------------------------------------------------------------------------
def ranking_segmentos(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de segmentos por tránsito y por participación."""
    log.info("Ranking de segmentos")
    base = (
        df.groupby("segmento")
        .agg(
            transitos_total=("transitos", "sum"),
            transitos_promedio_anio=("transitos", "mean"),
            calado_promedio=("calado_promedio_pies", "mean"),
            toneladas_total=("toneladas_cp_suez", "sum"),
            peajes_total_usd=("peajes_usd", "sum"),
        )
        .round(2)
    )
    total = base["transitos_total"].sum()
    base["participacion_pct"] = (base["transitos_total"] / total * 100).round(2)
    return base.sort_values("transitos_total", ascending=False)


# ---------------------------------------------------------------------------
# 4. Comparativa sequía vs recuperación
# ---------------------------------------------------------------------------
def impacto_eventos_macro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cuantifica el impacto de la sequía (FY2024) y la recuperación (FY2025)
    sobre los tránsitos por segmento, frente al baseline (FY2020–FY2023).
    """
    log.info("Calculando impacto de eventos macro")
    df = df.copy()
    df["periodo"] = np.select(
        [df["periodo_sequia"] == 1, df["periodo_recuperacion"] == 1],
        ["sequia", "recuperacion"],
        default="baseline",
    )
    prom = (
        df.groupby(["periodo", "segmento"])["transitos"]
        .mean()
        .reset_index()
        .rename(columns={"transitos": "transitos_promedio_anio"})
    )
    pivot = prom.pivot(index="segmento", columns="periodo", values="transitos_promedio_anio")
    for col in ("baseline", "sequia", "recuperacion"):
        if col not in pivot.columns:
            pivot[col] = np.nan
    pivot["var_sequia_pct"] = ((pivot["sequia"] - pivot["baseline"]) / pivot["baseline"] * 100).round(2)
    pivot["var_recuperacion_pct"] = ((pivot["recuperacion"] - pivot["baseline"]) / pivot["baseline"] * 100).round(2)
    return pivot.reset_index().sort_values("baseline", ascending=False)


# ---------------------------------------------------------------------------
# 5. Tendencia anual y CAGR
# ---------------------------------------------------------------------------
def tendencia_anual(df: pd.DataFrame) -> dict:
    """Tránsitos por año fiscal y CAGR del período total."""
    log.info("Calculando tendencia anual y CAGR")
    anual = (
        df.groupby("anio_fiscal")["transitos"]
        .sum()
        .reset_index()
        .rename(columns={"transitos": "transitos_anuales"})
        .sort_values("anio_fiscal")
    )
    anio_ini = int(anual["anio_fiscal"].min())
    anio_fin = int(anual["anio_fiscal"].max())
    trans_ini = float(anual.loc[anual["anio_fiscal"] == anio_ini, "transitos_anuales"].iloc[0])
    trans_fin = float(anual.loc[anual["anio_fiscal"] == anio_fin, "transitos_anuales"].iloc[0])
    n_anios = anio_fin - anio_ini
    cagr = ((trans_fin / trans_ini) ** (1 / n_anios) - 1) * 100 if n_anios > 0 else 0.0

    if len(anual) >= 3:
        corr, pval = stats.pearsonr(anual["anio_fiscal"], anual["transitos_anuales"])
        pendiente_significativa = bool(pval < 0.05)
    else:
        corr, pval, pendiente_significativa = float("nan"), float("nan"), False

    return {
        "tabla_anual": anual.round(2),
        "cagr_pct": round(cagr, 2),
        "correlacion_tiempo": round(float(corr), 3),
        "p_value": round(float(pval), 4),
        "tendencia_significativa": pendiente_significativa,
        "anio_inicio": anio_ini,
        "anio_fin": anio_fin,
    }


# ---------------------------------------------------------------------------
# 6. Generación de insights (texto para Persona 5 / LLM)
# ---------------------------------------------------------------------------
def generar_insights(
    resumen: dict,
    ranking: pd.DataFrame,
    impacto: pd.DataFrame,
    tendencia: dict,
) -> list[dict]:
    log.info("Generando insights clave")
    insights = []

    insights.append({
        "id": "rango",
        "titulo": "Cobertura del dataset",
        "detalle": (
            f"Datos de los años fiscales {resumen['anio_fiscal_inicio']}–"
            f"{resumen['anio_fiscal_fin']} ({resumen['anios_cubiertos']} años, "
            f"{resumen['segmentos']} segmentos). Total de tránsitos: "
            f"{resumen['transitos_total_periodo']:,}; peajes acumulados: "
            f"USD {resumen['peajes_total_periodo_usd']:,}."
        ),
    })

    top = ranking.index[0]
    top_share = float(ranking.iloc[0]["participacion_pct"])
    insights.append({
        "id": "segmento_lider",
        "titulo": "Segmento líder",
        "detalle": (
            f"'{top}' domina con {top_share:.1f}% de los tránsitos del período "
            f"y un promedio anual de {ranking.iloc[0]['transitos_promedio_anio']:.0f} tránsitos."
        ),
    })

    if "var_sequia_pct" in impacto.columns:
        impacto_sorted = impacto.dropna(subset=["var_sequia_pct"]).sort_values("var_sequia_pct")
        seg = impacto_sorted.iloc[0]["segmento"]
        var = float(impacto_sorted.iloc[0]["var_sequia_pct"])
        insights.append({
            "id": "impacto_sequia",
            "titulo": "Impacto de la sequía (FY2024)",
            "detalle": (
                f"Durante la sequía, '{seg}' cayó {abs(var):.1f}% frente al baseline "
                f"(de {impacto_sorted.iloc[0]['baseline']:.0f} a "
                f"{impacto_sorted.iloc[0]['sequia']:.0f} tránsitos anuales)."
            ),
        })

    if "var_recuperacion_pct" in impacto.columns:
        rec_sorted = impacto.dropna(subset=["var_recuperacion_pct"]).sort_values(
            "var_recuperacion_pct", ascending=False
        )
        seg = rec_sorted.iloc[0]["segmento"]
        var = float(rec_sorted.iloc[0]["var_recuperacion_pct"])
        insights.append({
            "id": "recuperacion_2025",
            "titulo": "Recuperación (FY2025)",
            "detalle": (
                f"En FY2025, '{seg}' supera el baseline en {var:.1f}% "
                f"({rec_sorted.iloc[0]['recuperacion']:.0f} tránsitos; "
                f"baseline: {rec_sorted.iloc[0]['baseline']:.0f})."
            ),
        })

    insights.append({
        "id": "tendencia",
        "titulo": "Tendencia de largo plazo",
        "detalle": (
            f"CAGR FY{tendencia['anio_inicio']}–FY{tendencia['anio_fin']}: "
            f"{tendencia['cagr_pct']:.2f}% anual. "
            f"Correlación Pearson(tránsitos, año) = {tendencia['correlacion_tiempo']} "
            f"(p={tendencia['p_value']}); "
            f"{'tendencia significativa' if tendencia['tendencia_significativa'] else 'tendencia no significativa'}."
        ),
    })

    return insights


# ---------------------------------------------------------------------------
# 7. Orquestación
# ---------------------------------------------------------------------------
def ejecutar() -> dict:
    log.info("=== INICIO ANÁLISIS DE TENDENCIAS PERSONA 3 ===")
    RUTA_OUTPUT.mkdir(parents=True, exist_ok=True)

    df = cargar_unificado()
    desc = estadisticas_descriptivas(df)
    desc["descripcion_por_segmento"].to_csv(RUTA_OUTPUT / "stats_por_segmento.csv")
    desc["descripcion_total"].to_csv(RUTA_OUTPUT / "stats_totales.csv")

    ranking = ranking_segmentos(df)
    ranking.to_csv(RUTA_OUTPUT / "ranking_segmentos.csv")

    impacto = impacto_eventos_macro(df)
    impacto.to_csv(RUTA_OUTPUT / "impacto_sequia_recuperacion.csv", index=False)

    tendencia = tendencia_anual(df)
    tendencia["tabla_anual"].to_csv(RUTA_OUTPUT / "tendencia_anual.csv", index=False)

    insights = generar_insights(desc["resumen"], ranking, impacto, tendencia)
    with open(RUTA_OUTPUT / "insights.json", "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    log.info("%d insights guardados en insights.json", len(insights))

    log.info("=== ANÁLISIS COMPLETADO ===")
    return {
        "descripcion": desc,
        "ranking": ranking,
        "impacto": impacto,
        "tendencia": tendencia,
        "insights": insights,
    }


if __name__ == "__main__":
    ejecutar()
