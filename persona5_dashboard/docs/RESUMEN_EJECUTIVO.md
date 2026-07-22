# Resumen Ejecutivo — Análisis de Datos del Canal de Panamá

**Grupo 8 — Segundo Parcial · Pipeline + Visualización**

---

## Panorama General

El análisis cubre los años fiscales **FY2020 a FY2025** del Canal de Panamá, con las siguientes cifras consolidadas:

| Indicador | Valor |
|---|---|
| Tránsitos totales | **79,674** |
| Peajes acumulados | **USD 19,194 millones** |
| Años fiscales analizados | 6 (FY2020–FY2025) |
| Segmentos de buques | 10 |
| Observaciones del modelo | 60 (10 segmentos × 6 años) |

---

## Hallazgos Principales

### Segmento líder
Los **portacontenedores** dominan con el **20.6%** de los tránsitos totales del período y un promedio anual de **2,738 tránsitos**.

### Impacto de la sequía (FY2023–FY2024)
La sequía afectó severamente a varios segmentos:

- **Gas natural (GNL):** cayó **72.2%** frente al baseline (de 414 a 115 tránsitos anuales)
- **Graneles secos:** cayeron **55%** (de 2,840 a 1,278)
- **Carga general:** cayó **50%** (de 575 a 287)
- **Tanqueros / Quimiqueros:** cayeron **19%**

### Recuperación (FY2025)
- **Pasajeros:** supera el baseline en **37.2%** (214 vs. 156)
- **Gas licuado (GLP):** subió **18.6%** vs. baseline
- **Portacontenedores:** mantiene crecimiento sostenido

### Tendencia de largo plazo
CAGR FY2020–FY2025: **0.05% anual**. Correlación Pearson(tránsitos, año) = -0.314 (p=0.5451), tendencia no significativa estadísticamente.

---

## Modelo Predictivo

### Especificación
| Parámetro | Valor |
|---|---|
| **Modelo ganador** | Random Forest |
| **Validación** | Leave-One-Year-Out |
| **Granularidad** | Segmento × año fiscal (ACP) |
| **Observaciones** | 60 |
| **Variables** | Segmento, precio del crudo, sequía, año fiscal |

### Métricas (LOYO)

| Métrica | Random Forest | Baseline (Media Histórica) | Mejora |
|---|---|---|---|
| **R²** | +0.921 | -0.004 | **+0.925** |
| **MAE** | 181 tránsitos | 875 tránsitos | **-79.3%** |
| **MAPE (total anual)** | 6.22% | 6.53% | — |

### Comparativa de modelos evaluados

| Modelo | MAE | R² |
|---|---|---|
| Random Forest | **181** | **0.921** |
| Gradient Boosting | 192 | 0.912 |
| Ridge | 232 | 0.899 |
| Media Histórica (baseline) | 875 | -0.004 |

### Pronóstico FY2026

**Total estimado: 13,361 tránsitos**

| Segmento | Tránsitos Predichos |
|---|---|
| Portacontenedores | 2,807 |
| Tanqueros / Quimiqueros | 2,649 |
| Graneles secos | 2,421 |
| Gas licuado (GLP) | 1,708 |
| Otros | 1,566 |
| Vehículos RoRo | 840 |
| Carga refrigerada | 522 |
| Carga general | 482 |
| Pasajeros | 174 |
| Gas natural (GNL) | 192 |

**Supuesto del modelo:** escenario base con precio del crudo a **USD 71.03/barril** y sin sequía.

---

## Dashboard (Streamlit)

El dashboard interactivo incluye 5 páginas:
1. **Inicio** — KPIs, serie temporal, insights
2. **Tendencias** — EDA, estacionalidad, descomposición
3. **Modelo Predictivo** — Pronóstico 2026, métricas, features
4. **Mapas** — Ubicación del canal, rutas, distribución geográfica
5. **Resumen LLM** — Generación de reportes con IA (OpenAI / Claude / Offline)

---

## Power BI

Modelo estrella implementado con 4 tablas:
- `dim_segmento` (10 segmentos con categorías)
- `dim_tiempo` (6 años fiscales con períodos y precio del crudo)
- `fact_transitos` (60 registros: tránsitos, toneladas, peajes)
- `fact_predicciones` (10 registros: pronóstico FY2026 por segmento)

Visual Q&A configurado con preguntas demo funcionales en lenguaje natural.

---

**Generado por:** Persona 5 — Grupo 8  
**Fecha:** Julio 2026
