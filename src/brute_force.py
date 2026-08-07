"""Búsqueda de partículas vecinas por fuerza bruta.

Este módulo implementa el método de referencia de complejidad O(N^2) para
la búsqueda de pares de partículas vecinas, utilizado como baseline para
comparar el desempeño del Cell Index Method (CIM).
"""

from typing import Dict, List

import numpy as np


def buscar_vecinos_fuerza_bruta(
    particulas: np.ndarray,
    lado: float,
    radio_interaccion: float,
    periodico: bool = False,
) -> Dict[int, List[int]]:
    """Busca los pares de partículas vecinas comparando todos contra todos.

    Args:
        particulas: Array con la información (posición) de las partículas.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        radio_interaccion: Distancia máxima para considerar dos partículas
            como vecinas.
        periodico: Si es True, se consideran condiciones de borde periódicas.

    Returns:
        Diccionario que mapea el índice de cada partícula a la lista de
        índices de sus partículas vecinas.
    """
    raise NotImplementedError
