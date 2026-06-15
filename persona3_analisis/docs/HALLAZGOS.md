# Hallazgos del Análisis Exploratorio — Canal de Panamá

**Responsable:** Persona 3
**Fuente primaria:** `persona1_ingesta/data/processed/canal_limpio.csv` (modo `muestra`)
**Fuente secundaria:** `persona3_analisis/data/raw/fuente2_combustibles.csv` (proxy Brent; pendiente de Persona 2)
**Período:** octubre 2019 – diciembre 2025 (75 meses, 10 segmentos, 750 observaciones)
**Generado por:** `python persona3_analisis/src/run_pipeline.py`

---

## 1. Resumen ejecutivo

- **Volumen total del período:** 72,543 tránsitos · 3,245,609,026 toneladas CP/SUAB · USD 20,294,617,711 en peajes.
- **Tendencia anual de tránsitos (todos los segmentos):**

  | Año | Tránsitos anuales | Variación interanual |
  |---|---|---|
  | 2019* | 2,808 | — (solo oct–dic) |
  | 2020 | 11,792 | — (12 meses completos) |
  | 2021 | 11,692 | −0.8% |
  | 2022 | 11,784 | +0.8% |
  | 2023 | 9,747 | **−17.3%** (sequía) |
  | 2024 | 10,759 | +10.4% (recuperación parcial) |
  | 2025 | 13,961 | **+29.8%** (récord) |

  \* 2019 contiene solo 3 meses (oct–dic), por lo que no es comparable con años completos. La CAGR reportada por el script (30.6%) es engañosa por este motivo; la métrica relevante es **2025 vs 2020 = +18.4%** o **2025 vs 2022 = +18.5%**.

---

## 2. Ranking de segmentos por tránsitos

| # | Segmento | Tránsitos (75m) | Promedio mensual | Participación |
|---|---|---:|---:|---:|
| 1 | Portacontenedores | 17,740 | 237 | 24.4% |
| 2 | Quimiqueros | 13,678 | 182 | 18.9% |
| 3 | Graneles_secos | 13,592 | 181 | 18.7% |
| 4 | Tanqueros | 8,933 | 119 | 12.3% |
| 5 | Carga_refrigerada | 5,160 | 69 | 7.1% |
| 6 | Vehiculos_RoRo | 4,012 | 54 | 5.5% |
| 7 | Gas_licuado_GLP | 3,258 | 43 | 4.5% |
| 8 | Otros | 2,925 | 39 | 4.0% |
| 9 | Gas_natural_GNL | 2,188 | 29 | 3.0% |
| 10 | Pasajeros | 1,057 | 14 | 1.5% |

**Lectura:** Los tres primeros segmentos (Portacontenedores, Quimiqueros, Graneles_secos) concentran **62.1%** de los tránsitos. Refuerza la dependencia del canal del comercio marítimo global contenerizado y de graneles.

---

## 3. Impacto de la sequía 2023–may-2024 y recuperación 2025+

Comparativa de promedios mensuales por segmento (baseline = período normal, sequía = jun-2023 a may-2024, recuperación = 2025+):

| Segmento | Baseline | Sequía | Var % | Recuperación | Var % |
|---|---:|---:|---:|---:|---:|
| Portacontenedores | 240 | 177 | **−26.1%** | 281 | +17.2% |
| Graneles_secos | 183 | 134 | **−26.7%** | 219 | +19.6% |
| Quimiqueros | 183 | 137 | **−25.4%** | 224 | **+22.2%** |
| Tanqueros | 120 | 89 | **−25.9%** | 145 | +21.0% |
| Carga_refrigerada | 70 | 51 | **−27.3%** | 80 | +14.0% |
| Vehiculos_RoRo | 54 | 40 | **−25.4%** | 64 | +17.1% |
| Gas_licuado_GLP | 44 | 32 | **−27.6%** | 52 | +18.3% |
| Otros | 39 | 30 | −24.5% | 47 | +19.8% |
| Gas_natural_GNL | 30 | 22 | **−26.0%** | 34 | +14.4% |
| Pasajeros | 14 | 10 | **−28.5%** | 17 | +18.0% |

**Lecturas clave:**
- El golpe de la sequía fue **homogéneo entre segmentos** (−24% a −29%); ningún segmento escapó.
- **Pasajeros** fue el más golpeado (−28.5%); es coherente con restricciones de calado que limitan cruceros.
- En 2025 la recuperación es **generalizada** (+14% a +22%); **Quimiqueros** lidera el rebote (+22.2%), sugiriendo recuperación de demanda de productos químicos y petroquímicos.

---

## 4. Estacionalidad (descomposición aditiva, período 12)

Componente estacional promedio por mes calendario (desviación sobre la serie mensual total):

| Mes | Δ tránsitos | % sobre la media |
|---|---:|---:|
| Ene | +57 | — |
| Feb | +83 | — |
| Mar | +76 | — |
| Abr | +84 | **+8.66%** (pico) |
| May | +68 | — |
| Jun | +3 | — |
| Jul | −32 | — |
| Ago | −90 | **−9.26%** (valle) |
| Sep | −80 | — |
| Oct | −84 | — |
| Nov | −51 | — |
| Dic | −14 | — |

**Lectura:** Temporada alta de tránsitos en **febrero–mayo** (pre-temporada de huracanes del Atlántico y pico de cosechas en gráneles), valle en **agosto–octubre**. La amplitud estacional es de **~17.9 puntos porcentuales** sobre la media mensual.

---

## 5. Tendencia de largo plazo

- **Correlación Pearson(tránsitos anuales, año) = 0.637** (p=0.124).
- **Crecimiento 2022 → 2025: +18.5%** (3 años).
- El p-valor > 0.05 refleja que la serie anual es corta (7 puntos) y la sequía distorsiona; **excluyendo 2023–2024** se observa una tendencia creciente sostenida desde 2022, coherente con la recuperación post-pandemia.

---

## 6. Correlación con la segunda fuente (Brent proxy)

| Variable | Correlación con `transitos` |
|---|---:|
| `precio_barril_usd` | −0.04 (débil) |
| `precio_var_mensual_pct` | +0.01 (nula) |
| `calado_promedio_pies` | −0.05 (nula) |
| `peajes_usd` | **+0.99** (definida) |

> ⚠️ La correlación entre tránsitos y peajes es ~1 por construcción (peajes = función creciente de tránsitos). El Brent es **dato de muestra pendiente de Persona 2**; cuando se conecte la fuente real, validar la correlación real con el combustible.

---

## 7. Recomendaciones para Persona 4 (modelo predictivo)

1. **Variables exógenas útiles detectadas:** `fase_fiscal`, `periodo_sequia` (binario), `periodo_recuperacion` (binario), `precio_barril_usd` (cuando esté la fuente real).
2. **Estructura sugerida:** modelo jerárquico o por segmento, dada la heterogeneidad de patrones (Pasajeros vs Portacontenedores).
3. **Hold-out temporal:** entrenar hasta 2024-09, validar con AF2025 (oct-2024 → sep-2025) y 2025-Q4 (oct–dic 2025) como test final.
4. **Métrica principal:** MAPE sobre tránsitos totales mensuales (cuidado con meses extremos de la sequía).

## 8. Recomendaciones para Persona 5 (dashboard)

Las siguientes figuras ya están listas en `persona3_analisis/figures/` (10 PNG):

| Archivo | Uso sugerido en dashboard |
|---|---|
| `01_serie_mensual.png` | Tarjeta principal con KPI + sparkline |
| `02_descomposicion_estacional.png` | Sección "Análisis técnico" |
| `04_composicion_por_segmento.png` | Treemap o stacked-bar interactivo |
| `05_ranking_segmentos.png` | Ranking lateral |
| `06_comparativa_periodos.png` | Filtro de período + comparativa |
| `07_heatmap_correlacion.png` | Sección "Drivers macro" |
| `08_estacionalidad_fase_fiscal.png` | Heatmap pequeño en panel |
| `09_tendencia_anual.png` | Tarjeta de tendencia + CAGR |
| `10_precio_vs_transitos.png` | Sección "Segunda fuente" |

---

## 9. Limitaciones y pendientes

1. **Fuente 1:** el script de Persona 1 actualmente opera en **modo `muestra`**; cuando se confirme la URL oficial, re-ejecutar con `--modo url` y re-correr este pipeline (los esquemas son compatibles).
2. **Fuente 2 (Brent proxy):** generada sintéticamente; **Persona 2 debe reemplazarla** con datos reales y re-ejecutar `preprocesamiento.py`. El código ya detecta automáticamente si existe la fuente real o no.
3. **Sin outliers detectados** en tránsitos (validación de no-negatividad de Persona 1 ya aplicada). El período 2023–may-2024 está marcado con `periodo_sequia=1` para uso como feature categórica en el modelo.
4. **CAGR reportada por el script es engañosa** por incluir un 2019 parcial; usar 2020–2025 o 2022–2025 para comparaciones válidas.
