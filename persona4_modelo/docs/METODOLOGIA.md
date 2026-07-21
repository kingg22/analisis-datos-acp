# Metodología del Modelo Predictivo — Canal de Panamá

**Responsable:** Persona 4
**Objetivo:** predecir el **volumen anual de tránsitos totales** del Canal de Panamá (por año fiscal ACP).
**Fuente primaria:** `persona2_pipeline/data/processed/dataset_unificado.csv` (serie anual de tránsitos + precio promedio del barril, FY2020–FY2025).
**Generado por:** `python persona4_modelo/src/run_pipeline.py`

---

## 1. Planteamiento

La ACP publica el desglose de tránsitos por segmento a nivel **anual** (año
fiscal, oct–sep). La serie tiene por tanto **6 observaciones** (FY2020–FY2025).
Con tan pocos puntos, el enfoque correcto es un **modelo simple e interpretable**
(regresión de tendencia, con el precio del crudo como variable exógena), no un
ensemble de Machine Learning que requeriría muchas más observaciones y
sobreajustaría de inmediato.

---

## 2. Features

A partir de la serie anual se construyen 2 variables predictoras
(`src/preparacion_datos.py`):

| Feature | Descripción |
|---|---|
| `indice_tendencia` | Posición del año fiscal en la serie (0, 1, 2, …). Captura la tendencia. |
| `precio_barril_usd_prom` | Precio promedio del petróleo crudo en el año fiscal (Fuente 2 / FMI PCPS). |

Target: `transitos_totales` (tránsitos del año fiscal).

---

## 3. Esquema de validación

Con 6 observaciones, un hold-out o una validación cruzada de varios folds no es
viable. Se usa **Leave-One-Out (LOO)**, la validación adecuada para muestras muy
pequeñas: se deja fuera un año fiscal, se entrena con los otros 5 y se predice el
año excluido; se repite para los 6 años. Las métricas (MAE, RMSE, MAPE, R²) se
calculan sobre esas 6 predicciones. **El modelo ganador se selecciona por el
menor MAPE de LOO.**

---

## 4. Modelos comparados

| Modelo | Rol |
|---|---|
| **Media histórica** | Baseline: predice el promedio (sin aprendizaje). |
| **Tendencia lineal** | Regresión lineal: transitos ~ índice de tiempo. |
| **Tendencia + precio** | Regresión lineal: transitos ~ índice de tiempo + precio del crudo. |

Implementación en `src/entrenamiento.py` (scikit-learn: `DummyRegressor`, `LinearRegression`).

---

## 5. Resultados

En validación Leave-One-Out, la **media histórica** obtiene el menor MAPE
(≈ 6.5%). Con solo 6 años y la fuerte caída de la sequía (FY2024, −16% frente a
FY2023), la serie **no muestra una tendencia lineal clara** (correlación
tránsitos–año débil y no significativa, según Persona 3), por lo que los modelos
de tendencia no superan a un promedio. Es un resultado honesto y esperable dada
la escasez de datos.

La tabla completa y comparativa se guarda en `output/metricas_modelos.csv`; el
resumen en `output/resumen_entrenamiento.json`.

---

## 6. Pronóstico

Se reentrena el modelo ganador con **toda** la serie y se proyectan los próximos
años fiscales (**FY2026–FY2027**). El precio del crudo se proyecta plano (último
valor observado). Salida en `output/predicciones_2026.csv`, lista para el
dashboard de Persona 5.

---

## 7. Limitaciones

1. **Serie muy corta:** 6 años fiscales. Cualquier métrica tiene alta
   incertidumbre; por eso se prioriza un modelo simple y la validación LOO.
2. **Granularidad anual:** la ACP no publica el desglose por segmento a nivel
   mensual, así que no es posible modelar estacionalidad intra-anual.
3. **Exógeno de precio plano** en el pronóstico (supuesto conservador).
4. **Sin tendencia lineal fuerte:** que gane el promedio refleja la realidad de
   los datos, no un fallo del pipeline. Al añadir más años fiscales (nuevos
   informes anuales), el modelo se re-evalúa automáticamente.

---

## 8. Reproducibilidad

```bash
python persona4_modelo/src/run_pipeline.py
```

Todos los artefactos (modelo serializado, métricas, predicciones, figuras) se
regeneran de forma determinista.
