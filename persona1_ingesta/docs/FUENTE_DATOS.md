# Documentación de la Fuente 1 — Tránsitos del Canal de Panamá

**Responsable:** Persona 1
**Última actualización:** revisar y completar al confirmar la URL definitiva

---

## 1. Origen de los datos

Los datos de tránsitos del Canal de Panamá son publicados oficialmente por la
**Autoridad del Canal de Panamá (ACP)**, entidad autónoma del Estado encargada
de la operación y administración del Canal. Cada **año fiscal** de la ACP va de
**octubre a septiembre** del año siguiente (importante para las agregaciones).

### Portales públicos disponibles

| Portal | URL | Contenido |
|---|---|---|
| Datos Abiertos de Panamá | https://www.datosabiertos.gob.pa | Datasets gubernamentales bajo licencia abierta (CC-BY 4.0) |
| INEC — Transporte | https://www.inec.gob.pa | Estadísticas de tránsito marítimo (alimentadas por ACP/AMP) |
| Pancanal — Informes Anuales | https://pancanal.com/informes-anuales/ | Informes anuales y estadísticas operativas |
| Portal Logístico de Panamá | https://logistics.gatech.pa | Estadísticas de tránsito por segmento de mercado |

---

## 2. Cifras oficiales de referencia

Estas cifras (de fuentes oficiales ACP) sirven para **validar** que los datos
ingestados sean coherentes:

- **AF2024:** 11,240 tránsitos de buques de alto y bajo calado; 210 millones de
  toneladas largas de carga; USD 3,381 millones en peajes.
- **AF2025 (segmentos principales):** portacontenedores 2,893 buques,
  graneleros 2,230, quimiqueros 2,218.
- **1er trimestre AF2026 (oct–dic 2025):** 3,107 tránsitos de alto calado
  (+22.8% interanual frente a 2,531 del año anterior).

> Contexto relevante para el análisis: la **sequía de 2023–2024** redujo los
> tránsitos por restricciones de calado y reservas; en 2025 hubo recuperación.
> El modo `muestra` del script refleja esta dinámica.

---

## 3. Formato

- **Tipo de archivo:** CSV (valores separados por comas), codificación UTF-8.
- **Granularidad esperada:** mensual, por segmento de mercado.
- **Encabezados:** se normalizan automáticamente a minúsculas con guion bajo.

---

## 4. Frecuencia de actualización

- La ACP publica estadísticas **mensuales y trimestrales**.
- Los informes anuales se publican al cierre de cada **año fiscal** (septiembre).
- **Recomendación:** re-ejecutar la ingesta de forma mensual para mantener el
  dashboard actualizado.

---

## 5. Licencia

Los datasets del Portal de Datos Abiertos de Panamá se publican bajo
**Creative Commons Atribución 4.0 Internacional (CC-BY 4.0)**: permiten uso,
redistribución y adaptación citando la fuente. **Citar a la ACP / INEC** como
origen en el dashboard y la documentación final.

---

## 6. Pasos para conectar la fuente real (pendiente del equipo)

1. Entrar a https://www.datosabiertos.gob.pa y buscar "Canal" / "tránsitos".
2. Localizar el recurso CSV y copiar su **URL de descarga directa**.
3. Opción A — configurar la variable de entorno y usar modo `url`:
   ```bash
   export URL_CANAL_CSV="<url-del-csv>"
   python src/ingesta_canal.py --modo url
   ```
4. Opción B — descargar el CSV, colocarlo en `data/raw/` y usar modo `local`.
5. Revisar el log: si el esquema difiere, ajustar el mapeo de columnas en la
   función `limpiar()`. La salida `canal_limpio.csv` debe conservar el esquema
   documentado en el README para no romper el pipeline.
