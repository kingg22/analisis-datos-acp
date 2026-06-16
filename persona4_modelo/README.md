# Persona 4 — Modelo Predictivo (ML)

**Grupo 8 — Análisis de Datos del Canal de Panamá**
Segundo Parcial · Pipeline + Visualización

Este módulo cubre la **fase de modelado**: consume el dataset unificado de
Persona 2 y entrena un modelo de Machine Learning para **predecir el volumen
mensual de tránsitos** del Canal de Panamá, generando además un pronóstico a
12 meses listo para el dashboard de Persona 5.

---

## Estructura

```
persona4_modelo/
├── src/
│   ├── preparacion_datos.py   # Carga + ingeniería de features (lags, régimen, estacionalidad)
│   ├── entrenamiento.py       # CV temporal + hold-out, compara 4 modelos, serializa el ganador
│   ├── prediccion.py          # Pronóstico recursivo a 12 meses (2026)
│   ├── visualizaciones.py     # 4 figuras PNG para el dashboard
│   └── run_pipeline.py        # Orquestador (corre los 3 módulos en orden)
├── data/
│   ├── raw/                   # (reservado)
│   └── processed/             # dataset_modelo.csv (matriz de features)
├── output/                    # Métricas, predicciones, importancia de features
├── figures/                   # 4 PNG de evaluación y pronóstico
├── models/                    # modelo_transitos.pkl (modelo ganador serializado)
├── docs/
│   └── METODOLOGIA.md         # Metodología, métricas y limitaciones
├── requirements.txt
└── README.md
```

---

## Dependencias

Gestionadas desde la raíz con `uv` (o `pip`):

```bash
uv sync                      # desde la raíz
# o
pip install -r requirements.txt
```

Paquetes: `pandas`, `numpy`, `scikit-learn`, `matplotlib`.

---

## Ejecución

### Pipeline completo (recomendado)

```bash
python persona4_modelo/src/run_pipeline.py
```

El orquestador corre en secuencia:

1. `entrenamiento.py` — ingeniería de features, **validación cruzada temporal**
   (5 folds, ventana expansiva) + **hold-out** 2024-10→2025-12, compara 4
   modelos, selecciona el de menor MAPE de CV y lo reentrena con toda la serie.
2. `prediccion.py` — pronóstico recursivo de 12 meses (2026).
3. `visualizaciones.py` — 4 figuras PNG.

### Módulos individuales

```bash
python persona4_modelo/src/preparacion_datos.py
python persona4_modelo/src/entrenamiento.py
python persona4_modelo/src/prediccion.py
python persona4_modelo/src/visualizaciones.py
```

---

## Dependencia de otras personas

- **Persona 2** (recomendada): provee `persona2_pipeline/data/processed/dataset_unificado.csv`.
  Si no existe, el módulo recae automáticamente en el agregado de Persona 3
  (`agregado_serie_total.csv`, sin precio) para no bloquear el desarrollo.
- **Persona 3**: las definiciones de régimen (sequía/recuperación) y la
  recomendación de hold-out provienen de `HALLAZGOS.md`.

---

## Resultados (modo muestra)

| | Modelo ganador | MAPE (CV temporal) | MAPE (hold-out 2025) |
|---|---|---:|---:|
| | **Gradient Boosting** | **6.94%** (±3.91) | 14.79% |

> El hold-out 2025 es una **prueba de estrés** ante el quiebre de régimen
> (año récord ausente del entrenamiento) — ver `docs/METODOLOGIA.md §3.2`.

Predictor dominante: `periodo_sequia` (57.9% de importancia).

---

## Entregables para Persona 5 (dashboard)

### Predicciones en `output/`

| Archivo | Contenido |
|---|---|
| `predicciones_2026.csv` | Pronóstico mensual 2026 (`fecha, transitos_predichos, anio, mes`) |
| `predicciones_test.csv` | Reales vs predichos en el hold-out (para validación visual) |
| `metricas_modelos.csv` | Tabla comparativa de los 4 modelos (CV + hold-out) |
| `importancia_features.csv` | Peso de cada feature en el modelo ganador |
| `resumen_entrenamiento.json` | Resumen completo (modelo ganador + todas las métricas) |

### Modelo en `models/`

| Archivo | Contenido |
|---|---|
| `modelo_transitos.pkl` | Modelo ganador serializado (`{modelo, features, nombre}`) |

### Figuras en `figures/`

| Archivo | Uso sugerido en dashboard |
|---|---|
| `01_comparativa_modelos.png` | Sección "Modelo" · ranking de error |
| `02_ajuste_test.png` | Validación: reales vs predichos |
| `03_importancia_features.png` | "¿Qué impulsa la predicción?" |
| `04_pronostico_2026.png` | **Tarjeta principal**: histórico + pronóstico 12 meses |

---

## Metodología detallada

Ver `docs/METODOLOGIA.md`.
