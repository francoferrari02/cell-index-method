"""Generación de conjuntos de partículas para las simulaciones del CIM.

Este módulo genera partículas con posición (x, y) y radio r, distribuidas
dentro de un espacio de simulación cuadrado de lado L, para ser utilizadas
como entrada de los algoritmos de búsqueda de vecinos (CIM y fuerza bruta).

Approach: rejection sampling
------------------------------
Para evitar partículas superpuestas se usa "rejection sampling": se genera
una posición candidata al azar y se verifica, contra todas las partículas
ya colocadas, que la distancia centro-centro sea mayor a la suma de los
radios (es decir, distancia borde-borde > 0). Si la candidata se superpone
con alguna partícula existente, se descarta y se reintenta con una nueva
posición aleatoria.

Limitaciones: a medida que aumenta la densidad de partículas (N / L^2), el
espacio libre disponible para nuevas posiciones válidas se reduce, y la
probabilidad de que una candidata aleatoria sea aceptada cae rápidamente.
Esto hace que el número de intentos necesarios para colocar cada partícula
crezca (en el límite, de forma no acotada) a medida que el sistema se
acerca a la densidad de empaquetamiento máxima. Por eso se establece un
límite máximo de intentos: si se supera, se asume que la densidad pedida
no es alcanzable (o resulta impracticable) con este método, y se lanza una
excepción en lugar de bloquear la ejecución indefinidamente.
"""

from typing import Dict

import numpy as np


class GeneracionParticulasError(RuntimeError):
    """Se lanza cuando no se logra generar el conjunto de partículas pedido.

    Típicamente indica que la densidad (N / L^2) solicitada es demasiado
    alta para los radios dados, y el rejection sampling no converge dentro
    del límite de intentos permitido.
    """


def calcular_densidad(n: int, lado: float) -> float:
    """Calcula la densidad de partículas del sistema.

    Args:
        n: Cantidad de partículas.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).

    Returns:
        Densidad N / L^2.
    """
    return n / lado**2


def generar_particulas(
    n: int,
    lado: float,
    r_min: float = 0.23,
    r_max: float = 0.26,
    seed: "int | None" = None,
    periodic: bool = False,
    max_intentos: int = 100_000,
) -> Dict[str, np.ndarray]:
    """Genera N partículas sin superposición dentro de un espacio 2D.

    Coloca las partículas una por una mediante rejection sampling: para
    cada partícula se generan posiciones candidatas al azar hasta
    encontrar una que no se superponga con ninguna de las ya colocadas
    (distancia centro-centro > r_i + r_j para todo par i, j).

    Args:
        n: Cantidad de partículas a generar.
        lado: Longitud del lado del espacio de simulación (cuadrado L x L).
        r_min: Cota inferior (inclusive) del radio, distribuido U[r_min, r_max].
        r_max: Cota superior (inclusive) del radio, distribuido U[r_min, r_max].
        seed: Semilla para el generador aleatorio (numpy Generator), para
            reproducibilidad. Si es None, la secuencia no es reproducible.
        periodic: Si es False (default), cada partícula se ubica en
            [r_i, L - r_i] en cada eje, para que no quede pegada/salida
            del borde. Si es True, se ubica en [0, L] (pensado para usarse
            junto con condiciones de borde periódicas en la búsqueda de
            vecinos).
        max_intentos: Cantidad máxima total de intentos (candidatas
            generadas y rechazadas incluidas) permitidos para completar la
            colocación de las N partículas. Si se supera, se lanza
            GeneracionParticulasError.

    Returns:
        Diccionario con dos arrays de numpy:
            - "posiciones": array de forma (N, 2) con las coordenadas (x, y)
              de cada partícula.
            - "radios": array de forma (N,) con el radio de cada partícula.

    Raises:
        GeneracionParticulasError: si no se logran colocar las N partículas
            sin superposición dentro de max_intentos intentos totales (por
            ejemplo, por pedir una densidad demasiado alta para el L y los
            radios dados).
    """
    rng = np.random.default_rng(seed)

    posiciones = np.empty((n, 2), dtype=float)
    radios = np.empty(n, dtype=float)

    intentos_totales = 0
    colocadas = 0

    while colocadas < n:
        if intentos_totales >= max_intentos:
            raise GeneracionParticulasError(
                f"No se pudieron generar {n} partículas en un espacio de "
                f"lado {lado} (densidad={calcular_densidad(n, lado):.4f}) "
                f"con radios en [{r_min}, {r_max}]: se alcanzó el límite de "
                f"{max_intentos} intentos habiendo colocado solo "
                f"{colocadas} partículas. Probá con una densidad menor, "
                f"radios más chicos, o un max_intentos mayor."
            )

        r_candidata = rng.uniform(r_min, r_max)

        if periodic:
            low, high = 0.0, lado
        else:
            low, high = r_candidata, lado - r_candidata
            if low > high:
                # El radio candidato no entra en el dominio no periódico.
                intentos_totales += 1
                continue

        pos_candidata = rng.uniform(low, high, size=2)

        if colocadas > 0:
            deltas = posiciones[:colocadas] - pos_candidata
            distancias = np.hypot(deltas[:, 0], deltas[:, 1])
            radios_suma = radios[:colocadas] + r_candidata
            hay_superposicion = np.any(distancias <= radios_suma)
        else:
            hay_superposicion = False

        intentos_totales += 1

        if hay_superposicion:
            continue

        posiciones[colocadas] = pos_candidata
        radios[colocadas] = r_candidata
        colocadas += 1

    return {"posiciones": posiciones, "radios": radios}
