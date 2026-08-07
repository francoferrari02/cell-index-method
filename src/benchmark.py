"""Experimentos de desempeño del Cell Index Method.

Este módulo orquesta la ejecución de benchmarks para comparar los tiempos
de ejecución del CIM contra el método de fuerza bruta, variando parámetros
como la cantidad de partículas (N) y la cantidad de celdas por lado (M).
"""

from typing import Any, Dict, List

import numpy as np


def correr_benchmark_tiempo_vs_m(
    n: int,
    lado: float,
    radio_interaccion: float,
    valores_m: List[int],
    repeticiones: int = 1,
) -> Dict[str, Any]:
    """Mide el tiempo de ejecución del CIM en función de M, con N fijo.

    Args:
        n: Cantidad de partículas a utilizar.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        radio_interaccion: Distancia máxima para considerar dos partículas
            como vecinas.
        valores_m: Lista de valores de M (celdas por lado) a evaluar.
        repeticiones: Cantidad de repeticiones por cada valor de M, para
            promediar los tiempos medidos.

    Returns:
        Diccionario con los resultados del experimento (tiempos medidos
        por cada valor de M).
    """
    raise NotImplementedError


def correr_benchmark_tiempo_vs_n(
    valores_n: List[int],
    lado: float,
    radio_interaccion: float,
    m: int,
    repeticiones: int = 1,
) -> Dict[str, Any]:
    """Mide el tiempo de ejecución del CIM y fuerza bruta en función de N.

    Args:
        valores_n: Lista de valores de N (cantidad de partículas) a evaluar.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        radio_interaccion: Distancia máxima para considerar dos partículas
            como vecinas.
        m: Cantidad de celdas por lado a utilizar para el CIM.
        repeticiones: Cantidad de repeticiones por cada valor de N, para
            promediar los tiempos medidos.

    Returns:
        Diccionario con los resultados del experimento (tiempos medidos
        por cada valor de N, tanto para CIM como para fuerza bruta).
    """
    raise NotImplementedError
