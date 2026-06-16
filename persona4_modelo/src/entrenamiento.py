"""
entrenamiento.py
================

Persona 4 - Entrenamiento y evaluación del modelo predictivo.

Predice el volumen mensual de tránsitos totales del Canal de Panamá usando un
hold-out temporal (no aleatorio, para respetar el orden de la serie):

  - ENTRENAMIENTO: hasta 2024-09 (inclusive)
  - PRUEBA:        2024-10 → 2025-12

Compara cuatro enfoques y selecciona el de menor MAPE en el conjunto de prueba:

  1. Naive estacional  — t = t-12 (baseline; sin aprendizaje)
  2. Regresión lineal  — modelo interpretable de referencia
  3. Random Forest     — no lineal, robusto a interacciones
  4. Gradient Boosting — no lineal, suele liderar en series tabulares

Métricas: MAE, RMSE, MAPE (%) y R². El modelo ganador se reentrena con toda la
serie y se serializa en `models/` para alimentar la generación de predicciones.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

import preparacion_datos as prep

log = logging.getLogger("persona4.entrenamiento")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
MODELS = BASE / "models"

# Corte del hold-out temporal (recomendado por Persona 3 en HALLAZGOS.md).
CORTE_ENTRENAMIENTO = pd.Timestamp("2024-09-01")

SEED = 42


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error en %."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluar(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Calcula MAE, RMSE, MAPE y R² para un conjunto de predicciones."""
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE": mape(y_true, y_pred),
        "R2": float(r2_score(y_true, y_pred)),
    }


def _definir_modelos() -> dict[str, object]:
    """Modelos de scikit-learn a comparar (excluye el baseline naive)."""
    return {
        "Regresion_Lineal": LinearRegression(),
        "Random_Forest": RandomForestRegressor(
            n_estimators=400, max_depth=6, min_samples_leaf=2,
            random_state=SEED, n_jobs=-1,
        ),
        "Gradient_Boosting": GradientBoostingRegressor(
            n_estimators=400, max_depth=3, learning_rate=0.03,
            subsample=0.9, random_state=SEED,
        ),
    }


def cross_validation_temporal(df: pd.DataFrame, feats: list[str], target: str,
                              n_splits: int = 5) -> dict[str, dict[str, float]]:
    """Validación cruzada de ventana expansiva (TimeSeriesSplit).

    Métrica primaria y más robusta que un único hold-out: promedia el error
    sobre `n_splits` cortes temporales sucesivos, respetando el orden de la
    serie (nunca entrena con datos futuros).
    """
    X = df[feats].to_numpy()
    y = df[target].to_numpy()
    tscv = TimeSeriesSplit(n_splits=n_splits)

    cv: dict[str, dict[str, float]] = {}
    for nombre, modelo_base in _definir_modelos().items():
        mapes, maes = [], []
        for idx_tr, idx_te in tscv.split(X):
            modelo = clone(modelo_base)
            modelo.fit(X[idx_tr], y[idx_tr])
            pred = modelo.predict(X[idx_te])
            mapes.append(mape(y[idx_te], pred))
            maes.append(mean_absolute_error(y[idx_te], pred))
        cv[nombre] = {
            "MAPE_cv": float(np.mean(mapes)),
            "MAPE_cv_std": float(np.std(mapes)),
            "MAE_cv": float(np.mean(maes)),
        }
        log.info("CV %-18s -> MAPE=%.2f%% (±%.2f)  MAE=%.1f",
                 nombre, cv[nombre]["MAPE_cv"], cv[nombre]["MAPE_cv_std"],
                 cv[nombre]["MAE_cv"])
    return cv


def ejecutar() -> dict:
    """Entrena, evalúa, selecciona y serializa el mejor modelo.

    Devuelve un dict con el resumen de métricas y el nombre del modelo ganador.
    La selección se basa en la **validación cruzada temporal** (métrica robusta);
    el hold-out 2024-10→2025-12 se reporta como prueba de estrés ante el quiebre
    de régimen de 2025.
    """
    OUTPUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = prep.preparar(persistir=True)
    feats = prep.COLUMNAS_FEATURES
    target = prep.TARGET

    # --- Validación cruzada temporal (selección del ganador) ----------------
    log.info("--- Validación cruzada temporal (ventana expansiva, 5 folds) ---")
    cv = cross_validation_temporal(df, feats, target, n_splits=5)
    ganador = min(cv, key=lambda n: cv[n]["MAPE_cv"])
    log.info("Modelo ganador por CV: %s (MAPE_cv=%.2f%%)", ganador, cv[ganador]["MAPE_cv"])

    # --- Hold-out temporal (prueba de estrés del régimen 2025) --------------
    log.info("--- Hold-out temporal (stress test) ---")
    train = df[df["fecha"] <= CORTE_ENTRENAMIENTO]
    test = df[df["fecha"] > CORTE_ENTRENAMIENTO]
    log.info("Entrenamiento: %d meses | Prueba: %d meses", len(train), len(test))

    X_train, y_train = train[feats], train[target].to_numpy()
    X_test, y_test = test[feats], test[target].to_numpy()

    resultados: dict[str, dict[str, float]] = {}
    modelos_entrenados: dict[str, object] = {}

    # Baseline naive estacional (t = t-12) sobre el hold-out.
    pred_naive = test["lag_12"].to_numpy()
    resultados["Naive_Estacional"] = evaluar(y_test, pred_naive)
    log.info("Naive_Estacional   -> MAPE=%.2f%%  MAE=%.1f",
             resultados["Naive_Estacional"]["MAPE"],
             resultados["Naive_Estacional"]["MAE"])

    for nombre, modelo in _definir_modelos().items():
        modelo.fit(X_train, y_train)
        pred = modelo.predict(X_test)
        resultados[nombre] = evaluar(y_test, pred)
        # Adjuntar la métrica de CV a la fila del modelo.
        resultados[nombre].update(cv[nombre])
        modelos_entrenados[nombre] = modelo
        log.info("%-18s -> [hold-out] MAPE=%.2f%%  MAE=%.1f  R2=%.3f",
                 nombre, resultados[nombre]["MAPE"],
                 resultados[nombre]["MAE"], resultados[nombre]["R2"])

    # --- Reentrenamiento del ganador con TODA la serie ----------------------
    modelo_final = _definir_modelos()[ganador]
    modelo_final.fit(df[feats], df[target].to_numpy())

    # --- Persistencia -------------------------------------------------------
    with open(MODELS / "modelo_transitos.pkl", "wb") as fh:
        pickle.dump({"modelo": modelo_final, "features": feats, "nombre": ganador}, fh)

    # Predicciones del conjunto de prueba (para la figura del dashboard).
    pred_test_ganador = modelos_entrenados[ganador].predict(X_test)
    df_pred_test = pd.DataFrame({
        "fecha": test["fecha"].values,
        "transitos_reales": y_test,
        "transitos_predichos": np.round(pred_test_ganador, 0),
    })
    df_pred_test.to_csv(OUTPUT / "predicciones_test.csv", index=False)

    # Tabla comparativa de métricas.
    df_metricas = pd.DataFrame(resultados).T.reset_index(names="modelo")
    df_metricas = df_metricas.sort_values("MAPE").reset_index(drop=True)
    df_metricas.to_csv(OUTPUT / "metricas_modelos.csv", index=False)

    # Importancia de features (si el modelo la expone).
    importancias = _importancia_features(modelo_final, feats)
    if importancias is not None:
        importancias.to_csv(OUTPUT / "importancia_features.csv", index=False)

    resumen = {
        "modelo_ganador": ganador,
        "criterio_seleccion": "menor MAPE en validación cruzada temporal",
        "corte_entrenamiento": str(CORTE_ENTRENAMIENTO.date()),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "cross_validation": cv,
        "metricas": resultados,
    }
    with open(OUTPUT / "resumen_entrenamiento.json", "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    log.info("Artefactos guardados en %s", OUTPUT)
    return resumen


def _importancia_features(modelo, feats: list[str]) -> pd.DataFrame | None:
    """Extrae importancia de features (árboles) o coeficientes (lineal)."""
    if hasattr(modelo, "feature_importances_"):
        valores = modelo.feature_importances_
        etiqueta = "importancia"
    elif hasattr(modelo, "coef_"):
        valores = np.abs(modelo.coef_)
        etiqueta = "coef_abs"
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
