# Medidas DAX — Persona 3 (KPIs)

Modelo confirmado por captura: `dim_segmento` (1) → `fact_transitos`/`fact_predicciones` (*) vía `segmento_id`;
`dim_tiempo` (1) → `fact_transitos`/`fact_predicciones` (*) vía `anio_fiscal`. Relaciones activas correctas.

Crea una tabla nueva sin filas ("Modelar → Nueva tabla" con `Medidas = {}` o usa "Nueva medida" sobre `fact_transitos`)
para organizar todo. Pega cada medida en "Nueva medida".

---

## 1-3. Totales base

```dax
Total Transitos = SUM(fact_transitos[transitos])

Total Peajes USD = SUM(fact_transitos[peajes_usd])

Total Toneladas = SUM(fact_transitos[toneladas_cp_suez])
```

## 4-5. Promedios por tránsito

```dax
Peaje Promedio por Transito =
DIVIDE([Total Peajes USD], [Total Transitos])

Toneladas por Transito =
DIVIDE([Total Toneladas], [Total Transitos])
```

## 6. Variación % interanual

```dax
Transitos Anio Anterior =
CALCULATE(
    [Total Transitos],
    DATEADD(dim_tiempo[anio_fiscal], -1, YEAR)
)
```

Nota: `anio_fiscal` es numérico (no fecha), así que `DATEADD` no funcionará directo.
Usa esta alternativa robusta:

```dax
Transitos Anio Anterior =
VAR AnioActual = SELECTEDVALUE(dim_tiempo[anio_fiscal])
RETURN
CALCULATE(
    [Total Transitos],
    FILTER(ALL(dim_tiempo), dim_tiempo[anio_fiscal] = AnioActual - 1)
)

Variacion % Interanual =
DIVIDE([Total Transitos] - [Transitos Anio Anterior], [Transitos Anio Anterior])
```

## 7. CAGR FY2020–FY2025

```dax
CAGR FY2020-2025 =
VAR Inicio = CALCULATE([Total Transitos], dim_tiempo[anio_fiscal] = 2020)
VAR Fin = CALCULATE([Total Transitos], dim_tiempo[anio_fiscal] = 2025)
VAR NumAnios = 5
RETURN
IF(
    Inicio > 0,
    (Fin / Inicio) ^ (1 / NumAnios) - 1,
    BLANK()
)
```

## 8. Participación % del segmento

```dax
Participacion % Segmento =
DIVIDE([Total Transitos], CALCULATE([Total Transitos], ALL(dim_segmento)))
```

## 9. Caída vs. baseline (sequía)

```dax
Transitos Baseline =
CALCULATE([Total Transitos], dim_tiempo[periodo] = "baseline")

Transitos Sequia =
CALCULATE([Total Transitos], dim_tiempo[periodo] = "sequia")

Caida % vs Baseline =
DIVIDE([Transitos Sequia] - [Transitos Baseline], [Transitos Baseline])
```

Promedio anual comparable (baseline son 3 años, sequía son 2):

```dax
Promedio Anual Baseline =
DIVIDE([Transitos Baseline], 3)

Promedio Anual Sequia =
DIVIDE([Transitos Sequia], 2)

Caida % Anualizada vs Baseline =
DIVIDE([Promedio Anual Sequia] - [Promedio Anual Baseline], [Promedio Anual Baseline])
```

## 10. Recuperación FY2025 vs. baseline

```dax
Transitos FY2025 =
CALCULATE([Total Transitos], dim_tiempo[anio_fiscal] = 2025)

Recuperacion % FY2025 vs Baseline =
DIVIDE([Transitos FY2025] - [Promedio Anual Baseline], [Promedio Anual Baseline])
```

## 11. Ranking de segmento

```dax
Ranking Segmento =
RANKX(
    ALL(dim_segmento[segmento]),
    [Total Transitos],
    ,
    DESC
)
```

## 12. Ingreso medio por segmento

```dax
Ingreso Medio por Segmento =
DIVIDE([Total Peajes USD], DISTINCTCOUNT(dim_segmento[segmento_id]))
```

---

## Extra sugerido (fact_predicciones)

```dax
Total Transitos Predichos = SUM(fact_predicciones[transitos_predichos])

Diferencia Prediccion vs Real =
[Total Transitos Predichos] - [Total Transitos]
```

---

## Dato clave para el contexto/insight (KPI #9)

FY2024: graneleros cayeron de 2,649 → 1,278 tránsitos (**−52%**), GNL cayó **−72%**.
Úsalo como caja de texto o tarjeta destacada en la página de tendencias — es el hallazgo más fuerte que tienen.

## Verificación rápida al pegar en Power BI

1. Revisa que `dim_tiempo[periodo]` tenga exactamente los valores `"baseline"` y `"sequia"` (minúsculas, sin tilde) — si no coincide el texto, las medidas 9 y 10 devuelven blanco.
2. Prueba cada medida en una tarjeta simple antes de montarla en un gráfico, para descartar errores de sintaxis.
3. Confirma signo/escala de `Variacion % Interanual` y `CAGR` formateándolos como porcentaje (no dejarlos en decimal crudo).
