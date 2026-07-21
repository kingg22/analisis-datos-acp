# Hallazgos del Análisis Exploratorio — Canal de Panamá

**Responsable:** Persona 3
**Fuente primaria:** `persona1_ingesta/data/processed/canal_limpio.csv` (datos oficiales ACP, modo `oficial`)
**Fuente secundaria:** `persona3_analisis/data/raw/fuente2_combustibles.csv` (precio del crudo, FMI PCPS, promedio por año fiscal)
**Período:** años fiscales **FY2020–FY2025** (6 años, 10 segmentos, 60 observaciones)
**Generado por:** `python persona3_analisis/src/run_pipeline.py`

> **Granularidad:** la ACP publica el desglose por segmento a nivel **anual** (año
> fiscal, oct–sep). Todo el análisis es anual; no hay estacionalidad mensual.

---

## 1. Resumen ejecutivo

- **Volumen total del período (FY2020–FY2025):** 79,674 tránsitos.
- **Tránsitos por año fiscal (todos los segmentos, cifras oficiales ACP):**

  | Año fiscal | Tránsitos | Variación interanual |
  |---|---:|---:|
  | FY2020 | 13,369 | — |
  | FY2021 | 13,342 | −0.2% |
  | FY2022 | 14,239 | +6.7% |
  | FY2023 | 14,080 | −1.1% |
  | FY2024 | 11,240 | **−20.2%** (sequía) |
  | FY2025 | 13,404 | **+19.3%** (recuperación) |

- La serie **no muestra una tendencia lineal clara**: sube hasta FY2022, cae con
  la sequía (FY2024) y se recupera en FY2025. CAGR FY2020–FY2025 ≈ 0% y la
  correlación tránsitos–año no es significativa (p ≈ 0.55).

---

## 2. Ranking de segmentos por tránsitos

| # | Segmento | Tránsitos (6 años) | Promedio anual | Participación |
|---|---|---:|---:|---:|
| 1 | Portacontenedores | 16,428 | 2,738 | 20.6% |
| 2 | Tanqueros_quimiqueros | 15,901 | 2,650 | 20.0% |
| 3 | Graneles_secos | 14,869 | 2,478 | 18.7% |
| 4 | Gas_licuado_GLP | 9,452 | 1,575 | 11.9% |
| 5 | Otros | 9,159 | 1,527 | 11.5% |
| 6 | Vehiculos_RoRo | 4,668 | 778 | 5.9% |
| 7 | Carga_refrigerada | 3,273 | 546 | 4.1% |
| 8 | Carga_general | 3,049 | 508 | 3.8% |
| 9 | Gas_natural_GNL | 1,832 | 305 | 2.3% |
| 10 | Pasajeros | 1,043 | 174 | 1.3% |

**Lectura:** los tres primeros segmentos (Portacontenedores, Tanqueros/quimiqueros,
Graneles secos) concentran **~59%** de los tránsitos: dependencia del comercio
contenerizado, de líquidos a granel y de graneles secos.

---

## 3. Impacto de la sequía (FY2024) y recuperación (FY2025)

Comparativa por segmento: baseline = promedio FY2020–FY2023; sequía = FY2024;
recuperación = FY2025.

| Segmento | Baseline | Sequía (FY2024) | Var % | Recuperación (FY2025) | Var % |
|---|---:|---:|---:|---:|---:|
| Graneles_secos | 2,840 | 1,278 | **−55.0%** | 2,230 | −21.5% |
| Carga_general | 575 | 287 | **−50.1%** | 463 | −19.4% |
| Gas_natural_GNL | 414 | 115 | **−72.2%** | 61 | −85.3% |
| Carga_refrigerada | 580 | 436 | **−24.9%** | 516 | −11.1% |
| Tanqueros_quimiqueros | 2,752 | 2,230 | **−19.0%** | 2,662 | −3.3% |
| Portacontenedores | 2,691 | 2,773 | +3.1% | 2,893 | +7.5% |
| Gas_licuado_GLP | 1,522 | 1,561 | +2.6% | 1,805 | +18.6% |
| Vehiculos_RoRo | 754 | 783 | +3.9% | 871 | +15.6% |
| Otros | 1,475 | 1,572 | +6.6% | 1,689 | +14.5% |
| Pasajeros | 156 | 205 | +31.4% | 214 | +37.2% |

**Lecturas clave:**
- La sequía golpeó sobre todo a **graneleros (−55%)** y **carga general (−50%)**:
  buques sensibles a las restricciones de calado y a los peajes.
- El **gas natural (GNL)** es el segmento en mayor caída estructural (FY2024 y
  FY2025 muy por debajo del baseline), por cambios en los patrones de comercio
  energético más que por la sequía.
- **Portacontenedores, GLP y vehículos** resistieron o crecieron: prioridad de
  slots de reserva para buques de alto valor.

---

## 4. Tendencia de largo plazo

- **CAGR FY2020–FY2025 ≈ 0%** (la serie termina cerca de donde empezó tras la
  caída y recuperación).
- **Correlación Pearson(tránsitos, año) = −0.31 (p ≈ 0.55):** no significativa;
  con 6 puntos y el shock de la sequía, no hay una tendencia lineal robusta.
- La dinámica relevante es de **shock y recuperación** (sequía FY2024 → rebote
  FY2025), no de crecimiento sostenido.

---

## 5. Relación con la segunda fuente (precio del crudo)

Correlaciones sobre el dataset unificado anual por segmento:

| Variable | Correlación con `transitos` |
|---|---:|
| `precio_barril_usd_prom` | débil |
| `peajes_usd` | **~1.0** (por construcción) |
| `toneladas_cp_suez` | **~1.0** (por construcción) |

> La correlación entre tránsitos y peajes/toneladas es ~1 porque ambos se
> prorratean a partir de los tránsitos. El precio del crudo tiene relación débil
> a esta granularidad anual.

---

## 6. Recomendaciones para Persona 4 (modelo predictivo)

1. **Serie corta (6 años):** usar modelos simples (tendencia lineal / media) y
   validación **Leave-One-Out**; evitar ensembles de ML (sobreajuste inmediato).
2. **Exógeno disponible:** `precio_barril_usd_prom` (promedio anual del crudo).
3. **Sin estacionalidad modelable:** la fuente es anual; la señal es la variación
   año a año (shock de la sequía y recuperación).

## 7. Recomendaciones para Persona 5 (dashboard)

Figuras listas en `persona3_analisis/figures/` (7 PNG):

| Archivo | Uso sugerido en dashboard |
|---|---|
| `01_serie_anual.png` | Tarjeta principal con la serie anual |
| `02_composicion_por_segmento.png` | Stacked-bar de composición |
| `03_ranking_segmentos.png` | Ranking lateral |
| `04_comparativa_periodos.png` | Comparativa baseline/sequía/recuperación |
| `05_heatmap_correlacion.png` | Sección "Drivers macro" |
| `06_tendencia_anual.png` | Tarjeta de tendencia + CAGR |
| `07_precio_vs_transitos.png` | Sección "Segunda fuente" |

---

## 8. Limitaciones

1. **Granularidad anual:** la ACP no publica el desglose por segmento a nivel
   mensual; por eso no hay análisis de estacionalidad intra-anual.
2. **`calado_promedio_pies`** es un valor nominal de referencia por segmento, no
   publicado por la ACP (ver `persona1_ingesta/docs/FUENTE_DATOS.md`).
3. **Serie corta:** 6 años fiscales; las métricas de tendencia tienen alta
   incertidumbre. Al publicarse nuevos informes anuales, re-ejecutar el pipeline.
