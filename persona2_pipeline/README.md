# Persona 2 — Ingesta de Datos (Fuente 2) + Pipeline

**Grupo 8 — Análisis de Datos del Canal de Panamá**  
Segundo Parcial · Pipeline + Visualización

Este módulo cubre la **segunda fuente de datos** y el **pipeline de integración**
que une ambas fuentes en datasets listos para análisis y modelado.

---

## Qué entrega este módulo

| Archivo | Descripción | Lo consume |
|---|---|---|
| `data/raw/fuente2_raw.csv` | Precios mensuales del petróleo crudo + features derivados | Trazabilidad local |
| `data/processed/dataset_unificado.csv` | Serie mensual: tránsitos totales + precio barril | Persona 4 (ML) |
| `data/processed/dataset_unificado_completo.csv` | Canal por segmento × mes + precio barril | Persona 3 (EDA) |
| `persona3_analisis/data/raw/fuente2_combustibles.csv` | Copia para Persona 3 (formato esperado por `preprocesamiento.py`) | Persona 3 |

---

## Fuente 2: Precios de Petróleo Crudo (FMI PCPS)

- **Organismo:** International Monetary Fund — Primary Commodity Price System
- **Indicador:** `POILAPSP` (Crude Oil, average spot price, USD/barril)
- **API pública:** Sin clave de acceso. Ver `docs/FUENTE_DATOS.md` para detalle.
- **Cobertura:** Oct 2019 – Dic 2025 (mismo rango que Fuente 1 de Persona 1)

---

## Estructura

```
persona2_pipeline/
├── src/
│   ├── ingesta_fuente2.py    # Descarga precios del petróleo (FMI PCPS API)
│   └── pipeline.py           # Orquestador: une Fuente 1 + Fuente 2
├── data/
│   ├── raw/                  # fuente2_raw.csv (generado al ejecutar)
│   └── processed/            # dataset_unificado*.csv (generados al ejecutar)
├── docs/
│   └── FUENTE_DATOS.md       # Documentación de la Fuente 2
├── requirements.txt
└── README.md
```

---

## Instalación

```bash
pip install -r requirements.txt
```

O desde la raíz del proyecto con `uv`:

```bash
uv sync
```

---

## Uso

### Opción A — Solo ingesta de Fuente 2

```bash
# Descarga datos reales del FMI (requiere internet)
python src/ingesta_fuente2.py --modo api

# Genera datos sintéticos (sin internet, para desarrollo)
python src/ingesta_fuente2.py --modo muestra
```

### Opción B — Pipeline completo (recomendado)

```bash
# Ejecuta todo: Fuente 1 + Fuente 2 + join → datasets unificados
python src/pipeline.py

# Con modos explícitos
python src/pipeline.py --modo-fuente1 muestra --modo-fuente2 api
```

El pipeline:
1. Verifica si los datos de Persona 1 ya están en disco; si no, los genera.
2. Descarga/genera los precios de la Fuente 2.
3. Hace el join mensual por `fecha`.
4. Exporta `dataset_unificado.csv` y `dataset_unificado_completo.csv`.
5. Copia `fuente2_combustibles.csv` a `persona3_analisis/data/raw/` automáticamente.

---

## Esquema de los datasets de salida

### `dataset_unificado.csv` (para Persona 4)

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | datetime | Primer día del mes |
| `transitos_totales` | int | Total de tránsitos mensuales (Fuente 1) |
| `precio_barril_usd` | float | Precio del petróleo crudo (USD/barril) |
| `var_mensual_pct` | float | Variación % del precio respecto al mes anterior |
| `precio_barril_usd_ma3` | float | Media móvil 3 meses del precio |
| `anio` | int | Año |
| `mes` | int | Mes (1-12) |

### `dataset_unificado_completo.csv` (para Persona 3)

Todas las columnas de `canal_limpio.csv` (Persona 1) + `precio_barril_usd` + `precio_barril_usd_ma3`.

---

## Diseño del pipeline

El pipeline es intencional en su simplicidad: scripts Python secuenciales
sin dependencia de Airflow ni Prefect. Cada paso está claramente delimitado
en funciones en `pipeline.py`, lo que facilita migrar a un DAG de Prefect
si el equipo lo requiere en el futuro.

```
Fuente 1 (ACP)          Fuente 2 (FMI PCPS)
persona1_ingesta/   +   persona2_pipeline/
canal_serie_mensual.csv  fuente2_raw.csv
canal_limpio.csv              |
        |                     |
        +------[ JOIN ]-------+
               fecha
                |
        dataset_unificado.csv           → Persona 4
        dataset_unificado_completo.csv  → Persona 3
        fuente2_combustibles.csv        → Persona 3
```
