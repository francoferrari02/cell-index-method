"""Utilidades de entrada/salida para los archivos del TP.

Este módulo maneja la lectura de los archivos de configuración estática
(cantidad de partículas, lado, radio de interacción, etc.) y dinámica
(posiciones y velocidades por partícula), así como la escritura de los
resultados obtenidos (vecinos encontrados, tiempos de ejecución, etc.).
"""

from typing import Any, Dict, List

import numpy as np


def leer_archivo_estatico(path: str) -> Dict[str, Any]:
    """Lee el archivo estático de configuración de la simulación.

    Args:
        path: Ruta al archivo estático de entrada.

    Returns:
        Diccionario con los parámetros de configuración leídos (por ejemplo,
        cantidad de partículas, lado del espacio, radio de interacción).
    """
    raise NotImplementedError


def leer_archivo_dinamico(path: str) -> np.ndarray:
    """Lee el archivo dinámico con la posición (y velocidad) de las partículas.

    Args:
        path: Ruta al archivo dinámico de entrada.

    Returns:
        Array de numpy con la información de las partículas leídas.
    """
    raise NotImplementedError


def escribir_resultado_vecinos(path: str, vecinos: Dict[int, List[int]]) -> None:
    """Escribe a disco el resultado de la búsqueda de vecinos.

    Args:
        path: Ruta del archivo de salida a generar.
        vecinos: Diccionario que mapea el índice de cada partícula a la
            lista de índices de sus partículas vecinas.
    """
    raise NotImplementedError
