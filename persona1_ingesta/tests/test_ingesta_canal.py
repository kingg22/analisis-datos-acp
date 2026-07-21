"""Pruebas de regresión para la ingesta oficial de Persona 1."""

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


RUTA_MODULO = Path(__file__).resolve().parents[1] / "src" / "ingesta_canal.py"
SPEC = importlib.util.spec_from_file_location("ingesta_canal", RUTA_MODULO)
ingesta = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ingesta)


class IngestaCanalTests(unittest.TestCase):
    def test_prorrateo_entero_conserva_total(self):
        reparto = ingesta.prorratear_entero(10, pd.Series([1, 1, 1]))
        np.testing.assert_array_equal(reparto, np.array([4, 3, 3]))
        self.assertEqual(int(reparto.sum()), 10)

    def test_prorrateo_rechaza_pesos_negativos(self):
        with self.assertRaisesRegex(ValueError, "pesos.*negativos"):
            ingesta.prorratear_entero(10, pd.Series([2, -1]))

    def test_modos_oficial_y_local_son_equivalentes_por_defecto(self):
        oficial = ingesta.ingestar("oficial")
        local = ingesta.ingestar("local")
        pd.testing.assert_frame_equal(oficial, local)

    def test_totales_procesados_reproducen_indicadores_oficiales(self):
        limpio = ingesta.limpiar(ingesta.ingestar("oficial"))
        serie = ingesta.construir_serie_anual(limpio).set_index("anio_fiscal")
        indicadores = ingesta.leer_desde_local(ingesta.ARCHIVO_INDICADORES).set_index(
            "anio_fiscal"
        )

        for anio, fila in indicadores.iterrows():
            self.assertEqual(
                int(serie.loc[anio, "transitos_totales"]),
                int(fila["transitos_totales"]),
            )
            self.assertEqual(
                int(serie.loc[anio, "toneladas_totales"]),
                round(float(fila["toneladas_pcums_millones"]) * 1_000_000),
            )
            self.assertEqual(
                int(serie.loc[anio, "peajes_totales_usd"]),
                round(float(fila["peajes_millones_balboas"]) * 1_000_000),
            )

    def test_calado_no_publicado_permanece_vacio(self):
        limpio = ingesta.limpiar(ingesta.ingestar("oficial"))
        self.assertTrue(limpio["calado_promedio_pies"].isna().all())

    def test_archivo_local_no_puede_salir_de_raw(self):
        with self.assertRaisesRegex(ValueError, "dentro de data/raw"):
            ingesta.leer_desde_local("../../archivo.csv")


if __name__ == "__main__":
    unittest.main()
