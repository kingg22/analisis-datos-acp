# Guía para Power BI Desktop — Persona 5

## 1. Cargar los datos

1. Abrí Power BI Desktop
2. **Obtener datos** → **Texto/CSV**
3. Seleccioná `data\powerbi\datos_powerbi_completos.csv`
4. **Cargar**
5. Repetí para `data\powerbi\fact_predicciones.csv` (predicciones 2026)

## 2. Crear relaciones (Modelo estrella)

1. Click en **Modelo** (barra izquierda)
2. Arrastrá y conectá:
   - Asegurate que las relaciones se auto-detecten al cargar los CSVs
   - Si no, crealas manualmente: `anio_fiscal` conecta ambas tablas

## 3. Agregar visual Q&A

1. En el panel **Visualizaciones**, click en el icono de **Preguntas y respuestas** (Q&A)
2. Se agrega al lienzo — probá escribiendo preguntas

## 4. Configurar sinónimos

1. Click en el visual Q&A
2. En el panel **Visualizaciones**, click en **Configuración** (engranaje)
3. Sección **Sinónimos** → agregá:

| Columna | Sinónimos |
|---|---|
| `transitos` | buques, naves, barcos, cruces |
| `segmento` | tipo de buque, clase, categoria |
| `peajes_usd` | ingresos, tarifas, peaje |
| `periodo` | etapa, fase |
| `categoria` | grupo, tipo |
| `anio_fiscal` | año, año fiscal, ejercicio |

## 5. Preguntas demo para Q&A

Estas 5 preguntas funcionan seguro con los nombres de columna actuales:

```text
1. total de transitos por anio fiscal
2. transitos by segmento
3. promedio de peajes por categoria
4. transitos by periodo
5. cual fue el total de transitos en 2024
```

## 6. Agregar el resumen ejecutivo

1. Abrí el archivo `persona5_dashboard/docs/RESUMEN_EJECUTIVO.md`
2. Copiá todo el contenido
3. En Power BI Desktop, agregá un **Cuadro de texto**
4. Pegá el contenido

## 7. Guardar

1. **Archivo** → **Guardar como** → `Canal Panama - Dashboard.pbix`
2. Publicá si tenés acceso: **Publicar** → elegí workspace en Power BI Service
