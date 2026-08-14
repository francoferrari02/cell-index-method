"""Punto 3 del TP: tiempo de busqueda de vecinos (CIM) en funcion de M.

Corre `experimento_variacion_M` para un N intermedio y para el N maximo
generable (encontrado con `explorar_n_max.py`), superpone ambas curvas y
guarda la figura resultante.
"""

from src.benchmark import experimento_variacion_M, graficar_variacion_M
from src.visualize import guardar_figura

L = 20.0
RC = 1.0
R_MIN, R_MAX = 0.23, 0.26
N_REPETICIONES = 100
SEED = 42
N_INTERMEDIO = 570  # N_max / 2
N_MAXIMO = 1140  # encontrado en explorar_n_max.py


def main() -> None:
    df_intermedio = experimento_variacion_M(
        n=N_INTERMEDIO, l=L, rc=RC, r_min=R_MIN, r_max=R_MAX,
        n_repeticiones=N_REPETICIONES, seed=SEED,
    )
    df_maximo = experimento_variacion_M(
        n=N_MAXIMO, l=L, rc=RC, r_min=R_MIN, r_max=R_MAX,
        n_repeticiones=N_REPETICIONES, seed=SEED,
        max_intentos=5_000_000,  # N alto necesita mas intentos que el default
    )

    ax = graficar_variacion_M(
        [df_intermedio, df_maximo],
        labels=[f"N={N_INTERMEDIO}", f"N={N_MAXIMO}"],
        titulo="Punto 3: tiempo de busqueda de vecinos vs M (CIM)",
        escala_log_y=True,
        escala_log_x=True,
    )
    guardar_figura(ax.figure, "punto3_variacion_M")

    print(df_intermedio)
    print(df_maximo)


if __name__ == "__main__":
    main()
