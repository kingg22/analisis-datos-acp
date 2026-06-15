"""
analisis_tendencias.py
======================

Persona 3 - Análisis Exploratorio de Tendencias de Tránsitos
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Carga el dataset unificado de preprocesamiento.py y produce:
  - Estadísticas descriptivas
  - Descomposición estacional (tendencia / estacionalidad / residuo)
  - Análisis por tipo de buque / segmento
  - Comparativa sequía (2023–may-2024) vs recuperación (2025+)
  - Ranking de insights clave para el dashboard
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
            f"No se encontró {RUTA_UNIFICADO}. "
            "Ejecuta primero: python src/preprocesamiento.py"
        )
    df = pd.read_csv(RUTA_UNIFICADO, parse_dates=["fecha"])
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
        df.groupby("segmento")[num_cols]
        .agg(["mean", "median", "std", "min", "max"])
        .round(2)
    )
    desc_total = df[num_cols].describe().round(2)

    # Meses cubiertos
    meses_unicos = df["fecha"].dt.to_period("M").nunique()
    rango_fechas = (df["fecha"].min().date(), df["fecha"].max().date())

    resumen = {
        "rango_fechas": {"inicio": str(rango_fechas[0]), "fin": str(rango_fechas[1])},
        "meses_cubiertos": int(meses_unicos),
        "segmentos": int(df["segmento"].nunique()),
        "filas_totales": int(df.shape[0]),
        "transitos_total_periodo": int(df["transitos"].sum()),
        "transitos_promedio_mes": round(df.groupby("fecha")["transitos"].sum().mean(), 1),
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
# 3. Descomposición estacional (clásica aditiva)
# ---------------------------------------------------------------------------
def descomposicion_estacional(df: pd.DataFrame, periodo: int = 12) -> dict:
    """
    Descomposición clásica aditiva (media móvil centrada) sobre la serie
    mensual total de tránsitos. Devuelve los componentes en una Serie.
    """
    log.info("Descomposición estacional (período=%d)", periodo)
    serie = (
        df.groupby("fecha")["transitos"]
        .sum()
        .sort_index()
        .asfreq("MS")
    )

    # Media móvil centrada
    tendencia = serie.rolling(window=periodo, center=True, min_periods=1).mean()
    detrend = serie - tendencia
    estacional_idx = detrend.index.month
    estacionalidad = detrend.groupby(estacional_idx).mean()
    residuo = serie - tendencia - estacionalidad.reindex(estacional_idx).values

    # Estacionalidad relativa (% sobre la media)
    media = serie.mean()
    estacional_pct = (estacionalidad / media * 100).round(2)

    return {
        "serie": serie,
        "tendencia": tendencia,
        "estacionalidad": estacionalidad,
        "estacionalidad_pct": estacional_pct,
        "residuo": residuo,
    }


# ---------------------------------------------------------------------------
# 4. Análisis por tipo de buque / segmento
# ---------------------------------------------------------------------------
def ranking_segmentos(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de segmentos por tránsito y por participación."""
    log.info("Ranking de segmentos")
    base = (
        df.groupby("segmento")
        .agg(
            transitos_total=("transitos", "sum"),
            transitos_promedio_mes=("transitos", "mean"),
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
# 5. Comparativa sequía vs recuperación
# ---------------------------------------------------------------------------
def impacto_eventos_macro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cuantifica el impacto de la sequía 2023–may-2024 y la recuperación 2025+
    sobre el total de tránsitos por segmento.
    """
    log.info("Calculando impacto de eventos macro")
    df = df.copy()
    df["periodo"] = np.select(
        [
            df["periodo_sequia"] == 1,
            df["periodo_recuperacion"] == 1,
        ],
        ["sequia", "recuperacion"],
        default="baseline",
    )

    # Promedio mensual de tránsitos por período y segmento
    prom = (
        df.groupby(["periodo", "segmento"])["transitos"]
        .mean()
        .reset_index()
        .rename(columns={"transitos": "transitos_promedio_mes"})
    )
    # Pivot para tener una fila por segmento
    pivot = prom.pivot(index="segmento", columns="periodo", values="transitos_promedio_mes")
    # Garantizar columnas
    for col in ("baseline", "sequia", "recuperacion"):
        if col not in pivot.columns:
            pivot[col] = np.nan
    # Variaciones porcentuales
    pivot["var_sequia_pct"] = ((pivot["sequia"] - pivot["baseline"]) / pivot["baseline"] * 100).round(2)
    pivot["var_recuperacion_pct"] = ((pivot["recuperacion"] - pivot["baseline"]) / pivot["baseline"] * 100).round(2)
    return pivot.reset_index().sort_values("baseline", ascending=False)


# ---------------------------------------------------------------------------
# 6. Estacionalidad por fase fiscal
# ---------------------------------------------------------------------------
def estacionalidad_fase_fiscal(df: pd.DataFrame) -> pd.DataFrame:
    """Tránsitos promedio por fase fiscal ACP (oct→sep)."""
    log.info("Estacionalidad por fase fiscal")
    return (
        df.groupby(["fase_fiscal", "segmento"])["transitos"]
        .mean()
        .reset_index()
        .rename(columns={"transitos": "transitos_promedio"})
        .round(2)
    )


# ---------------------------------------------------------------------------
# 7. Tendencia anual y CAGR
# ---------------------------------------------------------------------------
def tendencia_anual(df: pd.DataFrame) -> dict:
    """Tránsitos anuales y CAGR del período total."""
    log.info("Calculando tendencia anual y CAGR")
    anual = (
        df.groupby("anio")["transitos"]
        .sum()
        .reset_index()
        .rename(columns={"transitos": "transitos_anuales"})
    )
    anio_ini = int(anual["anio"].min())
    anio_fin = int(anual["anio"].max())
    trans_ini = float(anual.loc[anual["anio"] == anio_ini, "transitos_anuales"].iloc[0])
    trans_fin = float(anual.loc[anual["anio"] == anio_fin, "transitos_anuales"].iloc[0])
    n_anios = anio_fin - anio_ini
    cagr = ((trans_fin / trans_ini) ** (1 / n_anios) - 1) * 100 if n_anios > 0 else 0.0

    # Test de Mann-Kendall simplificado: correlación de Pearson vs tiempo
    if len(anual) >= 3:
        corr, pval = stats.pearsonr(anual["anio"], anual["transitos_anuales"])
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
# 8. Generación de insights (texto para Persona 5 / LLM)
# ---------------------------------------------------------------------------
def generar_insights(
    resumen: dict,
    ranking: pd.DataFrame,
    impacto: pd.DataFrame,
    tendencia: dict,
    descomposicion: dict,
) -> list[dict]:
    log.info("Generando insights clave")
    insights = []

    # Insight 1: rango y volumen
    insights.append({
        "id": "rango",
        "titulo": "Cobertura del dataset",
        "detalle": (
            f"Datos desde {resumen['rango_fechas']['inicio']} hasta "
            f"{resumen['rango_fechas']['fin']} ({resumen['meses_cubiertos']} meses, "
            f"{resumen['segmentos']} segmentos). Total de tránsitos: "
            f"{resumen['transitos_total_periodo']:,}; peajes acumulados: "
            f"USD {resumen['peajes_total_periodo_usd']:,}."
        ),
    })

    # Insight 2: segmento líder
    top = ranking.index[0]
    top_share = float(ranking.iloc[0]["participacion_pct"])
    insights.append({
        "id": "segmento_lider",
        "titulo": "Segmento líder",
        "detalle": (
            f"'{top}' domina con {top_share:.1f}% de los tránsitos del período "
            f"y un promedio mensual de {ranking.iloc[0]['transitos_promedio_mes']:.0f} tránsitos."
        ),
    })

    # Insight 3: impacto sequía
    if "var_sequia_pct" in impacto.columns:
        impacto_sorted = impacto.dropna(subset=["var_sequia_pct"]).sort_values("var_sequia_pct")
        seg_mas_golpeado = impacto_sorted.iloc[0]["segmento"]
        var = float(impacto_sorted.iloc[0]["var_sequia_pct"])
        insights.append({
            "id": "impacto_sequia",
            "titulo": "Impacto de la sequía 2023–may-2024",
            "detalle": (
                f"Durante la sequía, '{seg_mas_golpeado}' cayó {abs(var):.1f}% "
                f"frente al baseline. Promedio mensual pasó de "
                f"{impacto_sorted.iloc[0]['baseline']:.0f} a "
                f"{impacto_sorted.iloc[0]['sequia']:.0f} tránsitos."
            ),
        })

    # Insight 4: recuperación 2025
    if "var_recuperacion_pct" in impacto.columns:
        rec_sorted = impacto.dropna(subset=["var_recuperacion_pct"]).sort_values(
            "var_recuperacion_pct", ascending=False
        )
        seg_mas_recuperado = rec_sorted.iloc[0]["segmento"]
        var = float(rec_sorted.iloc[0]["var_recuperacion_pct"])
        insights.append({
            "id": "recuperacion_2025",
            "titulo": "Recuperación 2025+",
            "detalle": (
                f"En 2025, '{seg_mas_recuperado}' supera el baseline en {var:.1f}%. "
                f"Promedio mensual: {rec_sorted.iloc[0]['recuperacion']:.0f} tránsitos "
                f"(baseline: {rec_sorted.iloc[0]['baseline']:.0f})."
            ),
        })

    # Insight 5: estacionalidad
    est_pct = descomposicion["estacionalidad_pct"]
    mes_pico = int(est_pct.idxmax())
    mes_valle = int(est_pct.idxmin())
    insights.append({
        "id": "estacionalidad",
        "titulo": "Estacionalidad",
        "detalle": (
            f"Mes calendario pico: {mes_pico} (+{est_pct.max():.2f}% sobre la media). "
            f"Mes valle: {mes_valle} ({est_pct.min():.2f}% sobre la media). "
            f"Amplitud estacional: {(est_pct.max() - est_pct.min()):.2f} puntos porcentuales."
        ),
    })

    # Insight 6: tendencia
    insights.append({
        "id": "tendencia",
        "titulo": "Tendencia de largo plazo",
        "detalle": (
            f"CAGR {tendencia['anio_inicio']}–{tendencia['anio_fin']}: {tendencia['cagr_pct']:.2f}% anual. "
            f"Correlación Pearson(tránsitos, año) = {tendencia['correlacion_tiempo']} "
            f"(p={tendencia['p_value']}); "
            f"{'tendencia estadísticamente significativa' if tendencia['tendencia_significativa'] else 'tendencia no significativa'}."
        ),
    })

    return insights


# ---------------------------------------------------------------------------
# 9. Orquestación
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

    estacionalidad = estacionalidad_fase_fiscal(df)
    estacionalidad.to_csv(RUTA_OUTPUT / "estacionalidad_fase_fiscal.csv", index=False)

    tendencia = tendencia_anual(df)
    tendencia["tabla_anual"].to_csv(RUTA_OUTPUT / "tendencia_anual.csv", index=False)

    descomposicion = descomposicion_estacional(df)
    # Persistir componentes clave
    componentes = pd.DataFrame({
        "fecha": descomposicion["serie"].index,
        "observado": descomposicion["serie"].values,
        "tendencia": descomposicion["tendencia"].values,
        "residuo": descomposicion["residuo"].values,
    })
    componentes.to_csv(RUTA_OUTPUT / "descomposicion_serie.csv", index=False)
    descomposicion["estacionalidad"].to_frame("componente_estacional").to_csv(
        RUTA_OUTPUT / "componente_estacional.csv"
    )

    insights = generar_insights(desc["resumen"], ranking, impacto, tendencia, descomposicion)
    with open(RUTA_OUTPUT / "insights.json", "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    log.info("%d insights guardados en insights.json", len(insights))

    log.info("=== ANÁLISIS COMPLETADO ===")
    return {
        "descripcion": desc,
        "ranking": ranking,
        "impacto": impacto,
        "estacionalidad_fase_fiscal": estacionalidad,
        "tendencia": tendencia,
        "descomposicion": descomposicion,
        "insights": insights,
    }


if __name__ == "__main__":
    ejecutar()
