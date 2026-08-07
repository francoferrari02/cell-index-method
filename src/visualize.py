"""Visualización de partículas y resultados de las simulaciones.

Este módulo contiene funciones para graficar la disposición espacial de las
partículas, resaltar las relaciones de vecindad encontradas y visualizar los
resultados de los benchmarks (tiempo vs. N, tiempo vs. M).
"""

from typing import Dict, List, Optional

import numpy as np


def graficar_particulas(
    particulas: np.ndarray,
    lado: float,
    vecinos: Optional[Dict[int, List[int]]] = None,
    m: Optional[int] = None,
    path_salida: Optional[str] = None,
) -> None:
    """Grafica las partículas en el espacio de simulación.

    Args:
        particulas: Array con la información (posición) de las partículas.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        vecinos: Diccionario opcional de vecinos a resaltar en el gráfico.
        m: Cantidad de celdas por lado, para dibujar la grilla del CIM.
        path_salida: Ruta donde guardar la figura. Si es None, se muestra
            en pantalla.
    """
    raise NotImplementedError
