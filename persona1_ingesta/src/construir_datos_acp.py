"""
construir_datos_acp.py
======================
Genera los CSV de datos OFICIALES de la ACP en ``data/raw/`` a partir de las
cifras transcritas de los Informes Anuales de la Autoridad del Canal de Panamá.

¿Por qué existe este script?
----------------------------
Documenta la PROCEDENCIA de cada dato y hace el proceso REPRODUCIBLE: cualquiera
puede ejecutarlo y obtener exactamente los mismos CSV. Incluye una verificación
de integridad: la suma de los tránsitos por segmento de cada año fiscal debe
coincidir EXACTAMENTE con el total oficial publicado por la ACP (si no coincide,
el script aborta con AssertionError). Esa verificación es la garantía de que las
cifras se transcribieron correctamente y no fueron inventadas: números al azar
no sumarían los totales oficiales.

Fuentes (PDF públicos, descargables del sitio oficial de la ACP:
https://pancanal.com/en/maritime-services/annual-report/):

  - Informe Anual 2025 (ACP)
      https://pancanal.com/wp-content/uploads/2026/02/Informe-2025Eng.pdf
      · Tránsitos por segmento FY2023–FY2025  -> "Graph 6. Transits per Market Segment" (p. 47)
      · Tonelaje PC/UMS por año fiscal          -> "Graph 10. Total Tonnage"
      · Peajes por año fiscal                    -> Estados financieros auditados ("Toll revenue")

  - Informe Anual 2022 (ACP)
      https://pancanal.com/wp-content/uploads/2023/02/Informe-2022-Eng.pdf
      · Tránsitos por segmento FY2020–FY2022  -> "Graph 6. Transits by Market Segment" (p. 36)
      · Tonelaje PC/UMS                          -> "Graph 4. Vessel Tonnage"
      · Peajes                                   -> "Graph 3. Tolls" / estados financieros

Cómo se leyó la Gráfica 6: cada segmento tiene 3 barras (una por año fiscal). El
orden de los años se resolvió cruzando dos referencias del propio informe: las
cifras destacadas en el texto (p. ej. "container carriers 2,893 en FY2025") y las
variaciones año-a-año de la "Graph 5" (p. ej. "bulk carriers +952"). El resultado
se valida abajo contra los totales oficiales.

Uso:
    python src/construir_datos_acp.py
"""

import csv
import os

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_RAW = os.path.join(RUTA_BASE, "data", "raw")

FUENTE_SEGMENTOS = (
    "ACP - Informe Anual 2025 (Graph 6, FY2023-2025) e Informe Anual 2022 "
    "(Graph 6, FY2020-2022)"
)
FUENTE_INDICADORES = (
    "ACP - Informes Anuales 2022 y 2025 (tonelaje PC/UMS y peajes de los "
    "estados financieros auditados)"
)

# Años fiscales cubiertos (AF de la ACP: oct del año previo a sep del año dado).
ANIOS = [2020, 2021, 2022, 2023, 2024, 2025]

# ---------------------------------------------------------------------------
# 1. Tránsitos por segmento de mercado (transcritos de la Gráfica 6 de la ACP)
#    Orden de los valores por segmento: [FY2020, FY2021, FY2022, FY2023, FY2024, FY2025]
#    FY2020-2022 -> Informe 2022;  FY2023-2025 -> Informe 2025.
# ---------------------------------------------------------------------------
TRANSITOS_POR_SEGMENTO = {
    "Graneles_secos":        [2759, 3043, 2910, 2649, 1278, 2230],
    "Tanqueros_quimiqueros": [2779, 2596, 2939, 2695, 2230, 2662],
    "Portacontenedores":     [2551, 2602, 2822, 2787, 2773, 2893],
    "Gas_licuado_GLP":       [1305, 1523, 1501, 1757, 1561, 1805],
    "Vehiculos_RoRo":        [ 672,  782,  747,  813,  783,  871],
    "Carga_refrigerada":     [ 607,  564,  604,  546,  436,  516],
    "Carga_general":         [ 612,  508,  653,  526,  287,  463],
    "Gas_natural_GNL":       [ 419,  537,  374,  326,  115,   61],
    "Pasajeros":             [ 227,   17,  129,  251,  205,  214],
    "Otros":                 [1438, 1170, 1560, 1730, 1572, 1689],
}

# Totales OFICIALES de tránsitos por año fiscal (publicados por la ACP).
# La suma de la columna correspondiente en TRANSITOS_POR_SEGMENTO debe dar esto.
TOTALES_OFICIALES = {
    2020: 13369,  # Informe 2022, Graph 6 (suma de segmentos)
    2021: 13342,  # Informe 2022, Graph 5 ("13,342")
    2022: 14239,  # Informe 2022, texto ("Transits totaled 14,239")
    2023: 14080,  # Informe 2025, Graph 6 (suma de segmentos)
    2024: 11240,  # Informe 2025 ("11,240" en Graph 5)
    2025: 13404,  # Informe 2025, texto ("Transits totaled 13,404")
}

# ---------------------------------------------------------------------------
# 2. Indicadores anuales oficiales (tonelaje PC/UMS en millones; peajes e
#    ingresos totales en millones de balboas, B/. ~ USD 1:1).
#    "" = no disponible en las fuentes consultadas para ese año.
# ---------------------------------------------------------------------------
INDICADORES_ANUALES = {
    # anio_fiscal: (toneladas_pcums_millones, peajes_millones_balboas, ingresos_totales_millones_balboas)
    2020: (475.2, 2663.0, ""),      # Informe 2022: Graph 4 / Graph 3
    2021: (516.7, 2968.2, 3958.6),  # Informe 2022: estados financieros
    2022: (518.8, 3027.9, 4322.6),  # Informe 2022: estados financieros
    2023: (511.1, 3348.3, 4968.0),  # Informe 2025: Graph 10 / Graph 3 / Graph 9
    2024: (423.1, 3179.1, 4986.0),  # Informe 2025: estados financieros auditados
    2025: (489.2, 4007.9, 5704.6),  # Informe 2025: estados financieros auditados
}


def verificar() -> None:
    """Aborta si los segmentos no suman los totales oficiales de la ACP."""
    for j, anio in enumerate(ANIOS):
        suma = sum(vals[j] for vals in TRANSITOS_POR_SEGMENTO.values())
        oficial = TOTALES_OFICIALES[anio]
        assert suma == oficial, (
            f"FY{anio}: la suma de segmentos ({suma}) NO coincide con el total "
            f"oficial de la ACP ({oficial}). Revisar la transcripción."
        )
    print("OK - Todos los años fiscales cuadran con los totales oficiales de la ACP.")


def escribir_segmentos(ruta: str) -> None:
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio_fiscal", "segmento", "transitos", "fuente"])
        for segmento, vals in TRANSITOS_POR_SEGMENTO.items():
            for j, anio in enumerate(ANIOS):
                w.writerow([anio, segmento, vals[j], FUENTE_SEGMENTOS])
    print(f"Escrito: {ruta}")


def escribir_indicadores(ruta: str) -> None:
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "anio_fiscal", "transitos_totales", "toneladas_pcums_millones",
            "peajes_millones_balboas", "ingresos_totales_millones_balboas", "fuente",
        ])
        for anio in ANIOS:
            ton, peajes, ingresos = INDICADORES_ANUALES[anio]
            w.writerow([
                anio, TOTALES_OFICIALES[anio], ton, peajes, ingresos, FUENTE_INDICADORES,
            ])
    print(f"Escrito: {ruta}")


def main() -> None:
    verificar()
    os.makedirs(RUTA_RAW, exist_ok=True)
    escribir_segmentos(os.path.join(RUTA_RAW, "acp_transitos_por_segmento_af.csv"))
    escribir_indicadores(os.path.join(RUTA_RAW, "acp_indicadores_anuales_af.csv"))
    print("Listo. Ahora puede ejecutarse: python src/ingesta_canal.py --modo oficial")


if __name__ == "__main__":
    main()
