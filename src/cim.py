"""Implementación del algoritmo Cell Index Method (CIM).

Este módulo divide el espacio de simulación en una grilla de M x M celdas
y utiliza dicha grilla para encontrar de forma eficiente los pares de
partículas vecinas, según el criterio de distancia BORDE-BORDE:

    distancia_borde_borde(i, j) = ||centro_i - centro_j|| - (r_i + r_j)
    i, j son vecinas si distancia_borde_borde(i, j) < rc

Elección de M_max con partículas de radio no nulo
---------------------------------------------------
El criterio clásico del CIM para partículas puntuales exige L/M > rc, de
forma que alcance con revisar la celda propia y las 8 celdas vecinas para
encontrar todos los posibles vecinos dentro del radio de interacción rc.

Acá las partículas tienen radio, y el criterio de vecindad es sobre la
distancia BORDE-BORDE, no centro-centro. Dos partículas pueden interactuar
(distancia borde-borde < rc) con sus CENTROS separados hasta
rc + r_i + r_j, que en el peor caso (ambas con el radio máximo del
sistema) es rc + 2*r_max. Por eso se define un radio de interacción
efectivo:

    rc_efectivo = rc + 2 * r_max

y se exige L/M > rc_efectivo (equivalentemente, M < L / rc_efectivo) para
garantizar que ningún par de partículas vecinas pueda quedar en celdas
no adyacentes. De ahí:

    M_max = floor(L / rc_efectivo)

Con M <= M_max, dos partículas vecinas siempre caen en la misma celda o en
celdas adyacentes (incluidas las diagonales), por lo que basta con
comparar cada partícula contra las de su celda y las 8 celdas vecinas.
Nota: M=1 siempre es válido (una única celda, equivalente a fuerza bruta),
así que en la práctica se toma M_max = max(1, floor(L / rc_efectivo)).

Recorrido "hacia adelante" para no duplicar pares
---------------------------------------------------
Para cada celda se comparan sus partículas contra sí misma (pares i < j
dentro de la celda) y contra las celdas vecinas en un semi-stencil de 2D
{derecha, arriba, arriba-derecha, arriba-izquierda}. Ese conjunto de 4
direcciones + la celda propia cubre las 8 celdas vecinas sin repetir
ningún par de celdas dos veces (la otra mitad del stencil queda cubierta
implícitamente cuando se procesa la celda vecina correspondiente).
"""

import math
import time
from typing import Any, Callable, Dict, List, Tuple

import numpy as np


class MInvalidoError(ValueError):
    """Se lanza cuando M supera el M_max permitido para L, rc y r_max dados.

    Un M demasiado grande (celdas demasiado chicas) puede hacer que dos
    partículas vecinas (distancia borde-borde < rc) queden en celdas no
    adyacentes, y el CIM las pasaría por alto.
    """


def calcular_M_max(l: float, rc: float, r_max: float) -> int:
    """Calcula la cantidad máxima de celdas por lado (M) válida para el CIM.

    Ver el docstring del módulo para el razonamiento completo. En resumen:
    como el criterio de vecindad es sobre la distancia borde-borde y las
    partículas tienen radio, se usa un radio de interacción efectivo
    rc_efectivo = rc + 2*r_max (peor caso: dos partículas del radio
    máximo) para asegurar que las partículas vecinas siempre caigan en
    celdas iguales o adyacentes.

    Args:
        l: Longitud del lado del espacio de simulación (cuadrado L x L).
        rc: Radio de interacción (criterio de vecindad borde-borde).
        r_max: Radio máximo entre todas las partículas del sistema.

    Returns:
        M_max: cantidad máxima de celdas por lado tal que L/M > rc_efectivo.
        Se garantiza M_max >= 1, ya que M=1 (una sola celda) siempre es
        válido y equivale a fuerza bruta.
    """
    rc_efectivo = rc + 2 * r_max
    return max(1, math.floor(l / rc_efectivo))


def construir_celdas(
    posiciones: np.ndarray,
    l: float,
    m: int,
) -> Dict[Tuple[int, int], List[int]]:
    """Construye la grilla de celdas y asigna cada partícula a su celda.

    Args:
        posiciones: Array (N, 2) con las coordenadas (x, y) de cada
            partícula.
        l: Longitud del lado del espacio de simulación (cuadrado L x L).
        m: Cantidad de celdas por lado de la grilla.

    Returns:
        Diccionario que mapea el índice (fila, columna) de cada celda a la
        lista de índices de partículas contenidas en ella. Solo incluye
        celdas no vacías.
    """
    tam_celda = l / m
    celdas: Dict[Tuple[int, int], List[int]] = {}

    for idx, (x, y) in enumerate(posiciones):
        col = min(int(x / tam_celda), m - 1)
        fila = min(int(y / tam_celda), m - 1)
        celdas.setdefault((fila, col), []).append(idx)

    return celdas


# Semi-stencil de offsets (delta_fila, delta_columna) que, junto con la
# celda propia (pares i < j dentro de ella), cubre las 8 celdas vecinas de
# una celda 2D sin comparar ningún par de celdas dos veces.
_OFFSETS_VECINOS = [(0, 1), (1, -1), (1, 0), (1, 1)]


def _distancia_borde_borde(
    pos_i: np.ndarray,
    pos_j: np.ndarray,
    r_i: float,
    r_j: float,
    l: float,
    periodic: bool,
) -> float:
    """Calcula la distancia borde-borde entre dos partículas."""
    delta = pos_i - pos_j
    if periodic:
        delta = delta - l * np.round(delta / l)
    distancia_centros = math.hypot(delta[0], delta[1])
    return distancia_centros - (r_i + r_j)


def _agregar_par_si_vecino(
    i: int,
    j: int,
    posiciones: np.ndarray,
    radios: np.ndarray,
    l: float,
    rc: float,
    periodic: bool,
    vecinos: Dict[int, List[int]],
) -> None:
    dist_borde = _distancia_borde_borde(
        posiciones[i], posiciones[j], radios[i], radios[j], l, periodic
    )
    if dist_borde < rc:
        vecinos[i].append(j)
        vecinos[j].append(i)


def buscar_vecinos_cim(
    posiciones: np.ndarray,
    radios: np.ndarray,
    l: float,
    m: int,
    rc: float,
    periodic: bool = False,
) -> Dict[int, List[int]]:
    """Busca los pares de partículas vecinas utilizando el Cell Index Method.

    Dos partículas i, j son vecinas si su distancia borde-borde
    (||centro_i - centro_j|| - (r_i + r_j)) es menor a rc.

    Args:
        posiciones: Array (N, 2) con las coordenadas (x, y) de cada
            partícula.
        radios: Array (N,) con el radio de cada partícula.
        l: Longitud del lado del espacio de simulación (cuadrado L x L).
        m: Cantidad de celdas por lado de la grilla.
        rc: Radio de interacción (criterio de vecindad borde-borde).
        periodic: Si es True, se consideran condiciones de borde
            periódicas: las celdas vecinas se calculan módulo M y la
            distancia entre partículas usa la convención de mínima imagen.

    Returns:
        Diccionario {id_particula: [ids de vecinas]}, bidireccional (si j
        es vecina de i, entonces i también aparece en la lista de j).

    Raises:
        MInvalidoError: si m > calcular_M_max(l, rc, radios.max()), ya que
            en ese caso el CIM podría no detectar pares de partículas
            vecinas cuyos centros caigan en celdas no adyacentes.
    """
    n = len(posiciones)
    r_max = float(np.max(radios)) if n > 0 else 0.0
    m_max = calcular_M_max(l, rc, r_max)

    if m > m_max:
        raise MInvalidoError(
            f"M={m} supera el M_max={m_max} permitido para L={l}, rc={rc} "
            f"y r_max={r_max:.4f} (rc_efectivo={rc + 2 * r_max:.4f}). Con "
            f"un M mayor a M_max, el CIM podría no detectar pares de "
            f"partículas vecinas cuyos centros caen en celdas no "
            f"adyacentes."
        )

    celdas = construir_celdas(posiciones, l, m)
    vecinos: Dict[int, List[int]] = {i: [] for i in range(n)}

    # Con M chico (1 o 2) y condiciones periódicas, el wraparound puede
    # hacer que una celda "se vecine a sí misma" o que dos offsets
    # distintos apunten a la misma celda vecina (colisión). Se dedupean
    # los pares de celdas ya procesados para no comparar el mismo par de
    # partículas más de una vez.
    pares_celdas_procesados = set()

    for (fila, col), indices_celda in celdas.items():
        # Pares dentro de la misma celda (i < j para no duplicar).
        for a in range(len(indices_celda)):
            for b in range(a + 1, len(indices_celda)):
                i, j = indices_celda[a], indices_celda[b]
                _agregar_par_si_vecino(i, j, posiciones, radios, l, rc, periodic, vecinos)

        # Pares contra celdas vecinas (semi-stencil "hacia adelante").
        celda_actual = (fila, col)
        for d_fila, d_col in _OFFSETS_VECINOS:
            fila_vecina = fila + d_fila
            col_vecina = col + d_col

            if periodic:
                fila_vecina %= m
                col_vecina %= m
            elif not (0 <= fila_vecina < m and 0 <= col_vecina < m):
                continue

            celda_vecina = (fila_vecina, col_vecina)

            if celda_vecina == celda_actual:
                # M=1 (o wraparound degenerado): ya cubierta por el loop
                # intra-celda de arriba.
                continue

            par_celdas = frozenset((celda_actual, celda_vecina))
            if par_celdas in pares_celdas_procesados:
                continue
            pares_celdas_procesados.add(par_celdas)

            indices_vecina = celdas.get(celda_vecina)
            if not indices_vecina:
                continue

            for i in indices_celda:
                for j in indices_vecina:
                    _agregar_par_si_vecino(i, j, posiciones, radios, l, rc, periodic, vecinos)

    return vecinos


def buscar_vecinos_fuerza_bruta(
    posiciones: np.ndarray,
    radios: np.ndarray,
    l: float,
    rc: float,
    periodic: bool = False,
) -> Dict[int, List[int]]:
    """Busca los pares de partículas vecinas comparando todos contra todos.

    Mismo criterio de vecindad que `buscar_vecinos_cim` (distancia
    borde-borde < rc), pero comparando exhaustivamente todos los pares
    (equivalente al caso M=1 del CIM). Se usa como referencia para
    verificar la correctitud del CIM.

    Args:
        posiciones: Array (N, 2) con las coordenadas (x, y) de cada
            partícula.
        radios: Array (N,) con el radio de cada partícula.
        l: Longitud del lado del espacio de simulación (cuadrado L x L).
        rc: Radio de interacción (criterio de vecindad borde-borde).
        periodic: Si es True, se usa la convención de mínima imagen para
            calcular la distancia entre partículas.

    Returns:
        Diccionario {id_particula: [ids de vecinas]}, bidireccional.
    """
    n = len(posiciones)
    vecinos: Dict[int, List[int]] = {i: [] for i in range(n)}

    for i in range(n):
        for j in range(i + 1, n):
            _agregar_par_si_vecino(i, j, posiciones, radios, l, rc, periodic, vecinos)

    return vecinos


def medir_tiempo_busqueda(
    funcion_busqueda: Callable[..., Dict[int, List[int]]],
    *args: Any,
    **kwargs: Any,
) -> Tuple[Dict[int, List[int]], float]:
    """Ejecuta una función de búsqueda de vecinos y mide su tiempo de corrida.

    Args:
        funcion_busqueda: Función a ejecutar (por ejemplo,
            `buscar_vecinos_cim` o `buscar_vecinos_fuerza_bruta`).
        *args: Argumentos posicionales para `funcion_busqueda`.
        **kwargs: Argumentos nombrados para `funcion_busqueda`.

    Returns:
        Tupla (resultado, tiempo_segundos), donde `resultado` es lo que
        devuelve `funcion_busqueda` y `tiempo_segundos` es el tiempo de
        ejecución medido con `time.perf_counter()`.
    """
    inicio = time.perf_counter()
    resultado = funcion_busqueda(*args, **kwargs)
    tiempo_segundos = time.perf_counter() - inicio
    return resultado, tiempo_segundos
