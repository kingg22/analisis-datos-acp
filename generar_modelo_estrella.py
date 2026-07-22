"""
Genera el modelo estrella (dimensional) para Power BI.

Fuentes:
  - persona3_analisis/data/processed/canal_unificado.csv
  - persona4_modelo/output/predicciones_2026_por_segmento.csv

Salida en data/powerbi/:
  - dim_segmento.csv      (10 filas)
  - dim_tiempo.csv        ( 6 filas: FY2020–FY2025)
  - fact_transitos.csv    (60 filas)
  - fact_predicciones.csv (10 filas: FY2026)
"""

import pandas as pd
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
SRC_CANAL = ROOT / "persona3_analisis" / "data" / "processed" / "canal_unificado.csv"
SRC_PRED  = ROOT / "persona4_modelo"  / "output" / "predicciones_2026_por_segmento.csv"
OUT_DIR   = ROOT / "data" / "powerbi"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Lectura de fuentes ────────────────────────────────────────────────────────
canal = pd.read_csv(SRC_CANAL)
pred  = pd.read_csv(SRC_PRED)

# ── dim_segmento ──────────────────────────────────────────────────────────────
# nombre_display: etiqueta limpia para Power BI
# categoria: Contenedores | Graneles | Líquidos | Gases | Otros
SEGMENTO_META: dict[str, tuple[str, str]] = {
    "Carga_general":         ("Carga general",          "Graneles"),
    "Carga_refrigerada":     ("Carga refrigerada",      "Graneles"),
    "Gas_licuado_GLP":       ("Gas licuado (GLP)",      "Gases"),
    "Gas_natural_GNL":       ("Gas natural (GNL)",      "Gases"),
    "Graneles_secos":        ("Graneles secos",          "Graneles"),
    "Otros":                 ("Otros",                   "Otros"),
    "Pasajeros":             ("Pasajeros",               "Otros"),
    "Portacontenedores":     ("Portacontenedores",       "Contenedores"),
    "Tanqueros_quimiqueros": ("Tanqueros / Quimiqueros", "Líquidos"),
    "Vehiculos_RoRo":        ("Vehículos RoRo",          "Otros"),
}

dim_segmento = pd.DataFrame(
    [
        {
            "segmento_id":    idx + 1,
            "segmento":       seg,
            "nombre_display": meta[0],
            "categoria":      meta[1],
        }
        for idx, (seg, meta) in enumerate(SEGMENTO_META.items())
    ]
)
dim_segmento.to_csv(OUT_DIR / "dim_segmento.csv", index=False, encoding="utf-8-sig")
print(f"✓ dim_segmento.csv      → {len(dim_segmento)} filas")

# ── dim_tiempo ────────────────────────────────────────────────────────────────
# Periodos:  baseline     = FY2020–FY2022
#            sequia       = FY2023–FY2024
#            recuperacion = FY2025
# es_sequia: 1 para FY2023–FY2024, 0 resto
precios_anuales = (
    canal.groupby("anio_fiscal")["precio_barril_usd_prom"]
    .first()
    .reset_index()
    .sort_values("anio_fiscal")
)

def _periodo(y: int) -> str:
    if y <= 2022:
        return "baseline"
    if y <= 2024:
        return "sequia"
    return "recuperacion"

dim_tiempo = pd.DataFrame({
    "anio_fiscal":            precios_anuales["anio_fiscal"],
    "etiqueta":               precios_anuales["anio_fiscal"].apply(lambda y: f"FY{y}"),
    "periodo":                precios_anuales["anio_fiscal"].apply(_periodo),
    "es_sequia":              precios_anuales["anio_fiscal"].apply(lambda y: 1 if 2023 <= y <= 2024 else 0),
    "precio_barril_usd_prom": precios_anuales["precio_barril_usd_prom"].round(2),
})
dim_tiempo.to_csv(OUT_DIR / "dim_tiempo.csv", index=False, encoding="utf-8-sig")
print(f"✓ dim_tiempo.csv        → {len(dim_tiempo)} filas")

# ── Mapa segmento → segmento_id ───────────────────────────────────────────────
seg_id: dict[str, int] = dim_segmento.set_index("segmento")["segmento_id"].to_dict()

# ── fact_transitos ────────────────────────────────────────────────────────────
fact_transitos = (
    canal[["anio_fiscal", "segmento", "transitos", "toneladas_cp_suez", "peajes_usd"]]
    .copy()
    .assign(segmento_id=lambda df: df["segmento"].map(seg_id))
    [["anio_fiscal", "segmento_id", "transitos", "toneladas_cp_suez", "peajes_usd"]]
    .sort_values(["anio_fiscal", "segmento_id"])
    .reset_index(drop=True)
)
fact_transitos.to_csv(OUT_DIR / "fact_transitos.csv", index=False, encoding="utf-8-sig")
print(f"✓ fact_transitos.csv    → {len(fact_transitos)} filas")

# ── fact_predicciones ─────────────────────────────────────────────────────────
fact_predicciones = (
    pred[["anio_fiscal", "segmento", "transitos_predichos"]]
    .copy()
    .assign(segmento_id=lambda df: df["segmento"].map(seg_id))
    [["anio_fiscal", "segmento_id", "transitos_predichos"]]
    .sort_values("segmento_id")
    .reset_index(drop=True)
)
fact_predicciones.to_csv(OUT_DIR / "fact_predicciones.csv", index=False, encoding="utf-8-sig")
print(f"✓ fact_predicciones.csv → {len(fact_predicciones)} filas")

print(f"\nArchivos generados en: {OUT_DIR.resolve()}")
