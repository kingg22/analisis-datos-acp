# Metodología del Modelo Predictivo — Canal de Panamá

**Responsable:** Persona 4
**Objetivo:** predecir el **volumen de tránsitos** del Canal de Panamá por año fiscal ACP.
**Fuentes:**
- `persona1_ingesta/data/raw/acp_transitos_por_segmento_af.csv` — tránsitos oficiales por segmento (ACP).
- `persona2_pipeline/data/processed/dataset_unificado.csv` — precio promedio del crudo por año fiscal (FMI/FRED).

**Generado por:** `python persona4_modelo/src/run_pipeline.py`

---

## 1. Planteamiento: el problema de la muestra

La ACP publica sus estadísticas por **año fiscal** (oct–sep). Modelar directamente
la serie de **totales anuales** deja solo **6 observaciones** (FY2020–FY2025).

Con 6 puntos ningún algoritmo puede aprender: en una versión previa de este
módulo el modelo ganador resultó ser la **media histórica** —un baseline sin
aprendizaje— y los tres modelos evaluados obtuvieron **R² negativo**. El
pronóstico era una constante (el promedio de los 6 años) repetida para cada año
futuro.

### La solución: modelar a nivel de segmento

La ACP **sí** publica el desglose por **segmento de mercado**. Modelar el panel
`segmento × año fiscal` multiplica por 10 la información disponible:

|  | Enfoque anterior | Enfoque actual |
|---|---|---|
| Unidad de observación | año fiscal | segmento × año fiscal |
| Observaciones | 6 | **60** |
| Datos inventados o interpolados | ninguno | **ninguno** |

**No se fabrica ni se interpola ningún dato**: las 60 filas son cifras oficiales
publicadas por la ACP. El volumen anual total se recupera sumando la predicción
de los 10 segmentos.

Además el enfoque es más informativo para el negocio: la sequía de FY2024 no
afectó por igual a todos los segmentos (el GNL cayó ~72 % mientras los
portacontenedores apenas se movieron), y un modelo por segmento aprende esa
heterogeneidad — algo imposible en la serie agregada.

---

## 2. Features

Construidas en `src/preparacion_datos.py`:

| Feature | Tipo | Descripción |
|---|---|---|
| `segmento` | one-hot (10) | Identidad del segmento de mercado. Cada segmento opera en una escala propia. |
| `precio_barril_usd_prom` | continua | Precio promedio del crudo en el año fiscal (Fuente 2). |
| `sequia` | binaria | Régimen operativo: 1 en FY2024 (racionamiento de calado), 0 el resto. |

**Target:** `transitos` (tránsitos del segmento en ese año fiscal).

### Variables deliberadamente excluidas

- **`anio_fiscal` como número.** Los modelos de árboles no extrapolan fuera del
  rango visto: un árbol entrenado con 2020–2025 no sabe qué hacer con 2026.
  Incluirla degradó el R² de **+0.921 a −0.926**.
- **`lag1`** (tránsitos del año anterior por segmento). Conceptualmente atractiva,
  pero consume el primer año de la serie y reduce la muestra de 60 a 50
  observaciones. El resultado empeoró (R² +0.884 vs. +0.921), así que se descartó.

Ambas decisiones se tomaron **por evidencia empírica en validación**, no por
intuición.

---

## 3. Esquema de validación: Leave-One-Year-Out (LOYO)

Se deja fuera **un año fiscal completo** (sus 10 segmentos), se entrena con los 5
años restantes y se predice el año excluido. Se repite para los 6 años.

Es más exigente que un Leave-One-Out por observación: si se dejara fuera una sola
fila, el modelo vería los otros 9 segmentos del mismo año y podría filtrar
información de la coyuntura de ese año. Dejando fuera el año entero, **el modelo
nunca ve nada del año que predice**.

---

## 4. Modelos comparados

| Modelo | Rol |
|---|---|
| **Media histórica** (`DummyRegressor`) | Baseline sin aprendizaje. Referencia obligatoria. |
| **Ridge** | Regresión lineal regularizada. |
| **Gradient Boosting** | Ensamble de árboles por refuerzo. |
| **Random Forest** | Ensamble de árboles por bagging. |

### Criterio de selección: MAE (no MAPE)

A nivel de segmento el **MAPE se distorsiona con denominadores pequeños**:
'Pasajeros' cayó a **17 tránsitos** en FY2021 por la pandemia, y ahí un error de
100 tránsitos pesa 588 % — más que un error de 1,000 en portacontenedores. Por
eso el baseline llega a un MAPE de 302 % a nivel de segmento, una cifra sin
interpretación útil.

La selección se hace por **MAE**, que no sufre ese sesgo. El **MAPE se reporta
sobre el total anual agregado**, donde sí es interpretable.

---

## 5. Resultados

Validación Leave-One-Year-Out sobre 60 observaciones:

| Modelo | MAE ↓ | R² ↑ | MAPE (total anual) |
|---|---:|---:|---:|
| Media histórica (baseline) | 874.7 | −0.004 | 6.53 % |
| Ridge | 231.6 | +0.899 | 5.85 % |
| Gradient Boosting | 192.3 | +0.912 | 5.97 % |
| **Random Forest (ganador)** | **181.2** | **+0.921** | 6.22 % |

**El modelo aprende de verdad:** el MAE cae **79.3 %** frente al baseline y el R²
pasa de ≈0 a **+0.921**, en una validación donde nunca vio el año que predice.

### Dos matices honestos

**a) El baseline parece competitivo en el total anual, y no lo es.**
Su MAPE anual (6.53 %) es cercano al del ganador (6.22 %), pero es un artefacto
de la agregación: el baseline predice el promedio global (~1,328) para cada
segmento, y al sumar 10 segmentos obtiene ~13,279, que casualmente se acerca al
total anual medio. Sus errores por segmento —enormes y de signo opuesto— se
cancelan al sumar. A nivel de segmento, que es donde el modelo realmente opera,
el baseline es inservible: **R² = −0.004 y MAE = 875**, frente a **+0.921 y 181**
del ganador. Por eso la evaluación primaria es a nivel de segmento.

**b) Ridge gana en MAPE anual (5.85 %) pese a tener peor MAE y R².**
Con 6 años de validación esa diferencia está dentro del ruido. Random Forest se
selecciona por el criterio declarado **de antemano** (MAE), no eligiendo a
posteriori la métrica que más favorece al resultado.

### Qué aprendió el modelo

La importancia de features confirma que captura la estructura del negocio: la
**identidad del segmento** concentra el grueso de la importancia (cada segmento
opera en una escala distinta), mientras el **régimen de sequía** y el **precio
del crudo** aportan el ajuste coyuntural.

---

## 6. Pronóstico FY2026

Escenario base, con supuestos explícitos:

- **Precio del crudo:** se arrastra el último valor observado (FY2025 =
  71.03 USD/barril). Es el supuesto de caminata aleatoria: sin un modelo propio
  del petróleo, el mejor estimador del precio futuro es el precio actual.
- **`sequia = 0`:** operación normal, coherente con la recuperación de FY2025.

**Resultado: 13,361 tránsitos totales proyectados para FY2026**, con desglose por
segmento en `output/predicciones_2026_por_segmento.csv`.

### Por qué solo un año de horizonte

El modelo explica los tránsitos por segmento, régimen y precio del crudo, pero
**no incorpora una tendencia temporal** (ver §2). Bajo supuestos constantes
produciría un valor idéntico para FY2027: extender el horizonte daría una falsa
sensación de información. Para pronosticar más lejos habría que modelar primero
la evolución del exógeno.

---

## 7. Limitaciones

1. **6 años fiscales de cobertura.** Aunque el panel tiene 60 observaciones, la
   dimensión temporal sigue siendo corta: el modelo aprende bien las diferencias
   *entre segmentos*, pero tiene poca evidencia sobre la dinámica *a lo largo del
   tiempo*.
2. **Un solo episodio de sequía.** La variable `sequia` se estima con un único año
   (FY2024). El modelo captura *que* la sequía reduce tránsitos, pero no puede
   distinguir grados de severidad.
3. **Sin estacionalidad.** La ACP no publica el desglose mensual por segmento, así
   que el modelo no captura patrones intranuales. La ACP sí publica tránsitos
   totales mensuales en los *Notices to Shipping*; incorporarlos permitiría un
   modelo estacional y es la principal vía de mejora futura.
4. **Exógeno proyectado, no conocido.** El pronóstico FY2026 depende del supuesto
   sobre el precio del crudo.

---

## 8. Reproducibilidad

```bash
python persona4_modelo/src/run_pipeline.py
```

Todas las semillas están fijadas (`random_state=42`). El pipeline es
determinista: dos ejecuciones producen resultados idénticos.
