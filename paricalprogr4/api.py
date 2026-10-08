"""Módulo API: acceso, limpieza y procesamiento de los datos de análisis de suelos.

NOTA SOBRE LOS DATOS: en el Excel proporcionado, las columnas de Fósforo (P) y
Potasio (K) perdieron el separador decimal (p. ej. 8,26428936504816 quedó como el
entero 8264289365048160) y varios valores de pH quedaron convertidos en fechas
(p. ej. 4.12 -> 04/12). Por eso se limpian al cargar, con las reglas descritas
en cada función.
"""
import datetime as dt
import math
import unicodedata

import pandas as pd

NAN = float("nan")


# ---------------------------------------------------------------- utilidades
def _normalizar(texto):
    """Minúsculas y sin tildes, para comparar nombres sin problemas."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip()


def _buscar_columna(df, *claves):
    """Devuelve el nombre real de la primera columna que contenga alguna clave."""
    for col in df.columns:
        nombre = _normalizar(col)
        if any(clave in nombre for clave in claves):
            return col
    raise KeyError(f"No se encontró columna con: {claves}. Columnas: {list(df.columns)}")


def columnas_clave(df):
    """Mapea los nombres lógicos a las columnas reales del Excel."""
    return {
        "departamento": _buscar_columna(df, "departamento"),
        "municipio": _buscar_columna(df, "municipio"),
        "cultivo": _buscar_columna(df, "cultivo"),
        "topologia": _buscar_columna(df, "topograf", "topolog"),
        "ph": _buscar_columna(df, "ph agua", "ph "),
        "fosforo": _buscar_columna(df, "fosforo"),
        "potasio": _buscar_columna(df, "potasio"),
    }


# ----------------------------------------------------------------- limpieza
def _texto_a_float(texto):
    """'4,13' o '4.13' -> 4.13 ; '<3,87' -> 3.87 (límite de detección)."""
    texto = texto.strip().lstrip("<").strip().replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return NAN


def _limpiar_ph(v):
    """pH: texto/float normal; fechas solo si el mes es 11 o 12 (4.11 / 4.12).

    Una fecha con mes 1-9 es ambigua (04/09 puede ser 4.09 o 4.90), así que se descarta.
    """
    if isinstance(v, dt.datetime):
        return v.day + v.month / 100 if v.month in (11, 12) else NAN
    if isinstance(v, str):
        v = _texto_a_float(v) if not v.strip().startswith("<") else NAN
    if isinstance(v, (int, float)) and not math.isnan(v) and 0 < v <= 14:
        return float(v)
    return NAN


def _limpiar_entero_sin_decimal(v, digitos_parte_entera):
    """Reconstruye un número cuyo separador decimal se perdió.

    digitos_parte_entera(n_digitos) indica cuántos dígitos tenía la parte entera.
    """
    if isinstance(v, dt.datetime):
        return NAN
    if isinstance(v, str):
        return _texto_a_float(v)
    if isinstance(v, float):
        if math.isnan(v):
            return NAN
        if not (v >= 1000 and v.is_integer()):
            return v  # ya es un decimal real
        v = int(v)
    n = len(str(v))
    return v / 10 ** (n - digitos_parte_entera(n))


def _limpiar_fosforo(v):
    """P (mg/kg): 15-16 dígitos -> 1 entero; 17 dígitos -> 2 enteros; <=2 dígitos se deja igual."""
    def enteros(n):
        return n if n <= 2 else (2 if n >= 17 else 1)
    return _limpiar_entero_sin_decimal(v, enteros)


def _limpiar_potasio(v):
    """K (cmol/kg): se asume 0,xxx (valores típicos < 1), es decir 0 enteros."""
    return _limpiar_entero_sin_decimal(v, lambda n: 0)


# --------------------------------------------------------------------- carga
def cargar_datos(ruta_excel):
    """Lee el Excel (sin que pandas adivine tipos) y deja las columnas numéricas limpias."""
    df = pd.read_excel(ruta_excel, dtype=object)
    c = columnas_clave(df)
    df[c["ph"]] = df[c["ph"]].map(_limpiar_ph)
    df[c["fosforo"]] = df[c["fosforo"]].map(_limpiar_fosforo)
    df[c["potasio"]] = df[c["potasio"]].map(_limpiar_potasio)
    df[c["topologia"]] = df[c["topologia"]].replace(r"^ERROR.*$", "No indica", regex=True)
    return df


# ------------------------------------------------------------------- consulta
def filtrar(df, departamento, municipio, cultivo, n_registros):
    """Filtra por departamento, municipio y cultivo y toma los primeros n registros."""
    c = columnas_clave(df)
    mascara = (
        (df[c["departamento"]].map(_normalizar) == _normalizar(departamento))
        & (df[c["municipio"]].map(_normalizar) == _normalizar(municipio))
        & (df[c["cultivo"]].map(_normalizar) == _normalizar(cultivo))
    )
    return df[mascara].head(n_registros)


def calcular_medianas(df_filtrado, df_original):
    """Agrupa por topología y calcula la mediana de pH, P y K."""
    c = columnas_clave(df_original)
    datos = df_filtrado.copy()
    for var in ("ph", "fosforo", "potasio"):
        datos[c[var]] = pd.to_numeric(datos[c[var]], errors="coerce")

    resumen = (
        datos.groupby([c["departamento"], c["municipio"], c["cultivo"], c["topologia"]])[
            [c["ph"], c["fosforo"], c["potasio"]]
        ]
        .median()
        .reset_index()
    )
    resumen.columns = [
        "Departamento", "Municipio", "Cultivo", "Topología",
        "Mediana pH", "Mediana Fósforo (P)", "Mediana Potasio (K)",
    ]
    return resumen.round(2)
