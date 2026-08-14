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


def _matriz_distancia_borde_borde(
    pos_a: np.ndarray,
    radios_a: np.ndarray,
    pos_b: np.ndarray,
    radios_b: np.ndarray,
    l: float,
    periodic: bool,
) -> np.ndarray:
    """Matriz (len(pos_a), len(pos_b)) de distancias borde-borde, vectorizada.

    Calcula todas las distancias centro-centro entre los dos conjuntos de
    partículas de una sola vez (broadcasting), y les resta la suma de
    radios correspondiente.
    """
    delta = pos_a[:, None, :] - pos_b[None, :, :]  # (na, nb, 2)
    if periodic:
        delta = delta - l * np.round(delta / l)
    distancia_centros = np.linalg.norm(delta, axis=-1)  # (na, nb)
    return distancia_centros - (radios_a[:, None] + radios_b[None, :])


def _pares_vecinos_entre_conjuntos(
    indices_a: np.ndarray,
    indices_b: np.ndarray,
    posiciones: np.ndarray,
    radios: np.ndarray,
    l: float,
    rc: float,
    periodic: bool,
    misma_celda: bool,
) -> Tuple[np.ndarray, np.ndarray]:
    """Encuentra, de forma vectorizada, los pares vecinos entre dos
    conjuntos de índices de partículas (por ejemplo, dos celdas, o toda
    la nube de partículas contra sí misma en el caso de fuerza bruta).

    Args:
        indices_a, indices_b: arrays de índices globales de partículas.
        misma_celda: True si indices_a e indices_b son el mismo conjunto
            (hay que anular la diagonal para no auto-comparar una
            partícula consigo misma, y quedarse solo con el triángulo
            superior para no duplicar cada par).

    Returns:
        (indices_i, indices_j): arrays de índices globales de los pares
        vecinos encontrados (mismo largo cada uno).
    """
    if indices_a.size == 0 or indices_b.size == 0:
        vacio = np.empty(0, dtype=int)
        return vacio, vacio
    if misma_celda and indices_a.size < 2:
        vacio = np.empty(0, dtype=int)
        return vacio, vacio

    dist_borde = _matriz_distancia_borde_borde(
        posiciones[indices_a], radios[indices_a], posiciones[indices_b], radios[indices_b], l, periodic
    )
    mascara = dist_borde < rc

    if misma_celda:
        mascara = np.triu(mascara, k=1)  # anula diagonal y triángulo inferior

    filas, cols = np.nonzero(mascara)
    return indices_a[filas], indices_b[cols]


def _mapa_celdas_vecinas(m: int, periodic: bool) -> List[np.ndarray]:
    """Para cada una de las M² celdas y cada offset del semi-stencil,
    calcula el id de la celda vecina correspondiente (o -1 si no aplica).

    Esto se calcula una sola vez sobre la grilla de celdas (tamaño M², no
    N): la parte pesada es vectorizada con numpy, y el único loop de
    Python puro recorre la grilla de celdas (a lo sumo M² <= 169²
    entradas en total contando las 4 direcciones), nunca las N partículas
    ni pares de partículas, así que su costo no escala con N.

    Un offset se invalida (-1) si cae fuera de la grilla (caso no
    periódico), si coincide con la celda propia, o si el PAR de celdas
    {origen, destino} ya fue cubierto por otro offset (de esta celda o de
    la celda vecina): con M chico y condiciones periódicas, el wraparound
    puede hacer que dos offsets distintos —incluso de celdas origen
    distintas— colisionen en el mismo par de celdas, y hay que dedupear
    ese par a nivel global (no alcanza con mirar solo los offsets de la
    misma celda origen).

    Returns:
        Lista de 4 arrays (uno por offset), cada uno de tamaño M², con el
        id de celda vecina (fila*M + col) o -1.
    """
    n_celdas = m * m
    cell_id = np.arange(n_celdas)
    fila = cell_id // m
    col = cell_id % m

    mapa: List[np.ndarray] = []
    for d_fila, d_col in _OFFSETS_VECINOS:
        fila_v = fila + d_fila
        col_v = col + d_col

        if periodic:
            fila_v = fila_v % m
            col_v = col_v % m
            valido = np.ones(n_celdas, dtype=bool)
        else:
            valido = (fila_v >= 0) & (fila_v < m) & (col_v >= 0) & (col_v < m)

        objetivo = np.where(valido, fila_v * m + col_v, -1)
        objetivo = np.where(objetivo == cell_id, -1, objetivo)  # descarta autovecindad
        mapa.append(objetivo)

    # Dedup global de pares de celdas: a lo sumo 4*M² entradas (chico,
    # independiente de N), así que un loop de Python puro acá es barato.
    pares_procesados: set = set()
    for objetivo in mapa:
        for c in range(n_celdas):
            t = int(objetivo[c])
            if t == -1:
                continue
            par = frozenset((c, t))
            if par in pares_procesados:
                objetivo[c] = -1
            else:
                pares_procesados.add(par)

    return mapa


def _expandir_pares_hacia_celda(
    idx_particulas: np.ndarray,
    celda_objetivo: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
    orden: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Para cada partícula en `idx_particulas`, arma el par (partícula,
    vecino_candidato) contra TODAS las partículas de su celda objetivo,
    para todas las partículas a la vez, sin loop de Python por celda.

    Args:
        idx_particulas: índices globales de las partículas fuente.
        celda_objetivo: id de celda objetivo para cada partícula fuente
            (mismo largo que idx_particulas); -1 descarta esa partícula.
        starts, ends: para cada id de celda (0..M²-1), rango [start, end)
            en `orden` donde están las partículas de esa celda (grilla
            armada una sola vez con argsort + bincount, no por celda).
        orden: índices globales de las partículas, ordenados por celda.

    Returns:
        (idx_i, idx_j): pares candidatos (mismo largo cada uno). No se
        calcula ninguna distancia acá.
    """
    validas = celda_objetivo >= 0
    idx_fuente = idx_particulas[validas]
    if idx_fuente.size == 0:
        vacio = np.empty(0, dtype=int)
        return vacio, vacio

    celdas_obj = celda_objetivo[validas]
    s = starts[celdas_obj]
    cuentas = ends[celdas_obj] - s
    total = int(cuentas.sum())
    if total == 0:
        vacio = np.empty(0, dtype=int)
        return vacio, vacio

    idx_i = np.repeat(idx_fuente, cuentas)

    # Expansión de rangos "ragged" (de largo variable) sin loop de Python:
    # para la partícula k-ésima, su bloque de vecinos candidatos ocupa
    # `cuentas[k]` posiciones consecutivas en `orden`, empezando en s[k].
    inicio_bloque = np.cumsum(cuentas) - cuentas
    posicion_local = np.arange(total) - np.repeat(inicio_bloque, cuentas)
    posiciones = np.repeat(s, cuentas) + posicion_local
    idx_j = orden[posiciones]

    return idx_i, idx_j


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

    Implementación completamente vectorizada, sin ningún loop de Python
    sobre las M² celdas (solo un loop constante de 4 iteraciones, una por
    offset del semi-stencil). La grilla se arma una sola vez con
    `argsort`/`bincount` (no con un diccionario poblado partícula por
    partícula), y los pares candidatos de cada offset se expanden con
    operaciones de numpy sobre TODAS las partículas a la vez (ver
    `_expandir_pares_hacia_celda`). Recién al final se hace una única
    pasada vectorizada de cálculo de distancias sobre todos los
    candidatos juntos.

    Esto importa porque una implementación que recorre las M² celdas en
    Python y llama a numpy por cada una paga un overhead fijo por
    celda (no por partícula): con M grande cada celda tiene pocas
    partículas, y ese overhead terminaba dominando sobre el ahorro real
    de trabajo aritmético, haciendo que el tiempo volviera a subir cerca
    de M_max en vez de seguir bajando. Al eliminar el loop por celda, el
    tiempo baja monótonamente con M (menos pares candidatos totales).

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

    vecinos: Dict[int, List[int]] = {i: [] for i in range(n)}
    if n < 2:
        return vecinos

    # Grilla armada vectorizada (sin loop de Python por partícula ni por
    # celda): a cada partícula se le asigna un id de celda (fila*M+col),
    # y se ordena por ese id. `starts`/`ends` delimitan, para cada una de
    # las M² celdas, el rango de `orden` con sus partículas.
    tam_celda = l / m
    col_particula = np.minimum((posiciones[:, 0] / tam_celda).astype(int), m - 1)
    fila_particula = np.minimum((posiciones[:, 1] / tam_celda).astype(int), m - 1)
    celda_id_particula = fila_particula * m + col_particula

    orden = np.argsort(celda_id_particula, kind="stable")
    cuentas_por_celda = np.bincount(celda_id_particula, minlength=m * m)
    ends = np.cumsum(cuentas_por_celda)
    starts = ends - cuentas_por_celda

    todas_las_particulas = np.arange(n)
    candidatos_i: List[np.ndarray] = []
    candidatos_j: List[np.ndarray] = []

    # Pares dentro de la misma celda: cada partícula contra todas las de
    # su propia celda (incluida ella misma), filtrando luego i < j.
    idx_i, idx_j = _expandir_pares_hacia_celda(
        todas_las_particulas, celda_id_particula, starts, ends, orden
    )
    intra_validos = idx_i < idx_j
    candidatos_i.append(idx_i[intra_validos])
    candidatos_j.append(idx_j[intra_validos])

    # Pares contra celdas vecinas (semi-stencil "hacia adelante"), un
    # offset a la vez (4 iteraciones constantes, no M²).
    mapa_vecinas = _mapa_celdas_vecinas(m, periodic)
    for celda_objetivo_por_celda in mapa_vecinas:
        celda_objetivo_por_particula = celda_objetivo_por_celda[celda_id_particula]
        idx_i, idx_j = _expandir_pares_hacia_celda(
            todas_las_particulas, celda_objetivo_por_particula, starts, ends, orden
        )
        candidatos_i.append(idx_i)
        candidatos_j.append(idx_j)

    idx_i = np.concatenate(candidatos_i)
    idx_j = np.concatenate(candidatos_j)

    if idx_i.size == 0:
        return vecinos

    # Única pasada vectorizada de numpy sobre TODOS los pares candidatos
    # del sistema, en vez de una pasada por cada par de celdas.
    delta = posiciones[idx_i] - posiciones[idx_j]
    if periodic:
        delta = delta - l * np.round(delta / l)
    dist_centros = np.linalg.norm(delta, axis=-1)
    dist_borde = dist_centros - (radios[idx_i] + radios[idx_j])
    mascara = dist_borde < rc

    idx_i_final = idx_i[mascara]
    idx_j_final = idx_j[mascara]

    for i, j in zip(idx_i_final.tolist(), idx_j_final.tolist()):
        vecinos[i].append(j)
        vecinos[j].append(i)

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

    La matriz de distancias se calcula vectorizada con numpy
    (broadcasting), no con un loop anidado de Python: para N grande, un
    loop puro sobre C(N,2) pares es el cuello de botella dominante (por
    ejemplo, ~0.55s para N=1140 con el loop de Python vs. milisegundos
    vectorizado).

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

    if n < 2:
        return vecinos

    todos_los_indices = np.arange(n)
    idx_i, idx_j = _pares_vecinos_entre_conjuntos(
        todos_los_indices, todos_los_indices, posiciones, radios, l, rc, periodic, misma_celda=True
    )
    for i, j in zip(idx_i.tolist(), idx_j.tolist()):
        vecinos[i].append(j)
        vecinos[j].append(i)

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
