"""Script principal del punto 1 del enunciado del TP1.

Integra los módulos particles, cim y visualize para: generar un sistema
de N partículas, encontrar los vecinos de una partícula dada usando el
Cell Index Method, medir el tiempo de búsqueda, imprimir el resultado en
el formato pedido y generar una figura con la partícula elegida y sus
vecinas resaltadas.
"""

import argparse
from typing import Any, Dict, Optional

import numpy as np

from src.cim import buscar_vecinos_cim, calcular_M_max, medir_tiempo_busqueda
from src.particles import generar_particulas
from src.visualize import graficar_particulas, guardar_figura


def main(
    n: int,
    l: float,
    rc: float,
    particula_id: Optional[int] = None,
    m: Optional[int] = None,
    periodic: bool = False,
    seed: Optional[int] = None,
    r_min: float = 0.23,
    r_max: float = 0.26,
) -> Dict[str, Any]:
    """Corre el flujo completo del punto 1 del TP: generación + CIM + gráfico.

    Args:
        n: Cantidad de partículas a generar.
        l: Longitud del lado del espacio de simulación (cuadrado L x L).
        rc: Radio de interacción (criterio de vecindad borde-borde).
        particula_id: Índice de la partícula cuyos vecinos se quieren
            reportar y graficar. Si es None, se elige una al azar (usando
            `seed`).
        m: Cantidad de celdas por lado a usar en el CIM. Si es None, se
            calcula automáticamente con `calcular_M_max` (el M más fino
            posible para L, rc y el radio máximo del sistema).
        periodic: Si es True, se usan condiciones de borde periódicas.
        seed: Semilla para la generación de partículas y, si
            `particula_id` es None, para elegir la partícula al azar.
        r_min: Cota inferior del radio de las partículas.
        r_max: Cota superior del radio de las partículas.

    Returns:
        Diccionario con:
            - "vecinos": lista de ids de las partículas vecinas de
              `particula_id`.
            - "todos_los_vecinos": diccionario completo
              {id_particula: [ids de vecinas]} devuelto por el CIM.
            - "tiempo_segundos": tiempo de ejecución de la búsqueda de
              vecinos (CIM), medido con `medir_tiempo_busqueda`.
            - "particula_id": id de la partícula elegida (la pasada o la
              sorteada al azar).
            - "m": cantidad de celdas por lado efectivamente usada.
            - "path_figura": ruta del archivo de figura generado.
    """
    resultado_particulas = generar_particulas(
        n, lado=l, r_min=r_min, r_max=r_max, seed=seed, periodic=periodic
    )
    posiciones = resultado_particulas["posiciones"]
    radios = resultado_particulas["radios"]

    if m is None:
        m = calcular_M_max(l, rc, float(radios.max()))

    if particula_id is None:
        rng = np.random.default_rng(seed)
        particula_id = int(rng.integers(0, n))

    todos_los_vecinos, tiempo_segundos = medir_tiempo_busqueda(
        buscar_vecinos_cim, posiciones, radios, l, m, rc, periodic=periodic
    )
    vecinos = todos_los_vecinos[particula_id]

    print(f"Tiempo de busqueda (CIM, N={n}, M={m}): {tiempo_segundos:.6f} s")
    print(f"{particula_id} {' '.join(str(v) for v in vecinos)}")

    ax = graficar_particulas(
        posiciones,
        radios,
        l,
        particula_id=particula_id,
        vecinos=vecinos,
        mostrar_grilla=True,
        m=m,
        titulo=f"N={n}, L={l}, rc={rc}, M={m} - particula {particula_id}",
    )
    nombre_figura = f"main_tp1_N{n}_L{l:g}_rc{rc:g}".replace(".", "p")
    path_figura = guardar_figura(ax.figure, nombre_figura)
    print(f"Figura guardada en: {path_figura}")

    return {
        "vecinos": vecinos,
        "todos_los_vecinos": todos_los_vecinos,
        "tiempo_segundos": tiempo_segundos,
        "particula_id": particula_id,
        "m": m,
        "path_figura": path_figura,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TP1 - Cell Index Method: busqueda de vecinos de una particula."
    )
    parser.add_argument("--n", type=int, required=True, help="Cantidad de particulas.")
    parser.add_argument("--l", type=float, default=20.0, help="Lado del espacio (default: 20).")
    parser.add_argument("--rc", type=float, default=1.0, help="Radio de interaccion (default: 1).")
    parser.add_argument(
        "--particula-id", type=int, default=None, help="Id de la particula a analizar."
    )
    parser.add_argument(
        "--m", type=int, default=None, help="Celdas por lado (default: el maximo valido)."
    )
    parser.add_argument(
        "--periodic", action="store_true", help="Usar condiciones de borde periodicas."
    )
    parser.add_argument("--seed", type=int, default=None, help="Semilla aleatoria.")

    args = parser.parse_args()

    main(
        n=args.n,
        l=args.l,
        rc=args.rc,
        particula_id=args.particula_id,
        m=args.m,
        periodic=args.periodic,
        seed=args.seed,
    )
