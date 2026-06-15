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
| `data/processed/canal_limpio.csv` | Dataset limpio y estructurado por segmento | Persona 2 (pipeline), Persona 3 |
| `data/processed/canal_serie_mensual.csv` | Serie temporal mensual de tránsitos totales | Persona 4 (modelo predictivo) |

---

## Estructura

```
persona1_ingesta/
├── src/
│   └── ingesta_canal.py        # Script principal (ingesta + limpieza + persistencia)
├── data/
│   ├── raw/                    # CSV descargados manualmente (modo "local")
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

El script tiene **3 modos** según de dónde se obtienen los datos:

### Modo muestra (por defecto, para desarrollo)
Genera datos basados en cifras oficiales reales de la ACP. Permite a todo
el equipo avanzar mientras se confirma la URL de descarga definitiva.

```bash
python src/ingesta_canal.py --modo muestra
```

### Modo local
Lee un CSV ya descargado manualmente y colocado en `data/raw/`.

```bash
python src/ingesta_canal.py --modo local
```

### Modo url
Descarga el CSV directamente desde el portal público. Requiere configurar
la variable de entorno `URL_CANAL_CSV`.

```bash
export URL_CANAL_CSV="https://www.datosabiertos.gob.pa/.../transitos.csv"
python src/ingesta_canal.py --modo url
```

---

## Flujo del módulo

1. **Ingesta** — obtiene los datos crudos (url / local / muestra).
2. **Limpieza** — normaliza columnas, convierte fechas, elimina duplicados,
   maneja nulos, valida tránsitos no negativos y ordena cronológicamente.
3. **Estructuración** — construye una serie mensual agregada de tránsitos.
4. **Persistencia** — guarda los 3 CSV en `data/processed/`.

---

## Esquema de `canal_limpio.csv`

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | date | Primer día del mes del registro |
| `anio` | int | Año calendario |
| `mes` | int | Mes (1–12) |
| `anio_fiscal` | int | Año fiscal ACP (oct–sep) |
| `segmento` | str | Segmento de mercado del buque |
| `transitos` | int | Número de tránsitos del segmento en ese mes |
| `calado_promedio_pies` | float | Calado promedio en pies |
| `toneladas_cp_suez` | int | Carga estimada (toneladas CP/SUAB) |
| `peajes_usd` | int | Peajes estimados en USD |

---

## Nota para el equipo

> El modo `muestra` está activo por defecto para no bloquear el desarrollo.
> Apenas se confirme la URL/archivo oficial, basta con cambiar a `--modo url`
> o `--modo local`: **el resto del pipeline no necesita modificarse**, porque
> la salida (`canal_limpio.csv`) mantiene el mismo esquema.

Ver `docs/FUENTE_DATOS.md` para el detalle de la fuente pública.
