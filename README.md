# Análisis de Datos del Canal de Panamá

**Grupo 8 — Segundo Parcial · Pipeline + Visualización**

Proyecto de análisis de datos del Canal de Panamá que incluye ingesta de datos,
preprocesamiento, modelo predictivo y dashboard interactivo.

---

## Objetivo

Analizar las tendencias de tránsitos del Canal de Panamá (2019-2025), identificar
patrones estacionales, evaluar el impacto de la sequía 2023-2024 y generar
predicciones para 2026.

---

## Estructura del Proyecto

```
analisis-datos-acp/
├── persona1_ingesta/          # Ingesta de datos del Canal (Fuente 1)
├── persona2_pipeline/         # Segunda fuente + pipeline de unión
├── persona3_analisis/         # Preprocesamiento + análisis exploratorio
├── persona4_modelo/           # Modelo predictivo (ML)
├── persona5_dashboard/        # Dashboard interactivo (Streamlit)
├── pyproject.toml             # Dependencias del proyecto
└── README.md                  # Este archivo
```

---

## Roles

| Persona | Responsabilidad | Estado |
|---|---|---|
| **Persona 1** | Ingesta de datos del Canal de Panamá | ✅ |
| **Persona 2** | Segunda fuente + pipeline de unión | ✅ |
| **Persona 3** | Preprocesamiento + análisis de tendencias | ✅ |
| **Persona 4** | Modelo predictivo (Gradient Boosting) | ✅ |
| **Persona 5** | Dashboard Streamlit + resúmenes LLM | ✅ |

---

## Fuentes de Datos

1. **Canal de Panamá (ACP)** — Estadísticas de tránsito, tonelaje, peajes
2. **Combustibles (Brent)** — Precios internacionales de petróleo

---

## Tecnologías

- **Python 3.13+**
- **pandas** — Manipulación de datos
- **scikit-learn** — Machine Learning (Gradient Boosting)
- **Streamlit** — Dashboard interactivo
- **Plotly** — Visualizaciones interactivas y mapas
- **OpenAI / Anthropic** — Resúmenes ejecutivos con IA

---

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/kingg22/analisis-datos-acp.git
cd analisis-datos-acp

# Instalar dependencias con uv
uv sync

# O con pip
pip install -r persona5_dashboard/requirements.txt
```

---

## Ejecución

### Dashboard (recomendado)

```bash
streamlit run persona5_dashboard/src/app.py
```

Se abrirá en `http://localhost:8501`.

### Pipelines individuales

```bash
# Persona 1 — Ingesta
python persona1_ingesta/src/ingesta_canal.py

# Persona 2 — Pipeline
python persona2_pipeline/src/pipeline.py

# Persona 3 — Análisis
python persona3_analisis/src/run_pipeline.py

# Persona 4 — Modelo ML
python persona4_modelo/src/run_pipeline.py
```

---

## Resultados Clave

- **72,543 tránsitos** analizados (oct 2019 – dic 2025)
- **Segmento líder:** Portacontenedores (24.4%)
- **Impacto sequía:** Pasajeros cayó 28.5%
- **Modelo:** Gradient Boosting con MAPE 6.94% (CV)
- **Pronóstico 2026:** Recuperación esperada con 1,071-1,179 tránsitos/mes

---

## Dashboard

El dashboard incluye 5 páginas:

1. **Inicio** — KPIs, serie temporal, insights
2. **Tendencias** — EDA, estacionalidad, descomposición
3. **Modelo Predictivo** — Pronóstico 2026, métricas, features
4. **Mapas** — Ubicación del canal, rutas, distribución geográfica
5. **Resumen LLM** — Generación de reportes con IA

---

## Documentación

Cada módulo incluye su propio `README.md` con documentación detallada:

- [Persona 1](persona1_ingesta/README.md)
- [Persona 2](persona2_pipeline/README.md)
- [Persona 3](persona3_analisis/README.md)
- [Persona 4](persona4_modelo/README.md)
- [Persona 5](persona5_dashboard/README.md)

---

*Grupo 8 — Análisis de Datos del Canal de Panamá · Segundo Parcial 2026*
