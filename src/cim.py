"""Implementación del algoritmo Cell Index Method (CIM).

Este módulo contiene la lógica para dividir el espacio de simulación en
celdas y utilizar dicha grilla para encontrar de forma eficiente los pares
de partículas vecinas dentro de un radio de interacción dado.
"""

from typing import Dict, List, Tuple

import numpy as np


def construir_celdas(
    particulas: np.ndarray,
    lado: float,
    m: int,
) -> Dict[Tuple[int, int], List[int]]:
    """Construye la grilla de celdas y asigna cada partícula a su celda.

    Args:
        particulas: Array con la información (posición) de las partículas.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        m: Cantidad de celdas por lado de la grilla.

    Returns:
        Diccionario que mapea el índice (fila, columna) de cada celda a la
        lista de índices de partículas contenidas en ella.
    """
    raise NotImplementedError


def buscar_vecinos_cim(
    particulas: np.ndarray,
    lado: float,
    m: int,
    radio_interaccion: float,
    periodico: bool = False,
) -> Dict[int, List[int]]:
    """Busca los pares de partículas vecinas utilizando el Cell Index Method.

    Args:
        particulas: Array con la información (posición) de las partículas.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        m: Cantidad de celdas por lado de la grilla.
        radio_interaccion: Distancia máxima para considerar dos partículas
            como vecinas.
        periodico: Si es True, se consideran condiciones de borde periódicas.

    Returns:
        Diccionario que mapea el índice de cada partícula a la lista de
        índices de sus partículas vecinas.
    """
    raise NotImplementedError
