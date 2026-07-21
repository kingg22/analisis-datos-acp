"""
Utilidades de carga de datos para el dashboard (granularidad ANUAL).
Resuelve rutas relativas desde la raíz del proyecto.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


# ── Raíz del proyecto (4 niveles arriba de este archivo) ──────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve(*relative: str) -> Path:
    """Devuelve la ruta absoluta dentro del proyecto."""
    return PROJECT_ROOT.joinpath(*relative)


# ── Persona 1 ────────────────────────────────────────────────────────────────
def load_canal_serie_anual() -> pd.DataFrame:
    """Serie anual de tránsitos (Persona 1)."""
    return pd.read_csv(
        _resolve("persona1_ingesta", "data", "processed", "canal_serie_anual.csv")
    )


def load_canal_limpio() -> pd.DataFrame:
    """Dataset limpio de tránsitos por año fiscal y segmento (Persona 1)."""
    return pd.read_csv(
        _resolve("persona1_ingesta", "data", "processed", "canal_limpio.csv")
    )


# ── Persona 2 ────────────────────────────────────────────────────────────────
def load_dataset_unificado() -> pd.DataFrame:
    """Dataset unificado anual de ambas fuentes (Persona 2)."""
    return pd.read_csv(
        _resolve("persona2_pipeline", "data", "processed", "dataset_unificado.csv")
    )


# ── Persona 3 — Procesados ──────────────────────────────────────────────────
def load_canal_unificado() -> pd.DataFrame:
    """Dataset unificado anual con features derivados (Persona 3)."""
    return pd.read_csv(
        _resolve("persona3_analisis", "data", "processed", "canal_unificado.csv")
    )


def load_agregado_serie_total() -> pd.DataFrame:
    """Serie anual total agregada (Persona 3)."""
    return pd.read_csv(
        _resolve("persona3_analisis", "data", "processed", "agregado_serie_total.csv")
    )


def load_agregado_por_segmento() -> pd.DataFrame:
    """Composición por segmento y año fiscal (Persona 3)."""
    return pd.read_csv(
        _resolve("persona3_analisis", "data", "processed", "agregado_por_segmento_anio.csv")
    )


def load_agregado_por_periodo() -> pd.DataFrame:
    """Sequía / baseline / recuperación (Persona 3)."""
    return pd.read_csv(
        _resolve("persona3_analisis", "data", "processed", "agregado_por_periodo.csv")
    )


# ── Persona 3 — Output ──────────────────────────────────────────────────────
def load_insights() -> list[dict[str, Any]]:
    """Insights del EDA (Persona 3)."""
    path = _resolve("persona3_analisis", "output", "insights.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_ranking_segmentos() -> pd.DataFrame:
    return pd.read_csv(_resolve("persona3_analisis", "output", "ranking_segmentos.csv"))


def load_impacto_sequia() -> pd.DataFrame:
    return pd.read_csv(_resolve("persona3_analisis", "output", "impacto_sequia_recuperacion.csv"))


def load_tendencia_anual() -> pd.DataFrame:
    return pd.read_csv(_resolve("persona3_analisis", "output", "tendencia_anual.csv"))


def load_stats_por_segmento() -> pd.DataFrame:
    return pd.read_csv(_resolve("persona3_analisis", "output", "stats_por_segmento.csv"))


def load_stats_totales() -> pd.DataFrame:
    return pd.read_csv(_resolve("persona3_analisis", "output", "stats_totales.csv"))


# ── Persona 4 — Modelo ──────────────────────────────────────────────────────
def load_predicciones_2026() -> pd.DataFrame:
    """Pronóstico anual de próximos años fiscales (Persona 4)."""
    return pd.read_csv(_resolve("persona4_modelo", "output", "predicciones_2026.csv"))


def load_predicciones_test() -> pd.DataFrame:
    """Reales vs predichos en validación Leave-One-Out (Persona 4)."""
    return pd.read_csv(_resolve("persona4_modelo", "output", "predicciones_test.csv"))


def load_metricas_modelos() -> pd.DataFrame:
    """Tabla comparativa de modelos (Persona 4)."""
    return pd.read_csv(_resolve("persona4_modelo", "output", "metricas_modelos.csv"))


def load_importancia_features() -> pd.DataFrame:
    """Coeficientes del modelo ganador (Persona 4). Puede no existir si el ganador es un baseline."""
    ruta = _resolve("persona4_modelo", "output", "importancia_features.csv")
    if not ruta.exists():
        return pd.DataFrame(columns=["feature", "coef_abs"])
    return pd.read_csv(ruta)


def load_resumen_entrenamiento() -> dict[str, Any]:
    """Resumen completo del entrenamiento (Persona 4)."""
    path = _resolve("persona4_modelo", "output", "resumen_entrenamiento.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Figuras ──────────────────────────────────────────────────────────────────
def get_figure_path(persona: str, filename: str) -> Path:
    """Devuelve la ruta a una figura PNG de cualquier persona."""
    return _resolve(persona, "figures", filename)
