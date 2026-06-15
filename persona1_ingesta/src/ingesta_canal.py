"""
ingesta_canal.py
================
Módulo de ingesta de datos públicos de tránsitos del Canal de Panamá.

Responsable: PERSONA 1 - Ingesta de Datos (Fuente 1)
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Este módulo descarga, limpia y estructura datos públicos de tránsitos
del Canal de Panamá publicados por la Autoridad del Canal de Panamá (ACP)
a través del Portal de Datos Abiertos de Panamá (datosabiertos.gob.pa)
y el Instituto Nacional de Estadística y Censo (INEC).

FUENTES PÚBLICAS:
  1. Portal de Datos Abiertos de Panamá  -> https://www.datosabiertos.gob.pa
  2. INEC (Sección Transporte/Canal)      -> https://www.inec.gob.pa

NOTA IMPORTANTE:
  Las URLs de descarga directa (CSV) de los portales públicos cambian
  con cada actualización. El script soporta dos modos:
    - modo "url"  : descarga el CSV desde una URL pública configurada.
    - modo "local": lee un CSV ya descargado manualmente en data/raw/.
  Mientras el equipo confirma la URL definitiva, se incluye un generador
  de datos de muestra (data_muestra) basado en cifras oficiales reales
  publicadas por la ACP, para que Persona 3, 4 y 5 puedan avanzar.
"""

import os
import io
import logging
from datetime import datetime

import numpy as np
import pandas as pd
import requests

# ----------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------
RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_RAW = os.path.join(RUTA_BASE, "data", "raw")
RUTA_PROCESSED = os.path.join(RUTA_BASE, "data", "processed")

# URL de descarga directa de la fuente pública (rellenar cuando se confirme).
# Ejemplo de patrón típico del portal de Datos Abiertos de Panamá:
URL_CANAL_CSV = os.getenv("URL_CANAL_CSV", "")  # configurar por variable de entorno

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("ingesta_canal")


# ----------------------------------------------------------------------
# 1. Ingesta
# ----------------------------------------------------------------------
def descargar_desde_url(url: str, timeout: int = 30) -> pd.DataFrame:
    """Descarga un CSV público desde una URL y lo devuelve como DataFrame."""
    log.info("Descargando datos desde URL: %s", url)
    respuesta = requests.get(url, timeout=timeout)
    respuesta.raise_for_status()
    df = pd.read_csv(io.StringIO(respuesta.content.decode("utf-8", errors="replace")))
    log.info("Descarga completada: %d filas, %d columnas", df.shape[0], df.shape[1])
    return df


def leer_desde_local(nombre_archivo: str) -> pd.DataFrame:
    """Lee un CSV descargado manualmente y guardado en data/raw/."""
    ruta = os.path.join(RUTA_RAW, nombre_archivo)
    log.info("Leyendo archivo local: %s", ruta)
    df = pd.read_csv(ruta)
    log.info("Lectura completada: %d filas, %d columnas", df.shape[0], df.shape[1])
    return df


def data_muestra() -> pd.DataFrame:
    """
    Genera un dataset de muestra mensual de tránsitos del Canal de Panamá.

    Las cifras base provienen de estadísticas oficiales reales de la ACP:
      - AF2024: 11,240 tránsitos totales (alto + bajo calado).
      - Segmentos principales AF2025: portacontenedores (2,893),
        graneleros (2,230), quimiqueros (2,218).
    El generador construye una serie temporal mensual coherente con
    estacionalidad y tendencia, útil para desarrollo y pruebas del
    pipeline mientras se confirma la fuente CSV definitiva.
    """
    log.info("Generando dataset de MUESTRA basado en cifras oficiales ACP")
    rng = np.random.default_rng(42)

    # Rango: octubre 2019 (AF2020) hasta diciembre 2025
    fechas = pd.date_range(start="2019-10-01", end="2025-12-01", freq="MS")

    segmentos = {
        "Portacontenedores": 240,
        "Graneles_secos": 185,
        "Quimiqueros": 185,
        "Tanqueros": 120,
        "Carga_refrigerada": 70,
        "Vehiculos_RoRo": 55,
        "Gas_licuado_GLP": 45,
        "Gas_natural_GNL": 30,
        "Pasajeros": 15,
        "Otros": 40,
    }

    filas = []
    for i, fecha in enumerate(fechas):
        # Tendencia leve a la baja en 2023 (crisis de sequía) y recuperación 2025
        factor_sequia = 0.72 if fecha.year == 2023 and fecha.month >= 6 else 1.0
        factor_sequia = 0.78 if (fecha.year == 2024 and fecha.month <= 5) else factor_sequia
        factor_recuperacion = 1.18 if fecha.year == 2025 else 1.0
        # Estacionalidad: mayor tránsito en temporada alta (oct-ene)
        estacional = 1.0 + 0.08 * np.sin((fecha.month / 12) * 2 * np.pi)

        for segmento, base in segmentos.items():
            ruido = rng.normal(1.0, 0.06)
            transitos = int(
                base * estacional * factor_sequia * factor_recuperacion * ruido
            )
            # Calado y tonelaje promedio aproximados por segmento
            calado = round(rng.normal(40, 4), 1)
            toneladas_cp_suez = int(transitos * rng.normal(45000, 8000))
            peajes_usd = int(transitos * rng.normal(280000, 40000))

            filas.append(
                {
                    "fecha": fecha,
                    "anio": fecha.year,
                    "mes": fecha.month,
                    "anio_fiscal": fecha.year + 1 if fecha.month >= 10 else fecha.year,
                    "segmento": segmento,
                    "transitos": max(transitos, 0),
                    "calado_promedio_pies": calado,
                    "toneladas_cp_suez": max(toneladas_cp_suez, 0),
                    "peajes_usd": max(peajes_usd, 0),
                }
            )

    df = pd.DataFrame(filas)
    log.info("Dataset de muestra generado: %d filas", df.shape[0])
    return df


def ingestar(modo: str = "muestra", nombre_archivo: str = "transitos_canal.csv") -> pd.DataFrame:
    """
    Punto de entrada de la ingesta.

    Parámetros
    ----------
    modo : {"url", "local", "muestra"}
        - "url"     : descarga desde URL_CANAL_CSV.
        - "local"   : lee data/raw/<nombre_archivo>.
        - "muestra" : genera datos de muestra (default, para desarrollo).
    """
    if modo == "url":
        if not URL_CANAL_CSV:
            raise ValueError(
                "URL_CANAL_CSV no configurada. Definir variable de entorno "
                "o usar modo='local' / modo='muestra'."
            )
        return descargar_desde_url(URL_CANAL_CSV)
    if modo == "local":
        return leer_desde_local(nombre_archivo)
    if modo == "muestra":
        return data_muestra()
    raise ValueError(f"Modo no válido: {modo}")


# ----------------------------------------------------------------------
# 2. Limpieza y estructuración
# ----------------------------------------------------------------------
def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza y estandarización del dataset de tránsitos.

    Operaciones:
      - Normaliza nombres de columnas (minúsculas, sin espacios).
      - Convierte 'fecha' a tipo datetime.
      - Elimina filas totalmente vacías y duplicados.
      - Maneja valores nulos en columnas numéricas (relleno con 0).
      - Valida que no existan tránsitos negativos.
      - Ordena cronológicamente.
    """
    log.info("Iniciando limpieza. Filas de entrada: %d", df.shape[0])
    df = df.copy()

    # Normalizar nombres de columnas
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "", regex=True)
    )

    # Convertir fecha
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # Eliminar filas y duplicados
    antes = df.shape[0]
    df = df.dropna(how="all")
    df = df.drop_duplicates()
    log.info("Eliminadas %d filas vacías/duplicadas", antes - df.shape[0])

    # Manejo de nulos en numéricas
    columnas_numericas = df.select_dtypes(include=[np.number]).columns
    nulos = df[columnas_numericas].isna().sum().sum()
    if nulos:
        log.info("Rellenando %d valores nulos numéricos con 0", nulos)
        df[columnas_numericas] = df[columnas_numericas].fillna(0)

    # Validar tránsitos no negativos
    if "transitos" in df.columns:
        negativos = (df["transitos"] < 0).sum()
        if negativos:
            log.warning("Corrigiendo %d tránsitos negativos a 0", negativos)
            df.loc[df["transitos"] < 0, "transitos"] = 0

    # Ordenar
    if "fecha" in df.columns:
        df = df.sort_values("fecha").reset_index(drop=True)

    log.info("Limpieza completada. Filas de salida: %d", df.shape[0])
    return df


def construir_serie_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega los tránsitos por mes (todos los segmentos) para alimentar
    el análisis de tendencias (Persona 3) y el modelo predictivo (Persona 4).
    """
    if "fecha" not in df.columns or "transitos" not in df.columns:
        log.warning("No se puede construir serie mensual: faltan columnas clave")
        return pd.DataFrame()

    serie = (
        df.groupby(pd.Grouper(key="fecha", freq="MS"))["transitos"]
        .sum()
        .reset_index()
        .rename(columns={"transitos": "transitos_totales"})
    )
    log.info("Serie mensual construida: %d meses", serie.shape[0])
    return serie


# ----------------------------------------------------------------------
# 3. Persistencia
# ----------------------------------------------------------------------
def guardar(df: pd.DataFrame, nombre: str) -> str:
    """Guarda un DataFrame en data/processed/ como CSV. Devuelve la ruta."""
    os.makedirs(RUTA_PROCESSED, exist_ok=True)
    ruta = os.path.join(RUTA_PROCESSED, nombre)
    df.to_csv(ruta, index=False, encoding="utf-8")
    log.info("Archivo guardado: %s (%d filas)", ruta, df.shape[0])
    return ruta


# ----------------------------------------------------------------------
# 4. Orquestación
# ----------------------------------------------------------------------
def main(modo: str = "muestra") -> None:
    """Ejecuta el flujo completo de ingesta de la Fuente 1."""
    log.info("=== INICIO INGESTA FUENTE 1: CANAL DE PANAMÁ ===")
    log.info("Modo de ingesta: %s | Timestamp: %s", modo, datetime.now().isoformat())

    df_crudo = ingestar(modo=modo)
    guardar(df_crudo, "canal_crudo.csv")

    df_limpio = limpiar(df_crudo)
    ruta_limpio = guardar(df_limpio, "canal_limpio.csv")

    serie = construir_serie_mensual(df_limpio)
    if not serie.empty:
        guardar(serie, "canal_serie_mensual.csv")

    log.info("=== INGESTA COMPLETADA ===")
    log.info("Entregable principal para el pipeline: %s", ruta_limpio)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingesta de datos del Canal de Panamá")
    parser.add_argument(
        "--modo",
        default="muestra",
        choices=["url", "local", "muestra"],
        help="Fuente de ingesta (default: muestra)",
    )
    args = parser.parse_args()
    main(modo=args.modo)
