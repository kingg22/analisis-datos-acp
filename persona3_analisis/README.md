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
│   ├── analisis_tendencias.py # EDA anual, ranking, impacto macro, tendencia
│   ├── visualizaciones.py     # 7 figuras PNG listas para el dashboard
│   └── run_pipeline.py        # Orquestador (corre los 3 módulos en orden)
├── data/
│   ├── raw/                   # Segunda fuente (real o generada como muestra)
│   └── processed/             # CSVs unificados + agregados para dashboard
├── output/                    # Tablas, JSONs y componentes del EDA
├── figures/                   # 7 PNG de visualización
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

1. `preprocesamiento.py` — carga `canal_limpio.csv` (anual) de Persona 1, une la
   segunda fuente (precio del crudo por año fiscal) y produce `canal_unificado.csv`
   + 3 CSV agregados.
2. `analisis_tendencias.py` — EDA anual: stats descriptivas, ranking, impacto
   sequía/recuperación, tendencia anual con CAGR y 5 insights clave en
   `output/insights.json`.
3. `visualizaciones.py` — 7 figuras PNG en `figures/`.

### Módulos individuales

```bash
python persona3_analisis/src/preprocesamiento.py
python persona3_analisis/src/analisis_tendencias.py
python persona3_analisis/src/visualizaciones.py
```

---

## Dependencia de otras personas

- **Persona 1** (obligatoria): ejecuta primero
  `python persona1_ingesta/src/ingesta_canal.py --modo oficial` para producir
  `canal_limpio.csv`.
- **Persona 2** (opcional, no bloquea): si coloca su CSV en
  `persona3_analisis/data/raw/fuente2_combustibles.csv` con columnas
  `anio_fiscal, precio_barril_usd_prom`, el preprocesamiento lo usará como
  fuente real. Si no existe, se genera una muestra anual automáticamente.

---

## Entregables para Persona 5 (dashboard)

### CSVs en `data/processed/`

| Archivo | Contenido |
|---|---|
| `canal_unificado.csv` | 60 filas (año fiscal × segmento) con features derivados |
| `agregado_serie_total.csv` | Serie anual total (6 años fiscales) |
| `agregado_por_segmento_anio.csv` | Composición por segmento y año fiscal |
| `agregado_por_periodo.csv` | Sequía / baseline / recuperación |

### Tablas y JSONs en `output/`

| Archivo | Contenido |
|---|---|
| `insights.json` | 5 hallazgos en formato `{id, titulo, detalle}` para LLM |
| `ranking_segmentos.csv` | Tabla de ranking |
| `impacto_sequia_recuperacion.csv` | Comparativa de períodos |
| `tendencia_anual.csv` | Tránsitos por año fiscal + CAGR |
| `stats_por_segmento.csv` | Stats descriptivas por segmento |
| `stats_totales.csv` | Stats descriptivas totales |

### Figuras en `figures/`

| Archivo | Descripción |
|---|---|
| `01_serie_anual.png` | Serie anual con sequía (FY2024) y recuperación (FY2025) resaltadas |
| `02_composicion_por_segmento.png` | % apilada por año fiscal y segmento |
| `03_ranking_segmentos.png` | Barras horizontales de ranking |
| `04_comparativa_periodos.png` | Sequía vs baseline vs recuperación |
| `05_heatmap_correlacion.png` | Heatmap de correlación de variables numéricas |
| `06_tendencia_anual.png` | Tendencia lineal sobre tránsitos anuales |
| `07_precio_vs_transitos.png` | Eje dual: tránsitos vs precio del crudo |

---

## Hallazgos detallados

Ver `docs/HALLAZGOS.md`.
