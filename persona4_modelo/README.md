# Persona 4 — Modelo Predictivo (ML)

**Grupo 8 — Análisis de Datos del Canal de Panamá**
Segundo Parcial · Pipeline + Visualización

Este módulo cubre la **fase de modelado**: combina los tránsitos oficiales por
segmento de Persona 1 con el precio del crudo de Persona 2 y entrena un modelo de
Machine Learning para **predecir el volumen de tránsitos** del Canal de Panamá,
generando el pronóstico FY2026 para el dashboard de Persona 5.

> **Decisión clave de diseño:** la ACP publica por **año fiscal**, así que la serie
> de totales anuales tiene solo 6 puntos — insuficiente para que cualquier modelo
> aprenda. En lugar de eso se modela el panel **segmento × año fiscal**, que da
> **60 observaciones reales** (10 segmentos × 6 años) **sin inventar ni interpolar
> ningún dato**, y el total anual se obtiene sumando los segmentos.
> Ver [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) §1.

---

## Estructura

```
persona4_modelo/
├── src/
│   ├── preparacion_datos.py   # Panel segmento × año fiscal + features
│   ├── entrenamiento.py       # Leave-One-Year-Out, compara 4 modelos, serializa el ganador
│   ├── prediccion.py          # Pronóstico FY2026 por segmento + total
│   ├── visualizaciones.py     # 5 figuras PNG para el dashboard
│   └── run_pipeline.py        # Orquestador (corre los 3 módulos en orden)
├── data/
│   ├── raw/                   # (reservado)
│   └── processed/             # dataset_modelo.csv (panel modelable)
├── output/                    # Métricas, predicciones, importancia de features
├── figures/                   # 5 PNG de evaluación y pronóstico
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

- **Persona 1** (obligatoria): provee `acp_transitos_por_segmento_af.csv`, el panel
  de tránsitos oficiales por segmento de mercado.
- **Persona 2** (obligatoria): provee `dataset_unificado.csv` con el precio
  promedio del crudo por año fiscal.
- **Persona 3**: las definiciones de régimen (sequía FY2024 / recuperación FY2025)
  provienen de su análisis.

---

## Resultados

Validación **Leave-One-Year-Out** sobre 60 observaciones (10 segmentos × 6 años):

| Modelo | MAE ↓ | R² ↑ | MAPE (total anual) |
|---|---:|---:|---:|
| Media histórica (baseline) | 874.7 | −0.004 | 6.53 % |
| Ridge | 231.6 | +0.899 | 5.85 % |
| Gradient Boosting | 192.3 | +0.912 | 5.97 % |
| **Random Forest (ganador)** | **181.2** | **+0.921** | 6.22 % |

> **El modelo aprende de verdad:** el MAE cae **79.3 %** frente al baseline sin
> aprendizaje y el R² pasa de ≈0 a **+0.921**, en una validación donde el modelo
> nunca ve el año que predice.

**Pronóstico FY2026: 13,361 tránsitos totales** (desglose por segmento en
`output/predicciones_2026_por_segmento.csv`).

Los matices metodológicos —por qué se selecciona por MAE y no por MAPE, y por qué
el baseline parece competitivo en el total anual sin serlo— están documentados en
[`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) §4 y §5.

---

## Entregables para Persona 5 (dashboard)

### Predicciones en `output/`

| Archivo | Contenido |
|---|---|
| `predicciones_2026.csv` | Pronóstico del total anual (`anio_fiscal, transitos_predichos`) |
| `predicciones_2026_por_segmento.csv` | Pronóstico FY2026 desglosado por segmento |
| `predicciones_test.csv` | Total anual real vs predicho en LOYO (validación visual) |
| `predicciones_test_por_segmento.csv` | Real vs predicho por segmento y año |
| `metricas_modelos.csv` | Tabla comparativa de los 4 modelos (LOYO) |
| `importancia_features.csv` | Importancia de features del modelo ganador |
| `resumen_entrenamiento.json` | Resumen completo (modelo ganador + todas las métricas) |

### Modelo en `models/`

| Archivo | Contenido |
|---|---|
| `modelo_transitos.pkl` | Modelo ganador serializado (`{modelo, features, nombre}`) |

### Figuras en `figures/`

| Archivo | Uso sugerido en dashboard |
|---|---|
| `01_comparativa_modelos.png` | Sección "Modelo" · ranking de error (baseline destacado) |
| `02_ajuste_loo.png` | Validación: total anual real vs predicho (LOYO) |
| `03_importancia_features.png` | Importancia de features del modelo ganador |
| `04_pronostico_anual.png` | **Tarjeta principal**: histórico + pronóstico FY2026 |
| `05_ajuste_por_segmento.png` | Dispersión real vs predicho por segmento |

---

## Metodología detallada

Ver `docs/METODOLOGIA.md`.
