"""
Genera CSV combinado para Power BI Web (una sola tabla, sin relaciones)
"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[2] / "data" / "powerbi"

transitos = pd.read_csv(BASE / "fact_transitos.csv")
segmentos = pd.read_csv(BASE / "dim_segmento.csv")
tiempo = pd.read_csv(BASE / "dim_tiempo.csv")
predicciones = pd.read_csv(BASE / "fact_predicciones.csv")

# Combinar todo en una sola tabla plana
df = transitos.merge(segmentos, on="segmento_id").merge(tiempo, on="anio_fiscal")

# Columnas amigables para Q&A
df = df[[
    "anio_fiscal", "etiqueta", "periodo", "es_sequia", "precio_barril_usd_prom",
    "segmento_id", "segmento", "nombre_display", "categoria",
    "transitos", "toneladas_cp_suez", "peajes_usd",
]]

output = BASE / "datos_powerbi_completos.csv"
df.to_csv(output, index=False)
print(f"Creado: {output} ({len(df)} filas)")
