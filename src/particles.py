"""Generación de conjuntos de partículas para las simulaciones del CIM.

Este módulo se encarga de crear partículas con posición (y opcionalmente
radio y velocidad) distribuidas dentro de un espacio de simulación, para
ser utilizadas como entrada de los algoritmos de búsqueda de vecinos.
"""

from typing import Optional

import numpy as np


def generar_particulas(
    n: int,
    lado: float,
    radio: Optional[float] = None,
    semilla: Optional[int] = None,
) -> np.ndarray:
    """Genera N partículas distribuidas aleatoriamente en un espacio 2D.

    Args:
        n: Cantidad de partículas a generar.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        radio: Radio a asignar a cada partícula. Si es None, no se asigna.
        semilla: Semilla para el generador aleatorio, para reproducibilidad.

    Returns:
        Array de numpy con la información de las partículas generadas
        (posición, y opcionalmente radio).
    """
    raise NotImplementedError
