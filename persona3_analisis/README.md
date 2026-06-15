# Persona 3 — Preprocesamiento y Análisis de Tendencias

**Grupo 8 — Análisis de Datos del Canal de Panamá**
Segundo Parcial · Pipeline + Visualización

Este módulo cubre la **tercera fase** del pipeline: recibe los datos limpios
de Persona 1, los une con una segunda fuente (cuando exista), ejecuta análisis
exploratorio (EDA) y produce visualizaciones + insights para el dashboard de
Persona 5.

---

## Estructura

```
persona3_analisis/
├── src/
│   ├── preprocesamiento.py    # Join, normalización, nulos, features derivados
│   ├── analisis_tendencias.py # EDA, descomposición, ranking, impacto macro
│   ├── visualizaciones.py     # 10 figuras PNG listas para el dashboard
│   └── run_pipeline.py        # Orquestador (corre los 3 módulos en orden)
├── data/
│   ├── raw/                   # Segunda fuente (real o generada como muestra)
│   └── processed/             # CSVs unificados + agregados para dashboard
├── output/                    # Tablas, JSONs y componentes del EDA
├── figures/                   # 10 PNG de visualización
├── docs/
│   └── HALLAZGOS.md           # Hallazgos del análisis exploratorio
└── README.md
```

---

## Dependencias

Gestionadas desde la raíz con `uv`:

```bash
uv sync
```

Paquetes requeridos (ver `pyproject.toml` raíz): `pandas`, `numpy`, `requests`,
`matplotlib`, `seaborn`, `scipy`.

---

## Ejecución

### Pipeline completo

```bash
# Desde la raíz del proyecto
python persona3_analisis/src/run_pipeline.py
```

El orquestador corre en secuencia:

1. `preprocesamiento.py` — carga `canal_limpio.csv` de Persona 1, intenta
   cargar la segunda fuente real; si no existe, genera una muestra de Brent
   proxy y la persiste. Normaliza, une y produce `canal_unificado.csv` +
   4 CSV agregados.
2. `analisis_tendencias.py` — EDA completo: stats descriptivas, ranking,
   impacto sequía/recuperación, estacionalidad, tendencia anual con CAGR,
   descomposición estacional y 6 insights clave en `output/insights.json`.
3. `visualizaciones.py` — 10 figuras PNG en `figures/`.

### Módulos individuales

```bash
python persona3_analisis/src/preprocesamiento.py
python persona3_analisis/src/analisis_tendencias.py
python persona3_analisis/src/visualizaciones.py
```

---

## Dependencia de otras personas

- **Persona 1** (obligatoria): ejecuta primero
  `python persona1_ingesta/src/ingesta_canal.py --modo muestra` para producir
  `canal_limpio.csv`.
- **Persona 2** (opcional, no bloquea): si coloca su CSV en
  `persona3_analisis/data/raw/fuente2_combustibles.csv` con columnas
  `fecha, anio, mes, precio_barril_usd`, el preprocesamiento lo usará como
  fuente real. Si no existe, se genera una muestra automáticamente.

---

## Entregables para Persona 5 (dashboard)

### CSVs en `data/processed/`

| Archivo | Contenido |
|---|---|
| `canal_unificado.csv` | 750 filas × ~14 columnas: dataset unificado con features |
| `agregado_serie_total.csv` | Serie mensual total (75 meses) |
| `agregado_por_segmento_anio.csv` | Composición por segmento y año |
| `agregado_por_fase_fiscal.csv` | Estacionalidad por fase fiscal ACP |
| `agregado_por_periodo.csv` | Sequía / baseline / recuperación |

### Tablas y JSONs en `output/`

| Archivo | Contenido |
|---|---|
| `insights.json` | 6 hallazgos en formato `{id, titulo, detalle}` para LLM |
| `ranking_segmentos.csv` | Tabla de ranking |
| `impacto_sequia_recuperacion.csv` | Comparativa de períodos |
| `tendencia_anual.csv` | Tránsitos anuales + CAGR |
| `descomposicion_serie.csv` | Componentes observado / tendencia / residuo |
| `componente_estacional.csv` | Estacionalidad por mes calendario |
| `estacionalidad_fase_fiscal.csv` | Estacionalidad por fase fiscal ACP |
| `stats_por_segmento.csv` | Stats descriptivas por segmento |
| `stats_totales.csv` | Stats descriptivas totales |

### Figuras en `figures/`

| Archivo | Descripción |
|---|---|
| `01_serie_mensual.png` | Serie mensual con sombreados (sequía/recuperación) |
| `02_descomposicion_estacional.png` | Observado / tendencia / estacionalidad / residuo |
| `03_subserie_estacional.png` | Subserie por mes calendario (un color por año) |
| `04_composicion_por_segmento.png` | % apilada por año y segmento |
| `05_ranking_segmentos.png` | Barras horizontales de ranking |
| `06_comparativa_periodos.png` | Sequía vs baseline vs recuperación |
| `07_heatmap_correlacion.png` | Heatmap de correlación de variables numéricas |
| `08_estacionalidad_fase_fiscal.png` | Heatmap fase fiscal × segmento |
| `09_tendencia_anual.png` | Tendencia lineal sobre tránsitos anuales |
| `10_precio_vs_transitos.png` | Eje dual: tránsitos vs Brent |

---

## Hallazgos detallados

Ver `docs/HALLAZGOS.md`.
