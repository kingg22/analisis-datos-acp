# Persona 4 — Modelo Predictivo (ML)

**Grupo 8 — Análisis de Datos del Canal de Panamá**
Segundo Parcial · Pipeline + Visualización

Este módulo cubre la **fase de modelado**: consume el dataset unificado de
Persona 2 y entrena un modelo para **predecir el volumen anual de tránsitos** del
Canal de Panamá, generando un pronóstico de los próximos años fiscales para el
dashboard de Persona 5.

> **Nota importante sobre los datos:** la ACP publica el desglose por segmento a
> nivel **anual** (año fiscal), por lo que la serie tiene pocos puntos (FY2020–
> FY2025). Con tan pocos datos, el modelo apropiado es **simple e interpretable**
> (tendencia lineal + precio del crudo), validado con **Leave-One-Out** — no un
> ensemble de ML, que requeriría muchas más observaciones.

---

## Estructura

```
persona4_modelo/
├── src/
│   ├── preparacion_datos.py   # Carga + features (índice de tendencia, precio del crudo)
│   ├── entrenamiento.py       # Leave-One-Out, compara 3 modelos, serializa el ganador
│   ├── prediccion.py          # Pronóstico de los próximos años fiscales
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

1. `entrenamiento.py` — construye features, evalúa con **Leave-One-Out**, compara
   3 modelos (media histórica, tendencia lineal, tendencia + precio), selecciona
   el de menor MAPE y lo reentrena con toda la serie.
2. `prediccion.py` — pronóstico de los próximos años fiscales (FY2026–FY2027).
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
- **Persona 3**: las definiciones de régimen (sequía FY2024 / recuperación FY2025)
  provienen de su análisis.

---

## Resultados

| Modelo ganador | MAPE (Leave-One-Out) |
|---|---:|
| **Media histórica** | **~6.5%** |

> Con solo 6 años fiscales y la fuerte caída de la sequía (FY2024), un promedio
> resulta más robusto que los modelos de tendencia en validación Leave-One-Out.
> Es un resultado honesto: la serie anual no muestra una tendencia lineal clara.

---

## Entregables para Persona 5 (dashboard)

### Predicciones en `output/`

| Archivo | Contenido |
|---|---|
| `predicciones_2026.csv` | Pronóstico anual (`anio_fiscal, transitos_predichos`) |
| `predicciones_test.csv` | Reales vs predichos en Leave-One-Out (validación visual) |
| `metricas_modelos.csv` | Tabla comparativa de los 3 modelos (LOO) |
| `importancia_features.csv` | Coeficientes del modelo ganador (si es lineal) |
| `resumen_entrenamiento.json` | Resumen completo (modelo ganador + todas las métricas) |

### Modelo en `models/`

| Archivo | Contenido |
|---|---|
| `modelo_transitos.pkl` | Modelo ganador serializado (`{modelo, features, nombre}`) |

### Figuras en `figures/`

| Archivo | Uso sugerido en dashboard |
|---|---|
| `01_comparativa_modelos.png` | Sección "Modelo" · ranking de error (LOO) |
| `02_ajuste_loo.png` | Validación: reales vs predichos (Leave-One-Out) |
| `03_importancia_features.png` | Coeficientes del modelo (si aplica) |
| `04_pronostico_anual.png` | **Tarjeta principal**: histórico + pronóstico anual |

---

## Metodología detallada

Ver `docs/METODOLOGIA.md`.
