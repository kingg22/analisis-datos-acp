# Documentación de la Fuente 2 — Precios de Petróleo Crudo (FMI PCPS)

**Responsable:** Persona 2  
**Última actualización:** junio 2026

---

## 1. Origen de los datos

Los precios mensuales del petróleo crudo son publicados por el
**Fondo Monetario Internacional (FMI)** a través del sistema
**Primary Commodity Price System (PCPS)**, accessible via API SDMX JSON
sin necesidad de clave de acceso ni registro.

| Campo | Detalle |
|---|---|
| Organismo | International Monetary Fund (IMF) |
| Sistema | Primary Commodity Price System (PCPS) |
| Indicador | `POILAPSP` — Crude Oil, average spot price (UK Brent, Dubai Fateh, WTI) |
| Unidad | USD por barril (dólares corrientes) |
| Granularidad | Mensual |
| Cobertura geográfica | Mundial (`W0`) |
| Licencia | Datos públicos del FMI, uso libre con atribución |

---

## 2. Endpoint de la API

```
https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/
  PCPS/M.W0.POILAPSP.USD
  ?startPeriod=2019-10&endPeriod=2025-12
```

- **Protocolo:** HTTPS, respuesta JSON (SDMX Compact Data).
- **Autenticación:** Ninguna (API pública).
- **Rate limit:** No documentado oficialmente; usar con timeout de 30 s.
- **Formato de período:** `YYYY-MM` (ej. `2019-10`).

---

## 3. Estructura de la respuesta JSON

```json
{
  "CompactData": {
    "DataSet": {
      "Series": {
        "@FREQ": "M",
        "@REF_AREA": "W0",
        "@INDICATOR": "POILAPSP",
        "@UNIT_MEASURE": "USD",
        "Obs": [
          { "@TIME_PERIOD": "2019-10", "@OBS_VALUE": "59.71" },
          { "@TIME_PERIOD": "2019-11", "@OBS_VALUE": "62.43" }
        ]
      }
    }
  }
}
```

---

## 4. Relevancia para el análisis del Canal de Panamá

El precio del petróleo crudo está directamente vinculado a la dinámica
de tránsito por el Canal de Panamá a través de varios mecanismos:

1. **Costo de combustible (bunker fuel):** a mayor precio del crudo, mayor
   incentivo para las navieras de tomar rutas más cortas (como el Canal)
   en lugar de rodear el Cabo de Hornos, reduciendo millas de navegación.

2. **Demanda de tanqueros:** los picos de precio del crudo suelen
   correlacionar con mayor demanda de tránsito de buques tanqueros y
   de gas licuado (GNL/GLP), segmentos importantes en `canal_limpio.csv`.

3. **Contexto macroeconómico:** el precio del petróleo es un proxy del
   ciclo económico global, que también impulsa el comercio marítimo
   general medido en el Canal.

4. **Sequía 2023-2024:** la restricción de calado durante la sequía
   ocurrió en un periodo de relativa estabilidad de precios (75-85 USD),
   lo que permite aislar el efecto climático del económico en el modelo
   predictivo de Persona 4.

---

## 5. Formato de salida del script

### `persona2_pipeline/data/raw/fuente2_raw.csv`

Datos completos incluyendo features derivados:

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | `datetime` | Primer día del mes (formato `YYYY-MM-DD`) |
| `anio` | `int` | Año calendario |
| `mes` | `int` | Mes (1-12) |
| `precio_barril_usd` | `float` | Precio promedio mensual en USD/barril |
| `var_mensual_pct` | `float` | Variación porcentual respecto al mes anterior |
| `precio_barril_usd_ma3` | `float` | Media móvil de 3 meses (suavizado) |

### `persona3_analisis/data/raw/fuente2_combustibles.csv`

Subconjunto con las columnas esperadas por `preprocesamiento.py` de Persona 3:

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | `datetime` | Primer día del mes |
| `anio` | `int` | Año |
| `mes` | `int` | Mes |
| `precio_barril_usd` | `float` | Precio en USD/barril |

---

## 6. Cifras de referencia para validación

| Período | Precio aprox. (USD/barril) | Contexto |
|---|---|---|
| Oct 2019 | ~59-62 | Línea base pre-COVID |
| Abr 2020 | ~20-22 | Mínimo histórico COVID |
| Jun 2022 | ~115-120 | Pico guerra Ucrania |
| Dic 2023 | ~77-80 | Estabilización post-crisis |
| 2025 | ~70-78 | Normalización |

> Fuente de referencia: IMF World Economic Outlook, EIA Short-Term Energy Outlook.
