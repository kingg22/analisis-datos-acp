"""
entrenamiento.py
================

Persona 4 - Entrenamiento y evaluación del modelo predictivo (ANUAL).

La serie de tránsitos del Canal es anual (un punto por año fiscal), por lo que la
muestra es pequeña. Se comparan modelos simples e interpretables y se evalúan con
**Leave-One-Out** (LOO), la validación adecuada para pocos datos: se deja fuera un
año, se entrena con el resto y se predice el año excluido; se repite para todos.

Modelos comparados:
  1. Media histórica     — baseline (predice el promedio; sin aprendizaje).
  2. Tendencia lineal    — transitos ~ índice de tiempo.
  3. Tendencia + precio  — transitos ~ índice de tiempo + precio del crudo.

Métricas: MAE, RMSE, MAPE (%) y R² (sobre las predicciones LOO). El modelo ganador
se reentrena con toda la serie y se serializa en `models/`.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut

import preparacion_datos as prep

log = logging.getLogger("persona4.entrenamiento")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
MODELS = BASE / "models"


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluar(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE": mape(y_true, y_pred),
        "R2": float(r2_score(y_true, y_pred)),
    }


def _definir_modelos() -> dict[str, dict]:
    """Cada modelo declara su estimador y la lista de features que usa."""
    return {
        "Media_Historica": {
            "estimador": DummyRegressor(strategy="mean"),
            "features": ["indice_tendencia"],  # X ignorado por el baseline
        },
        "Tendencia_Lineal": {
            "estimador": LinearRegression(),
            "features": ["indice_tendencia"],
        },
        "Tendencia_mas_Precio": {
            "estimador": LinearRegression(),
            "features": ["indice_tendencia", "precio_barril_usd_prom"],
        },
    }


def loo_predicciones(df: pd.DataFrame, estimador, feats: list[str], target: str) -> np.ndarray:
    """Predicciones Leave-One-Out para un modelo dado."""
    X = df[feats].to_numpy()
    y = df[target].to_numpy()
    preds = np.empty(len(y), dtype=float)
    for idx_tr, idx_te in LeaveOneOut().split(X):
        m = clone(estimador)
        m.fit(X[idx_tr], y[idx_tr])
        preds[idx_te] = m.predict(X[idx_te])
    return preds


def ejecutar() -> dict:
    """Entrena, evalúa (LOO), selecciona y serializa el mejor modelo."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = prep.preparar(persistir=True)
    target = prep.TARGET
    y = df[target].to_numpy()

    resultados: dict[str, dict[str, float]] = {}
    preds_por_modelo: dict[str, np.ndarray] = {}

    log.info("--- Validación Leave-One-Out (%d años fiscales) ---", len(df))
    for nombre, spec in _definir_modelos().items():
        preds = loo_predicciones(df, spec["estimador"], spec["features"], target)
        resultados[nombre] = evaluar(y, preds)
        preds_por_modelo[nombre] = preds
        log.info("%-22s -> [LOO] MAPE=%.2f%%  MAE=%.1f  R2=%.3f",
                 nombre, resultados[nombre]["MAPE"], resultados[nombre]["MAE"],
                 resultados[nombre]["R2"])

    # Selección del ganador por menor MAPE en LOO.
    ganador = min(resultados, key=lambda n: resultados[n]["MAPE"])
    log.info("Modelo ganador (LOO): %s (MAPE=%.2f%%)", ganador, resultados[ganador]["MAPE"])

    # Reentrenar el ganador con TODA la serie.
    spec = _definir_modelos()[ganador]
    feats = spec["features"]
    modelo_final = clone(spec["estimador"])
    modelo_final.fit(df[feats].to_numpy(), y)

    with open(MODELS / "modelo_transitos.pkl", "wb") as fh:
        pickle.dump({"modelo": modelo_final, "features": feats, "nombre": ganador}, fh)

    # Predicciones LOO del ganador (para la figura del dashboard).
    df_pred = pd.DataFrame({
        "anio_fiscal": df["anio_fiscal"].to_numpy(),
        "transitos_reales": y,
        "transitos_predichos": np.round(preds_por_modelo[ganador], 0),
    })
    df_pred.to_csv(OUTPUT / "predicciones_test.csv", index=False)

    # Tabla comparativa de métricas.
    df_metricas = pd.DataFrame(resultados).T.reset_index(names="modelo").sort_values("MAPE")
    df_metricas.to_csv(OUTPUT / "metricas_modelos.csv", index=False)

    # Importancia / coeficientes del ganador (si es lineal).
    importancias = _importancia_features(modelo_final, feats)
    if importancias is not None:
        importancias.to_csv(OUTPUT / "importancia_features.csv", index=False)

    resumen = {
        "modelo_ganador": ganador,
        "criterio_seleccion": "menor MAPE en validación Leave-One-Out",
        "n_observaciones": int(len(df)),
        "granularidad": "anual (año fiscal ACP)",
        "metricas": resultados,
    }
    with open(OUTPUT / "resumen_entrenamiento.json", "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    log.info("Artefactos guardados en %s", OUTPUT)
    return resumen


def _importancia_features(modelo, feats: list[str]) -> pd.DataFrame | None:
    if hasattr(modelo, "coef_"):
        valores = np.abs(np.ravel(modelo.coef_))
        etiqueta = "coef_abs"
    elif hasattr(modelo, "feature_importances_"):
        valores = modelo.feature_importances_
        etiqueta = "importancia"
    else:
        return None
    return (
        pd.DataFrame({"feature": feats, etiqueta: valores})
        .sort_values(etiqueta, ascending=False)
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    ejecutar()
