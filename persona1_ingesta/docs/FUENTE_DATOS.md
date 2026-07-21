# Documentación de la Fuente 1 — Tránsitos del Canal de Panamá

**Responsable:** Persona 1
**Última actualización:** 2026-07-20

---

## 1. Origen de los datos

Los datos de tránsitos del Canal de Panamá son publicados oficialmente por la
**Autoridad del Canal de Panamá (ACP)**, entidad autónoma del Estado encargada
de la operación y administración del Canal. Cada **año fiscal (AF)** de la ACP va
de **octubre a septiembre** del año siguiente (importante para las agregaciones).

La fuente concreta usada en este proyecto son los **Informes Anuales oficiales de
la ACP**, descargables públicamente:

| Documento | URL | Aporta |
|---|---|---|
| Informe Anual 2025 (ACP) | https://pancanal.com/wp-content/uploads/2026/02/Informe-2025Eng.pdf | Tránsitos por segmento FY2023–FY2025 (Gráfica 6), tonelaje PC/UMS, peajes (estados financieros) |
| Informe Anual 2022 (ACP) | https://pancanal.com/wp-content/uploads/2023/02/Informe-2022-Eng.pdf | Tránsitos por segmento FY2020–FY2022 (Gráfica 6), tonelaje PC/UMS, peajes |
| Índice de Informes Anuales | https://pancanal.com/en/maritime-services/annual-report/ | Listado histórico de informes |

Otros portales públicos de referencia:

| Portal | URL |
|---|---|
| Estadísticas ACP | https://pancanal.com/en/statistics/ |
| Portal Logístico de Panamá | https://logistics.gatech.pa |
| Datos Abiertos de Panamá | https://www.datosabiertos.gob.pa |

---

## 2. Datos ingestados (archivos en `data/raw/`)

Las cifras de los informes anuales se transcribieron a dos CSV que constituyen la
entrada real del pipeline (cada fila incluye la columna `fuente`):

- **`acp_transitos_por_segmento_af.csv`** — tránsitos por segmento de mercado y
  año fiscal (FY2020–FY2025), 10 segmentos.
- **`acp_indicadores_anuales_af.csv`** — por año fiscal: tránsitos totales,
  tonelaje PC/UMS (millones), peajes (millones de balboas) e ingresos totales.

Estos CSV **no se editan a mano**: se generan con el script reproducible
`src/construir_datos_acp.py`, que declara cada cifra con su cita (informe, gráfica,
página) y **verifica** que la suma de los segmentos coincida exactamente con el
total oficial de cada año fiscal antes de escribir los archivos. Para regenerarlos
o auditar su procedencia:

```bash
python src/construir_datos_acp.py
```

### Tránsitos por segmento (oficiales, ACP) — verificados contra el total anual

| Segmento | FY2020 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|---:|---:|---:|
| Graneles secos | 2,759 | 3,043 | 2,910 | 2,649 | 1,278 | 2,230 |
| Tanqueros y quimiqueros | 2,779 | 2,596 | 2,939 | 2,695 | 2,230 | 2,662 |
| Portacontenedores | 2,551 | 2,602 | 2,822 | 2,787 | 2,773 | 2,893 |
| Gas licuado (GLP) | 1,305 | 1,523 | 1,501 | 1,757 | 1,561 | 1,805 |
| Vehículos / RoRo | 672 | 782 | 747 | 813 | 783 | 871 |
| Carga refrigerada | 607 | 564 | 604 | 546 | 436 | 516 |
| Carga general | 612 | 508 | 653 | 526 | 287 | 463 |
| Gas natural (GNL) | 419 | 537 | 374 | 326 | 115 | 61 |
| Pasajeros | 227 | 17 | 129 | 251 | 205 | 214 |
| Otros | 1,438 | 1,170 | 1,560 | 1,730 | 1,572 | 1,689 |
| **Total** | **13,369** | **13,342** | **14,239** | **14,080** | **11,240** | **13,404** |

Los totales por columna coinciden exactamente con los totales oficiales de
tránsitos publicados por la ACP para cada año fiscal.

### Indicadores anuales (oficiales, ACP)

| AF | Tránsitos | Tonelaje PC/UMS (M) | Peajes (B/. M) | Ingresos totales (B/. M) |
|---|---:|---:|---:|---:|
| FY2020 | 13,369 | 475.2 | 2,663.0 | — |
| FY2021 | 13,342 | 516.7 | 2,968.2 | 3,958.6 |
| FY2022 | 14,239 | 518.8 | 3,027.9 | 4,322.6 |
| FY2023 | 14,080 | 511.1 | 3,348.3 | 4,968.0 |
| FY2024 | 11,240 | 423.1 | 3,179.1 | 4,986.0 |
| FY2025 | 13,404 | 489.2 | 4,007.9 | 5,704.6 |

> Corrección respecto a versiones previas de este documento: los peajes de FY2024
> son **B/.3,179.1 millones** (estados financieros auditados, Informe Anual 2025),
> no 3,381 millones.

Contexto para el análisis: la **sequía de 2023–2024** redujo los tránsitos
(especialmente graneleros, que cayeron de 2,649 en FY2023 a 1,278 en FY2024) por
restricciones de calado; en **FY2025** hubo recuperación (+19.3% de tránsitos).

---

## 3. Granularidad (importante)

La ACP publica el desglose por segmento a nivel **anual (año fiscal)**, no mensual.
Por eso **todo el proyecto trabaja con datos anuales** (una fila por año fiscal ×
segmento) — no se inventa ninguna distribución mensual. Notas:

- Los tránsitos por segmento son cifras oficiales reales de la ACP.
- El tonelaje y los peajes anuales oficiales se prorratean de forma proporcional
  a los tránsitos de cada segmento (la suma por año fiscal reproduce la cifra
  oficial).
- **`calado_promedio_pies`** es un valor **nominal de referencia** por segmento,
  **no** publicado por la ACP; se incluye solo para conservar el esquema del
  pipeline.

---

## 4. Formato

- **Tipo de archivo:** CSV (valores separados por comas), codificación UTF-8.
- **Granularidad:** anual por segmento (año fiscal ACP); es la granularidad que usa todo el pipeline.
- **Encabezados:** se normalizan automáticamente a minúsculas con guion bajo.

---

## 5. Frecuencia de actualización

- Los informes anuales se publican al cierre de cada **año fiscal** (septiembre).
- La ACP también publica **resúmenes mensuales de operaciones** (Notices to
  Shipping) con tránsitos totales por mes, útiles para actualizar la serie.
- **Recomendación:** al publicarse el nuevo informe anual, añadir las filas del
  año fiscal a los CSV de `data/raw/` y re-ejecutar la ingesta.

---

## 6. Licencia y atribución

Los informes de la ACP son documentos públicos. **Citar a la Autoridad del Canal
de Panamá (ACP)** como origen en el dashboard y la documentación final, indicando
el Informe Anual correspondiente.

---

## 7. Cómo conectar un CSV oficial (modo `local`)

Si en el futuro la ACP publica un CSV mensual descargable:

1. Descargar el CSV y colocarlo en `data/raw/`.
2. Ejecutar `python src/ingesta_canal.py --modo local`.
3. Si el esquema difiere, ajustar el mapeo de columnas en `limpiar()`. La salida
   `canal_limpio.csv` debe conservar el esquema documentado en el README para no
   romper el pipeline.
