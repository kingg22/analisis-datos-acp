"""
entrenamiento.py
================

Persona 4 - Entrenamiento y evaluación del modelo predictivo.

El modelo predice los **tránsitos de cada segmento de mercado** en un año fiscal;
el volumen anual total del Canal se obtiene sumando los 10 segmentos.

Validación: **Leave-One-Year-Out (LOYO)**
-----------------------------------------
Se deja fuera un año fiscal COMPLETO (sus 10 segmentos), se entrena con los 5
años restantes y se predice el año excluido; se repite para los 6 años. Es una
validación honesta y exigente: el modelo nunca ve el año que predice, ni
siquiera parcialmente, así que no puede filtrarse información del futuro.

Modelos comparados
------------------
  1. Media histórica  — baseline sin aprendizaje (predice el promedio global).
  2. Ridge            — regresión lineal regularizada sobre las features.
  3. Gradient Boosting — ensamble de árboles por refuerzo.
  4. Random Forest    — ensamble de árboles por bagging.

Criterio de selección: **menor MAE a nivel de segmento**.
Se usa MAE y no MAPE porque a nivel de segmento el MAPE se dispara con los
denominadores pequeños (p. ej. 'Pasajeros' cayó a 17 tránsitos en FY2021 por la
pandemia: un error de 100 tránsitos ahí pesa 588 %, más que un error de 1,000 en
portacontenedores). El MAPE se reporta igualmente, y además se calcula sobre el
**total anual agregado**, que es la métrica de negocio relevante.
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
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import preparacion_datos as prep

log = logging.getLogger("persona4.entrenamiento")

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "output"
MODELS = BASE / "models"

SEMILLA = 42


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAPE (%) ignorando denominadores nulos."""
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


def _definir_modelos() -> dict[str, object]:
    return {
        "Media_Historica": DummyRegressor(strategy="mean"),
        "Ridge": Ridge(alpha=1.0),
        "Gradient_Boosting": GradientBoostingRegressor(random_state=SEMILLA),
        "Random_Forest": RandomForestRegressor(n_estimators=300, random_state=SEMILLA),
    }


def loyo_predicciones(df: pd.DataFrame, X: pd.DataFrame, estimador) -> np.ndarray:
    """Predicciones Leave-One-Year-Out: cada año se predice sin haberlo visto."""
    y = df[prep.TARGET].to_numpy()
    preds = np.empty(len(y), dtype=float)
    for anio in sorted(df["anio_fiscal"].unique()):
        test = (df["anio_fiscal"] == anio).to_numpy()
        modelo = clone(estimador).fit(X[~test], y[~test])
        preds[test] = modelo.predict(X[test])
    return np.clip(preds, 0, None)


def _metricas_anuales(df: pd.DataFrame, preds: np.ndarray) -> dict[str, float]:
    """Agrega las predicciones por año fiscal y evalúa el total anual."""
    agg = (
        df.assign(pred=preds)
        .groupby("anio_fiscal")
        .agg(real=(prep.TARGET, "sum"), pred=("pred", "sum"))
    )
    return {
        "MAE_total_anual": float(mean_absolute_error(agg["real"], agg["pred"])),
        "MAPE_total_anual": mape(agg["real"].to_numpy(), agg["pred"].to_numpy()),
    }


def ejecutar() -> dict:
    """Entrena, evalúa (LOYO), selecciona y serializa el mejor modelo."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = prep.preparar(persistir=True)
    X = prep.matriz_features(df)
    y = df[prep.TARGET].to_numpy()

    resultados: dict[str, dict[str, float]] = {}
    preds_por_modelo: dict[str, np.ndarray] = {}

    log.info("--- Validación Leave-One-Year-Out (%d obs., %d años) ---",
             len(df), df["anio_fiscal"].nunique())
    for nombre, estimador in _definir_modelos().items():
        preds = loyo_predicciones(df, X, estimador)
        metricas = evaluar(y, preds) | _metricas_anuales(df, preds)
        resultados[nombre] = metricas
        preds_por_modelo[nombre] = preds
        log.info(
            "%-18s -> MAE=%6.1f  R2=%+.3f  | total anual: MAPE=%5.2f%%",
            nombre, metricas["MAE"], metricas["R2"], metricas["MAPE_total_anual"],
        )

    # Selección por menor MAE a nivel de segmento (ver docstring del módulo).
    ganador = min(resultados, key=lambda n: resultados[n]["MAE"])
    baseline = resultados["Media_Historica"]["MAE"]
    mejora = (baseline - resultados[ganador]["MAE"]) / baseline * 100
    log.info("Modelo ganador: %s (MAE=%.1f, %.1f%% mejor que el baseline)",
             ganador, resultados[ganador]["MAE"], mejora)

    # Reentrenar el ganador con TODO el panel.
    modelo_final = clone(_definir_modelos()[ganador]).fit(X, y)
    with open(MODELS / "modelo_transitos.pkl", "wb") as fh:
        pickle.dump(
            {"modelo": modelo_final, "features": list(X.columns), "nombre": ganador},
            fh,
        )

    _persistir_artefactos(df, preds_por_modelo[ganador], resultados, modelo_final, X)

    resumen = {
        "modelo_ganador": ganador,
        "criterio_seleccion": "menor MAE (nivel segmento) en validación Leave-One-Year-Out",
        "n_observaciones": int(len(df)),
        "n_segmentos": int(df["segmento"].nunique()),
        "n_anios": int(df["anio_fiscal"].nunique()),
        "granularidad": "segmento × año fiscal (ACP)",
        "mejora_vs_baseline_pct": round(mejora, 1),
        "metricas": resultados,
    }
    with open(OUTPUT / "resumen_entrenamiento.json", "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    log.info("Artefactos guardados en %s", OUTPUT)
    return resumen


def _persistir_artefactos(
    df: pd.DataFrame,
    preds_ganador: np.ndarray,
    resultados: dict[str, dict[str, float]],
    modelo_final,
    X: pd.DataFrame,
) -> None:
    """Escribe los CSV que consume el dashboard de Persona 5."""
    # Detalle por segmento (validación LOYO del ganador).
    detalle = df[["anio_fiscal", "segmento", prep.TARGET]].copy()
    detalle = detalle.rename(columns={prep.TARGET: "transitos_reales"})
    detalle["transitos_predichos"] = np.round(preds_ganador, 0)
    detalle.to_csv(OUTPUT / "predicciones_test_por_segmento.csv", index=False)

    # Total anual agregado (formato esperado por el dashboard).
    anual = (
        detalle.groupby("anio_fiscal")[["transitos_reales", "transitos_predichos"]]
        .sum()
        .reset_index()
    )
    anual.to_csv(OUTPUT / "predicciones_test.csv", index=False)

    # Tabla comparativa de métricas.
    (
        pd.DataFrame(resultados).T.reset_index(names="modelo").sort_values("MAE")
        .to_csv(OUTPUT / "metricas_modelos.csv", index=False)
    )

    # Importancia de features del ganador.
    importancias = _importancia_features(modelo_final, list(X.columns))
    if importancias is not None:
        importancias.to_csv(OUTPUT / "importancia_features.csv", index=False)


def _importancia_features(modelo, feats: list[str]) -> pd.DataFrame | None:
    if hasattr(modelo, "feature_importances_"):
        valores, etiqueta = modelo.feature_importances_, "importancia"
    elif hasattr(modelo, "coef_"):
        valores, etiqueta = np.abs(np.ravel(modelo.coef_)), "coef_abs"
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
