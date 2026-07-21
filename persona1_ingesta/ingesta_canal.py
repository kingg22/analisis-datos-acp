"""
ingesta_canal.py
================
Módulo de ingesta de datos públicos de tránsitos del Canal de Panamá.

Responsable: PERSONA 1 - Ingesta de Datos (Fuente 1)
Proyecto: Grupo 8 - Análisis de Datos del Canal de Panamá
Curso: Segundo Parcial - Pipeline + Visualización

Este módulo carga, limpia y estructura datos públicos de tránsitos del Canal
de Panamá publicados por la Autoridad del Canal de Panamá (ACP).

GRANULARIDAD: ANUAL (año fiscal de la ACP, oct–sep). La ACP publica el desglose
por segmento de mercado a nivel anual, así que el proyecto trabaja con datos
anuales reales — sin inventar una distribución mensual.

FUENTE PÚBLICA REAL (modo por defecto "oficial"):
  Los tránsitos por segmento y los indicadores anuales (tonelaje PC/UMS, peajes)
  provienen de los INFORMES ANUALES OFICIALES de la ACP, guardados en data/raw/
  como CSV por el script src/construir_datos_acp.py (que cita cada cifra y
  verifica que sumen los totales oficiales). Fuentes:
    - Informe Anual 2025 -> años fiscales 2023, 2024 y 2025.
    - Informe Anual 2022 -> años fiscales 2020, 2021 y 2022.

MODO ADICIONAL:
    - "local" : lee un CSV de data/raw/; acepta --archivo para seleccionarlo.
"""

import os
import logging
from datetime import datetime

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------
RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_RAW = os.path.join(RUTA_BASE, "data", "raw")
RUTA_PROCESSED = os.path.join(RUTA_BASE, "data", "processed")

# Archivos de datos oficiales reales (ver docstring y docs/FUENTE_DATOS.md).
ARCHIVO_SEGMENTOS = "acp_transitos_por_segmento_af.csv"
ARCHIVO_INDICADORES = "acp_indicadores_anuales_af.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("ingesta_canal")


# ----------------------------------------------------------------------
# 1. Ingesta
# ----------------------------------------------------------------------
def leer_desde_local(nombre_archivo: str) -> pd.DataFrame:
    """Lee un CSV guardado en data/raw/."""
    ruta = os.path.abspath(os.path.join(RUTA_RAW, nombre_archivo))
    if os.path.commonpath([ruta, os.path.abspath(RUTA_RAW)]) != os.path.abspath(RUTA_RAW):
        raise ValueError("El archivo local debe estar dentro de data/raw/")
    log.info("Leyendo archivo local: %s", ruta)
    df = pd.read_csv(ruta)
    log.info("Lectura completada: %d filas, %d columnas", df.shape[0], df.shape[1])
    return df


def prorratear_entero(total: int, pesos: pd.Series) -> np.ndarray:
    """Prorratea un total entero conservándolo exactamente (mayores residuos)."""
    valores = pesos.to_numpy(dtype=float)
    if total < 0:
        raise ValueError("El total a prorratear no puede ser negativo")
    if (valores < 0).any():
        raise ValueError("Los pesos del prorrateo no pueden ser negativos")
    if valores.sum() <= 0:
        return np.zeros(len(valores), dtype=np.int64)

    cuotas = valores / valores.sum() * int(total)
    reparto = np.floor(cuotas).astype(np.int64)
    faltantes = int(total - reparto.sum())
    if faltantes:
        residuos = cuotas - reparto
        orden = np.argsort(-residuos, kind="stable")
        reparto[orden[:faltantes]] += 1
    return reparto


def construir_tabla_oficial(seg: pd.DataFrame, ind: pd.DataFrame) -> pd.DataFrame:
    """Combina las tablas oficiales y conserva exactamente sus totales anuales."""
    columnas_segmentos = {"anio_fiscal", "segmento", "transitos"}
    columnas_indicadores = {
        "anio_fiscal", "transitos_totales", "toneladas_pcums_millones",
        "peajes_millones_balboas",
    }
    if not columnas_segmentos.issubset(seg.columns):
        faltantes = sorted(columnas_segmentos - set(seg.columns))
        raise ValueError(f"Faltan columnas en el CSV de segmentos: {faltantes}")
    if not columnas_indicadores.issubset(ind.columns):
        faltantes = sorted(columnas_indicadores - set(ind.columns))
        raise ValueError(f"Faltan columnas en el CSV de indicadores: {faltantes}")

    ind = ind.set_index("anio_fiscal")
    filas = []
    for anio_fiscal, grupo in seg.groupby("anio_fiscal", sort=True):
        if anio_fiscal not in ind.index:
            raise ValueError(f"No hay indicadores oficiales para AF{anio_fiscal}")
        total_segmentos = int(grupo["transitos"].sum())
        total_publicado = int(ind.loc[anio_fiscal, "transitos_totales"])
        if total_segmentos != total_publicado:
            raise ValueError(
                f"AF{anio_fiscal}: segmentos={total_segmentos}, "
                f"total oficial={total_publicado}"
            )

        toneladas_millones = ind.loc[anio_fiscal, "toneladas_pcums_millones"]
        toneladas_af = int(round(float(toneladas_millones) * 1_000_000))
        peajes_millones = ind.loc[anio_fiscal, "peajes_millones_balboas"]
        peajes_af = (
            int(round(float(peajes_millones) * 1_000_000))
            if pd.notna(peajes_millones)
            else 0
        )
        toneladas_segmento = prorratear_entero(toneladas_af, grupo["transitos"])
        peajes_segmento = prorratear_entero(peajes_af, grupo["transitos"])

        for (_, r), toneladas, peajes in zip(
            grupo.iterrows(), toneladas_segmento, peajes_segmento,
        ):
            filas.append(
                {
                    "anio_fiscal": int(anio_fiscal),
                    "segmento": r["segmento"],
                    "transitos": int(r["transitos"]),
                    # La ACP no publica calado promedio por segmento.
                    "calado_promedio_pies": np.nan,
                    "toneladas_cp_suez": int(toneladas),
                    "peajes_usd": int(peajes),
                }
            )

    return pd.DataFrame(filas).sort_values(["anio_fiscal", "segmento"]).reset_index(drop=True)


def cargar_datos_oficiales() -> pd.DataFrame:
    """
    Construye la tabla ANUAL por segmento a partir de los datos OFICIALES
    reales de la ACP guardados en data/raw/.

    Proceso:
      1. Lee los tránsitos anuales por segmento (cifras oficiales verificadas).
      2. Lee los indicadores anuales (tonelaje PC/UMS y peajes oficiales).
      3. Reparte el tonelaje y los peajes anuales oficiales de cada año fiscal
         de forma proporcional a los tránsitos de cada segmento (prorrateo de una
         cifra real; la suma por año fiscal reproduce el total oficial).

    Devuelve un DataFrame con una fila por (anio_fiscal, segmento).
    """
    log.info("Cargando datos OFICIALES de la ACP desde data/raw/")
    for archivo in (ARCHIVO_SEGMENTOS, ARCHIVO_INDICADORES):
        if not os.path.exists(os.path.join(RUTA_RAW, archivo)):
            raise FileNotFoundError(
                f"No se encontró data/raw/{archivo}. "
                "Genéralo primero con: python src/construir_datos_acp.py"
            )
    seg = leer_desde_local(ARCHIVO_SEGMENTOS)
    ind = leer_desde_local(ARCHIVO_INDICADORES)
    df = construir_tabla_oficial(seg, ind)
    log.info(
        "Dataset oficial construido: %d filas (%d años fiscales, %d segmentos)",
        df.shape[0], seg["anio_fiscal"].nunique(), seg["segmento"].nunique(),
    )
    return df


def ingestar(modo: str = "oficial", nombre_archivo: str = ARCHIVO_SEGMENTOS) -> pd.DataFrame:
    """
    Punto de entrada de la ingesta.

    Parámetros
    ----------
    modo : {"oficial", "local"}
        - "oficial" : construye la serie anual desde los datos oficiales de la ACP
                      guardados en data/raw/ (default).
        - "local"   : lee data/raw/<nombre_archivo>.
    """
    if modo in ("muestra", "sintetica", "mensual"):
        log.warning(
            "El modo '%s' ya no existe; el proyecto usa datos anuales oficiales. "
            "Usando modo 'oficial'.", modo,
        )
        modo = "oficial"
    if modo == "oficial":
        return cargar_datos_oficiales()
    if modo == "local":
        df = leer_desde_local(nombre_archivo)
        if os.path.basename(nombre_archivo) == ARCHIVO_SEGMENTOS:
            indicadores = leer_desde_local(ARCHIVO_INDICADORES)
            return construir_tabla_oficial(df, indicadores)
        return df
    raise ValueError(f"Modo no válido: {modo}")


# ----------------------------------------------------------------------
# 2. Limpieza y estructuración
# ----------------------------------------------------------------------
def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza y estandarización del dataset anual de tránsitos.

    Operaciones:
      - Normaliza nombres de columnas (minúsculas, sin espacios).
      - Elimina filas totalmente vacías y duplicados.
      - Maneja nulos numéricos con 0, salvo el calado no publicado por la ACP.
      - Valida que no existan tránsitos negativos.
      - Ordena por año fiscal y segmento.
    """
    log.info("Iniciando limpieza. Filas de entrada: %d", df.shape[0])
    df = df.copy()

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "", regex=True)
    )

    antes = df.shape[0]
    df = df.dropna(how="all")
    df = df.drop_duplicates()
    log.info("Eliminadas %d filas vacías/duplicadas", antes - df.shape[0])

    columnas_numericas = df.select_dtypes(include=[np.number]).columns.difference(
        ["calado_promedio_pies"]
    )
    nulos = df[columnas_numericas].isna().sum().sum()
    if nulos:
        log.info("Rellenando %d valores nulos numéricos con 0", nulos)
        df[columnas_numericas] = df[columnas_numericas].fillna(0)

    if "transitos" in df.columns:
        negativos = (df["transitos"] < 0).sum()
        if negativos:
            log.warning("Corrigiendo %d tránsitos negativos a 0", negativos)
            df.loc[df["transitos"] < 0, "transitos"] = 0

    orden = [c for c in ("anio_fiscal", "segmento") if c in df.columns]
    if orden:
        df = df.sort_values(orden).reset_index(drop=True)

    log.info("Limpieza completada. Filas de salida: %d", df.shape[0])
    return df


def construir_serie_anual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega los tránsitos por año fiscal (todos los segmentos) para alimentar
    el análisis de tendencias (Persona 3) y el modelo predictivo (Persona 4).
    """
    if "anio_fiscal" not in df.columns or "transitos" not in df.columns:
        log.warning("No se puede construir serie anual: faltan columnas clave")
        return pd.DataFrame()

    agregaciones = {"transitos_totales": ("transitos", "sum")}
    if "toneladas_cp_suez" in df.columns:
        agregaciones["toneladas_totales"] = ("toneladas_cp_suez", "sum")
    if "peajes_usd" in df.columns:
        agregaciones["peajes_totales_usd"] = ("peajes_usd", "sum")

    serie = (
        df.groupby("anio_fiscal", as_index=False)
        .agg(**agregaciones)
        .sort_values("anio_fiscal")
        .reset_index(drop=True)
    )
    log.info("Serie anual construida: %d años fiscales", serie.shape[0])
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
def main(modo: str = "oficial", nombre_archivo: str = ARCHIVO_SEGMENTOS) -> None:
    """Ejecuta el flujo completo de ingesta de la Fuente 1."""
    log.info("=== INICIO INGESTA FUENTE 1: CANAL DE PANAMÁ ===")
    log.info("Modo de ingesta: %s | Timestamp: %s", modo, datetime.now().isoformat())

    df_crudo = ingestar(modo=modo, nombre_archivo=nombre_archivo)
    guardar(df_crudo, "canal_crudo.csv")

    df_limpio = limpiar(df_crudo)
    ruta_limpio = guardar(df_limpio, "canal_limpio.csv")

    serie = construir_serie_anual(df_limpio)
    if not serie.empty:
        guardar(serie, "canal_serie_anual.csv")

    log.info("=== INGESTA COMPLETADA ===")
    log.info("Entregable principal para el pipeline: %s", ruta_limpio)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingesta de datos del Canal de Panamá")
    parser.add_argument(
        "--modo",
        default="oficial",
        choices=["oficial", "local"],
        help="Fuente de ingesta (default: oficial = datos reales de la ACP)",
    )
    parser.add_argument(
        "--archivo",
        default=ARCHIVO_SEGMENTOS,
        help="CSV dentro de data/raw/ usado por --modo local",
    )
    args = parser.parse_args()
    main(modo=args.modo, nombre_archivo=args.archivo)
