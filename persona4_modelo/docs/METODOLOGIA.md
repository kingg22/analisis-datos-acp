# Metodología del Modelo Predictivo — Canal de Panamá

**Responsable:** Persona 4
**Objetivo:** predecir el **volumen mensual de tránsitos totales** del Canal de Panamá.
**Fuente primaria:** `persona2_pipeline/data/processed/dataset_unificado.csv` (serie mensual de tránsitos + precio del barril, 75 meses: oct-2019 → dic-2025).
**Generado por:** `python persona4_modelo/src/run_pipeline.py`

---

## 1. Planteamiento

El problema es de **regresión sobre una serie de tiempo univariada** (tránsitos
mensuales), enriquecida con variables exógenas y de régimen. Se eligió un
enfoque de **regresión supervisada con features de ingeniería temporal** en
lugar de un modelo ARIMA puro porque permite incorporar de forma natural las
variables exógenas detectadas por Persona 3 (precio del barril, régimen de
sequía/recuperación) y comparar varios algoritmos bajo el mismo marco.

---

## 2. Ingeniería de features

A partir de la serie mensual se construyen 10 variables predictoras
(`src/preparacion_datos.py`):

| Feature | Tipo | Descripción |
|---|---|---|
| `mes_sin`, `mes_cos` | Calendario | Estacionalidad cíclica (seno/coseno del mes) |
| `indice_tendencia` | Calendario | Número de mes desde el inicio (captura la tendencia de largo plazo) |
| `periodo_sequia` | Régimen | 1 entre jun-2023 y may-2024 (sequía del Gatún) |
| `periodo_recuperacion` | Régimen | 1 desde 2025 (recuperación post-sequía) |
| `lag_1` | Autorregresivo | Tránsitos del mes anterior |
| `lag_12` | Autorregresivo | Tránsitos del mismo mes del año anterior |
| `media_movil_3` | Autorregresivo | Media móvil de los 3 meses previos |
| `precio_barril_usd` | Exógeno | Precio del petróleo crudo (Fuente 2 / FMI PCPS) |
| `precio_barril_usd_ma3` | Exógeno | Media móvil 3 meses del precio |

Los regímenes de sequía y recuperación replican exactamente las definiciones de
`persona3_analisis/docs/HALLAZGOS.md` (sección 3). Las primeras 12 filas se
descartan por no tener `lag_12` válido → **63 meses modelables**.

---

## 3. Esquema de validación

Series de tiempo cortas exigen validación que **respete el orden temporal**
(nunca entrenar con el futuro). Se usan dos esquemas complementarios:

### 3.1 Validación cruzada temporal (métrica primaria)

`TimeSeriesSplit` de scikit-learn con **5 folds de ventana expansiva**: cada
fold entrena con todo el pasado disponible y valida con el bloque siguiente.
Promediar el error sobre 5 cortes da una estimación mucho más estable que un
único hold-out. **El modelo ganador se selecciona por el menor MAPE de CV.**

### 3.2 Hold-out temporal (prueba de estrés)

- **Entrenamiento:** hasta 2024-09 (48 meses)
- **Prueba:** 2024-10 → 2025-12 (15 meses)

Este corte sigue la recomendación de Persona 3 (HALLAZGOS §7). Se reporta como
**prueba de estrés**: el período de prueba contiene el **quiebre de régimen de
2025** (año récord, +29.8% interanual) que está *ausente* del entrenamiento, por
lo que ningún modelo puede anticipar plenamente ese salto de nivel. Esto explica
el R² negativo en el hold-out y es una limitación documentada, no un error del
modelo (ver §6).

---

## 4. Modelos comparados

| Modelo | Rol |
|---|---|
| **Naive estacional** (t = t-12) | Baseline sin aprendizaje |
| **Regresión lineal** | Referencia interpretable |
| **Random Forest** | No lineal, robusto |
| **Gradient Boosting** | No lineal, suele liderar en datos tabulares |

Hiperparámetros en `src/entrenamiento.py` (`semilla=42` para reproducibilidad).

---

## 5. Resultados

### Validación cruzada temporal (métrica primaria)

| Modelo | MAPE CV | ± std | MAE CV |
|---|---:|---:|---:|
| **Gradient Boosting** ✅ | **6.94%** | 3.91 | 65.6 |
| Random Forest | 11.42% | 9.82 | 97.5 |
| Regresión lineal | 26.26% | 24.14 | 222.4 |

### Hold-out 2024-10 → 2025-12 (prueba de estrés)

| Modelo | MAPE | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| Regresión lineal | 13.26% | 153.1 | 166.5 | −0.99 |
| Random Forest | 14.04% | 163.1 | 179.7 | −1.31 |
| Gradient Boosting | 14.79% | 171.2 | 187.4 | −1.52 |
| Naive estacional | 23.66% | 269.3 | 300.1 | −5.45 |

**Modelo seleccionado: Gradient Boosting** (mejor MAPE en CV: 6.94%). Todos los
modelos de ML superan ampliamente al baseline naive estacional.

### Importancia de features (Gradient Boosting)

| Feature | Importancia |
|---|---:|
| `periodo_sequia` | 57.9% |
| `indice_tendencia` | 14.0% |
| `mes_sin` | 10.7% |
| `periodo_recuperacion` | 8.2% |
| `lag_1` | 5.4% |
| resto | < 2% c/u |

**Lectura:** el régimen de sequía es, con mucho, el predictor dominante —
coherente con el hallazgo de Persona 3 de que la sequía 2023–2024 fue el evento
que más distorsionó la serie. La tendencia y la estacionalidad mensual aportan
la siguiente capa de señal. El precio del barril tiene importancia marginal
(<2%), consistente con la correlación débil (−0.04) reportada por Persona 3.

---

## 6. Pronóstico 2026

Se reentrena el modelo ganador con **toda** la serie y se proyectan **12 meses**
(2026-01 → 2026-12) de forma **recursiva**: cada mes predicho alimenta los lags
del mes siguiente. El `lag_12` del horizonte usa los tránsitos reales de 2025.

- **Total proyectado 2026:** ≈ 13,565 tránsitos (en línea con los 13,961 de 2025).
- **Patrón:** pico en feb–abr (~1,180/mes), valle en ago–sep (~1,070/mes),
  reproduciendo la estacionalidad histórica.
- **Supuesto:** el precio del barril se proyecta plano (último valor observado),
  dado su bajo peso predictivo; refinar si Persona 2 provee un pronóstico de precio.

Salida en `output/predicciones_2026.csv`, lista para el dashboard de Persona 5.

---

## 7. Limitaciones

1. **Quiebre de régimen 2025 no extrapolable:** el hold-out muestra R² negativo
   porque el salto de nivel de 2025 es inédito en el entrenamiento. La CV
   (que sí ve recuperación en los folds tardíos) confirma que el modelo es
   sólido cuando el régimen está representado.
2. **Serie corta:** 63 meses modelables; las métricas tienen varianza alta
   (ver ± de la CV).
3. **Datos de muestra:** mientras Persona 1/2 operen en modo `muestra`, las
   cifras son indicativas. El pipeline es agnóstico a la fuente: al reemplazar
   por datos reales y re-ejecutar, las métricas se actualizan automáticamente.
4. **Exógeno de precio plano** en el pronóstico (supuesto conservador).

---

## 8. Reproducibilidad

```bash
python persona4_modelo/src/run_pipeline.py
```

Todos los artefactos (modelo serializado, métricas, predicciones, figuras) se
regeneran de forma determinista (`semilla=42`).
