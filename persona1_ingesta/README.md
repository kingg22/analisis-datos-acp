# Persona 1 — Ingesta de Datos (Fuente 1: Canal de Panamá)

**Grupo 8 — Análisis de Datos del Canal de Panamá**
Segundo Parcial · Pipeline + Visualización

Este módulo cubre la **primera fuente de datos** del pipeline: los tránsitos
públicos del Canal de Panamá. Descarga, limpia, estructura y entrega los datos
en formato listo para el resto del equipo (Personas 3, 4 y 5).

---

## Qué entrega este módulo

| Archivo | Descripción | Lo consume |
|---|---|---|
| `data/processed/canal_crudo.csv` | Datos tal cual se ingestan (sin limpiar) | Trazabilidad |
| `data/processed/canal_limpio.csv` | Dataset limpio por año fiscal × segmento | Persona 2 (pipeline), Persona 3 |
| `data/processed/canal_serie_anual.csv` | Serie anual de tránsitos totales | Persona 4 (modelo predictivo) |

---

## Estructura

```
persona1_ingesta/
├── src/
│   ├── construir_datos_acp.py  # Paso 0: genera los CSV oficiales en data/raw/ (reproducible + verificado)
│   └── ingesta_canal.py        # Script principal (ingesta + limpieza + persistencia)
├── data/
│   ├── raw/                    # Datos oficiales ACP (acp_*.csv) + CSV del modo "local"
│   └── processed/              # Salidas generadas por el script
├── docs/
│   └── FUENTE_DATOS.md         # Documentación de la fuente (formato, frecuencia, licencia)
├── requirements.txt
└── README.md
```

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Uso

### Paso 0 — Generar los datos oficiales (reproducible)

Los CSV oficiales de `data/raw/` se generan con un script que transcribe las
cifras de los Informes Anuales de la ACP **con su cita exacta** (informe, gráfica,
página) y las **verifica automáticamente**: la suma de tránsitos por segmento de
cada año fiscal debe coincidir con el total oficial publicado por la ACP; si no
cuadra, el script aborta. Así queda documentado y demostrable de dónde salen.

```bash
python src/construir_datos_acp.py
# -> OK - Todos los años fiscales cuadran con los totales oficiales de la ACP.
```

(Los CSV ya están versionados en `data/raw/`, así que este paso solo es necesario
para regenerarlos o auditar su procedencia.)

### Modo oficial (por defecto)
Construye la serie a partir de **datos oficiales reales de la ACP** guardados en
`data/raw/` (`acp_transitos_por_segmento_af.csv` y `acp_indicadores_anuales_af.csv`),
transcritos de los Informes Anuales 2022 y 2025 de la ACP. Cubre los años
fiscales **FY2020–FY2025** (tránsitos por segmento, tonelaje PC/UMS y peajes).

```bash
python src/ingesta_canal.py --modo oficial
```

> **Granularidad:** la ACP publica el desglose por segmento a nivel **anual**
> (año fiscal, oct–sep), así que el proyecto trabaja con datos **anuales reales**
> — sin inventar una distribución mensual. Ver `docs/FUENTE_DATOS.md`.

### Modo local
Lee un CSV ya descargado manualmente y colocado en `data/raw/`. Pensado por si
en el futuro la ACP publica un CSV descargable de tránsitos.

```bash
python src/ingesta_canal.py --modo local
```

---

## Flujo del módulo

1. **Ingesta** — obtiene los datos crudos anuales (oficial / local).
2. **Limpieza** — normaliza columnas, elimina duplicados, maneja nulos, valida
   tránsitos no negativos y ordena por año fiscal y segmento.
3. **Estructuración** — construye la serie anual agregada de tránsitos.
4. **Persistencia** — guarda los 3 CSV en `data/processed/`.

---

## Esquema de `canal_limpio.csv`

| Columna | Tipo | Descripción |
|---|---|---|
| `anio_fiscal` | int | Año fiscal ACP (oct–sep) |
| `segmento` | str | Segmento de mercado del buque |
| `transitos` | int | Tránsitos del segmento en ese año fiscal (cifra oficial ACP) |
| `calado_promedio_pies` | float | Calado nominal de referencia por segmento (valor ilustrativo, **no** publicado por la ACP) |
| `toneladas_cp_suez` | int | Tonelaje PC/UMS prorrateado del total anual oficial |
| `peajes_usd` | int | Peajes prorrateados del total anual oficial de peajes (B/. ≈ USD) |

`canal_serie_anual.csv` agrega por año fiscal: `anio_fiscal, transitos_totales,
toneladas_totales, peajes_totales_usd`.

---

## Nota para el equipo

> El modo `oficial` (datos reales de la ACP) está activo por defecto. Los
> **tránsitos por segmento, el tonelaje y los peajes son cifras oficiales reales**
> de los Informes Anuales de la ACP (FY2020–FY2025), a granularidad anual. Si más
> adelante aparece un CSV oficial descargable, basta con colocarlo en `data/raw/`
> y usar `--modo local`.

Ver `docs/FUENTE_DATOS.md` para el detalle de la fuente pública y las cifras.
