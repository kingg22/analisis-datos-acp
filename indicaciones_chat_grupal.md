# Examen semetral (6 julio)

Que estaremos evaluando en la continuacion del parcial #2 

- Aplicar al menos una técnica de aprendizaje automático (Machine Learning), ya sea de clasificación, regresión o clustering, y justificar por qué el modelo seleccionado es el más adecuado para el problema planteado. Además, explicar los principales conceptos y resultados del modelo de predicción implementado.
- Diseñar e implementar un modelo estrella para la estructura de datos utilizada en Power BI.
- Desarrollar los dashboards en Power BI, incorporando visualizaciones claras e interactivas que faciliten el análisis de la información.
- Ampliar la cantidad de indicadores (KPIs) para obtener una visión más completa del comportamiento de los datos.
- Incorporar el uso de Modelos de Lenguaje de Gran Escala (LLMs) para interactuar con los datos mediante consultas en lenguaje natural, generación de resúmenes o apoyo al análisis de la información.

---

# Correciones de entrega anterior (lunes 20 julio)

## Persona 1 — Ingesta Fuente 1 (Canal) · El problema más grave
Diagnóstico: Los tránsitos del Canal no son datos públicos reales; se generan por fórmula con np.random.default_rng(42) en la función data_muestra() (persona1_ingesta/src/ingesta_canal.py, líneas 78-144). El modo url no funciona (requiere la variable de entorno URL_CANAL_CSV que está vacía) y no hay ningún CSV real en data/raw/.

Por qué importa: El enunciado pide literalmente "Ingesta de datos públicos del Canal". Este es el único requisito que el proyecto no cumple de verdad.

Qué debe hacer (en orden de prioridad):

Conseguir una fuente pública real de tránsitos del Canal (portal de datos abiertos de Panamá, INEC, o reportes de tráfico de la ACP) y descargarla vía --modo url o --modo local.
Si no encuentra CSV descargable, extraer aunque sea las cifras reales de los reportes oficiales de la ACP y cargarlas manualmente — que los números salgan de una fuente real, no de rng.normal.
Corregir el comentario engañoso en las líneas 25-26 y 82: dice "cifras oficiales reales publicadas por la ACP" cuando la serie es fabricada. Eso, si el profesor lo lee, se ve mal.

## Ingesta Fuente 2 (Petróleo) + Pipeline · Fácil de arreglar
Diagnóstico: Los precios del petróleo commiteados también son sintéticos (reproduje el generador con semilla 42 y dio exactamente los valores del CSV). PERO aquí sí hay una API real del FMI que funciona (ingesta_fuente2.py, --modo api). El pipeline de unión está bien hecho y es funcional.

Qué debe hacer:

Correr python persona2_pipeline/src/ingesta_fuente2.py --modo api con internet y volver a commitear los CSV con datos reales del FMI. Con esto al menos una de las dos fuentes queda 100% real sin tocar código.
Volver a correr el pipeline (pipeline.py) para regenerar dataset_unificado*.csv con los precios reales.
Nota: el pipeline en sí está bien; solo hay que alimentarlo con datos reales.

---

# Indicaciones nueva entrega (martes 21 julio)

Aquí tienes el mensaje listo para enviar. Todo está verificado contra los archivos reales del repo.

---

# 📋 Reparto de tareas — Continuación Parcial #2

**Contexto:** ahora se evalúan 5 puntos nuevos, centrados en **Power BI**. Lo que ya tenemos en Python/Streamlit sigue sirviendo como fuente de datos — no se tira nada.

## ⚠️ Orden de trabajo (importante)

```
Persona 2 (modelo estrella) ──► Personas 1, 3, 4 (dashboards + KPIs)
                            └─► Persona 5 (LLM)
```

**Persona 2 va primero.** Nadie puede armar visuales ni medidas hasta que el modelo estrella esté cargado. Meta sugerida: **2–3 días**, y luego P2 apoya en dashboards.

*Excepción:* Persona 4 puede adelantar 4 de sus 5 visuales sin esperar.

---

## 🟦 PERSONA 2 — Modelo estrella (BLOQUEANTE)

**Archivo base:** `persona3_analisis/data/processed/canal_unificado.csv` (60 filas)

**Estructura a construir:**

```
     dim_tiempo (6)            dim_segmento (10)
            \                        /
             └──► fact_transitos (60) ◄──┘
             └──► fact_predicciones (10) ◄──┘
```

**Tablas:**

| Tabla | Filas | Columnas |
|---|---|---|
| `dim_segmento` | 10 | `segmento_id`, `segmento`, `nombre_display`, `categoria` |
| `dim_tiempo` | 6 | `anio_fiscal`, `etiqueta` (FY2020…), `periodo`, `es_sequia`, `precio_barril_usd_prom` |
| `fact_transitos` | 60 | `anio_fiscal`, `segmento_id`, `transitos`, `toneladas_cp_suez`, `peajes_usd` |
| `fact_predicciones` | 10 | `anio_fiscal`, `segmento_id`, `transitos_predichos` |

**Datos para las dimensiones:**
- **Segmentos (10):** Carga_general, Carga_refrigerada, Gas_licuado_GLP, Gas_natural_GNL, Graneles_secos, Otros, Pasajeros, Portacontenedores, Tanqueros_quimiqueros, Vehiculos_RoRo
- **Períodos (3):** `baseline` (FY2020–22), `sequia` (FY2023–24), `recuperacion` (FY2025)
- **`categoria`:** agrúpalos tú (ej. Contenedores / Graneles / Líquidos / Gases / Otros)

**Relaciones:** 1 a muchos desde cada dimensión hacia ambas tablas de hechos.

**Entregable:** archivo `.pbix` con el modelo cargado y relaciones armadas → se lo pasas a P1, P3 y P4.

---

## 🟩 PERSONA 3 — Ampliar KPIs (medidas DAX)

**Depende de:** Persona 2

**Medidas a crear (mínimo 10):**

| # | KPI | Base |
|---|---|---|
| 1 | Total tránsitos | `SUM(transitos)` |
| 2 | Total peajes USD | `SUM(peajes_usd)` |
| 3 | Total toneladas | `SUM(toneladas_cp_suez)` |
| 4 | **Peaje promedio por tránsito** | peajes ÷ tránsitos |
| 5 | **Toneladas por tránsito** | toneladas ÷ tránsitos |
| 6 | **Variación % interanual** | vs. año fiscal anterior |
| 7 | **CAGR FY2020–FY2025** | crecimiento anual compuesto |
| 8 | **Participación % del segmento** | segmento ÷ total |
| 9 | **Caída vs. baseline** | sequía vs. FY2020–22 |
| 10 | **Recuperación FY2025** | FY2025 vs. baseline |
| 11 | Ranking de segmento | RANKX |
| 12 | Ingreso medio por segmento | peajes ÷ nº segmentos |

**Dato clave para el #9:** en FY2024 los graneleros cayeron de 2,649 a 1,278 (−52%) y el GNL un −72%. Son los números más impactantes que tenemos.

---

## 🟨 PERSONA 1 — Dashboards, parte A (2 páginas)

**Depende de:** Persona 2

**Página 1 — Visión General**
- Fila de tarjetas KPI (usa las medidas de P3)
- Mapa del Canal (coordenadas: Balboa, Miraflores, Pedro Miguel, Gatún, Colón)
- Evolución de tránsitos FY2020–FY2025
- Segmentador por año fiscal

**Página 2 — Tendencias históricas**
- Composición por segmento y año (barras apiladas)
- Ranking de segmentos
- Comparativa de períodos: baseline vs. sequía vs. recuperación
- Precio del crudo vs. tránsitos (eje doble)
- Segmentadores por segmento y período

**Referencia visual:** las figuras en `persona3_analisis/figures/` ya muestran estos gráficos hechos en Python — replícalos en Power BI.

---

## 🟧 PERSONA 4 — Modelo ML + Dashboard, parte B

**Puede empezar YA** (4 de 5 visuales no dependen de P2)

**Parte 1 — Justificar y explicar el modelo** *(ya está implementado)*
- Por qué **regresión** y no clasificación/clustering
- Por qué **Random Forest**: R²=0.921, MAE=181 vs. baseline MAE=875 (**−79% de error**)
- Explicar: validación Leave-One-Year-Out, R², MAE, baseline, importancia de features
- Resultado: **FY2026 = 13,361 tránsitos**

**Parte 2 — Página "Modelo Predictivo" en Power BI**

| Visual | Archivo |
|---|---|
| 3 tarjetas: 13,361 / R² 0.921 / MAE 181 | `predicciones_2026.csv`, `metricas_modelos.csv` |
| Barras: comparativa de 4 modelos | `metricas_modelos.csv` |
| Barras: importancia de features | `importancia_features.csv` |
| Real vs. predicho por año | `predicciones_test.csv` |
| Predicción por segmento | `predicciones_2026_por_segmento.csv` *(este sí necesita a P2)* |

**Obligatorio:** caja de texto con el supuesto → *"Escenario base: crudo $71.03/barril, sin sequía"*

---

## 🟪 PERSONA 5 — LLM

**Depende de:** Persona 2

**Parte 1 — Consultas en lenguaje natural (dentro de Power BI)**
- Agregar el **visual de P&R (Q&A)** — es nativo y gratis, no requiere licencia Copilot
- Configurar sinónimos para que entienda "buques", "naves", "barcos" → tránsitos
- Preparar 4–5 preguntas de demostración que funcionen seguro

**Parte 2 — Resúmenes ejecutivos**
- Mantener la integración con Claude/OpenAI que **ya funciona en Streamlit**
- Generar los resúmenes y embeberlos como texto en Power BI

**⚠️ Verificar primero:** Power BI **Copilot** requiere capacidad de pago (Fabric F64+/Premium). Confirmar qué licencia tiene la universidad **antes** de comprometerse. El visual de P&R es el plan seguro y no cuesta nada.

**⚠️ No usar visuales de Python** para llamar a la API: funcionan en Desktop pero **pierden internet al publicar** al servicio.

---

## Riesgos del equipo

1. **Nadie ha usado Power BI en este proyecto** — hay curva de aprendizaje, no lo dejen para el final
2. **Datos limitados:** 6 años × 10 segmentos = 60 filas. La ACP publica el desglose por segmento solo anual, no mensual. **Conviene decirlo en la presentación** en vez de que lo pregunten
3. **Duda para el profesor:** ¿Power BI *reemplaza* a Streamlit o se suman? Cambia bastante la carga de P5

---

Un par de notas para ti (no para el mensaje):

- **`categoria` en `dim_segmento` la inventé yo** — no viene en los datos. Es útil para agrupar visuales, pero que P2 sepa que es una decisión de diseño, no un dato de la ACP.
- **No verifiqué que el visual de P&R funcione bien en español** con nombres de columna como `transitos` sin tilde. Que P5 lo pruebe temprano; puede que necesite configurar sinónimos más de lo previsto.
