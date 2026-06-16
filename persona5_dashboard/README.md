# Persona 5 — Dashboard + Resúmenes LLM

**Grupo 8 — Análisis de Datos del Canal de Panamá**
Segundo Parcial · Pipeline + Visualización

Este módulo construye el **dashboard interactivo** del proyecto, integrando
visualizaciones de Persona 3 y predicciones de Persona 4, además de generar
**resúmenes ejecutivos con IA**.

---

## Estructura

```
persona5_dashboard/
├── src/
│   ├── app.py                        # Página principal del dashboard
│   ├── pages/
│   │   ├── 01_tendencias.py          # Análisis de tendencias (EDA visual)
│   │   ├── 02_modelo_predictivo.py   # Resultados del modelo ML
│   │   └── 03_resumen_llm.py         # Generación de resúmenes con IA
│   └── utils/
│       └── data_loader.py            # Funciones de carga de datos
├── static/                           # Assets estáticos
├── docs/                             # Documentación
├── requirements.txt                  # Dependencias del dashboard
└── README.md
```

---

## Dependencias

```bash
# Desde la raíz del proyecto
uv sync

# O directamente
pip install -r persona5_dashboard/requirements.txt
```

**Paquetes requeridos:** `streamlit`, `plotly`, `openai`, `anthropic`, `pandas`

---

## Ejecución

### Dashboard completo

```bash
# Desde la raíz del proyecto
cd /home/xhenno/dev/analisis-datos-acp
streamlit run persona5_dashboard/src/app.py
```

El dashboard se abrirá en `http://localhost:8501`.

### Páginas individuales

```bash
streamlit run persona5_dashboard/src/pages/01_tendencias.py
streamlit run persona5_dashboard/src/pages/02_modelo_predictivo.py
streamlit run persona5_dashboard/src/pages/03_resumen_llm.py
```

---

## Páginas del Dashboard

### 🏠 Inicio (app.py)
- KPIs principales: total tránsitos, promedio mensual, mes pico, modelo ML
- Serie temporal histórica + pronóstico 2026
- Insights clave del análisis
- Comparativa de períodos (sequía vs baseline vs recuperación)

### 📈 Tendencias (01_tendencias.py)
- Evolución mensual de tránsitos
- Tendencia anual con barras
- Distribución por segmento (ranking + pie chart)
- Evolución temporal por segmento
- Estacionalidad por mes calendario
- Heatmap fase fiscal × segmento
- Descomposición de la serie (observado/tendencia/estacional/residuo)
- Figuras EDA de Persona 3

### 🤖 Modelo Predictivo (02_modelo_predictivo.py)
- Resumen del modelo ganador (Gradient Boosting, MAPE 6.94%)
- Pronóstico interactivo 2026 con banda de confianza
- Comparativa de modelos evaluados
- Validación: reales vs predichos en hold-out
- Importancia de features
- Figuras del modelo de Persona 4

### 🧠 Resumen LLM (03_resumen_llm.py)
- Generación de resúmenes ejecutivos con IA
- Soporte para OpenAI (GPT) y Anthropic (Claude)
- Plantillas predefinidas: Ejecutivo, Tendencias, ML, Pronóstico, Dirección
- Exportación a Markdown
- Modo offline: genera resumen basado en reglas

---

## Dependencias de Otras Personas

- **Persona 1** (obligatoria): `canal_serie_mensual.csv`, `canal_limpio.csv`
- **Persona 2** (recomendada): `dataset_unificado.csv`
- **Persona 3** (obligatoria): CSVs en `data/processed/`, `output/`, `figures/`
- **Persona 4** (obligatoria): CSVs en `output/`, modelo serializado

---

## Configuración de IA

Para usar la generación de resúmenes con LLM:

1. **OpenAI:** Obtener API key en https://platform.openai.com
2. **Anthropic:** Obtener API key en https://console.anthropic.com

La API key se configura en la barra lateral del dashboard (nunca se almacena).

Si no se configura API, el dashboard genera resúmenes con datos disponibles.

---

## Integración

El dashboard está diseñado para consumir los archivos producidos por las demás
personas. Las rutas se resuelven automáticamente desde la raíz del proyecto.

**Estructura esperada de archivos:**

```
persona1_ingesta/data/processed/
persona2_pipeline/data/processed/
persona3_analisis/data/processed/
persona3_analisis/output/
persona3_analisis/figures/
persona4_modelo/output/
persona4_modelo/figures/
```

---

## Notas Técnicas

- **Streamlit** como framework principal (multi-page app)
- **Plotly** para visualizaciones interactivas
- Cache de datos con `@st.cache_data(ttl=300)` (5 min)
- CSS customizado para métricas con gradiente
- Resolución automática de rutas relativas al proyecto
