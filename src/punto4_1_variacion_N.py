"""Punto 4.1 del TP: tiempo de busqueda vs N, con M y L=20 fijos (densidad libre).

M se fija en el M ideal encontrado en el punto 3. Como L no cambia, la
densidad (N / L^2) crece junto con N.
"""

from src.benchmark import experimento_variacion_N, graficar_variacion_N
from src.visualize import guardar_figura

L = 20.0
RC = 1.0
R_MIN, R_MAX = 0.23, 0.26
N_REPETICIONES = 100
SEED = 42
M_IDEAL = 5  # encontrado en el punto 3
VALORES_N = [10, 17, 29, 48, 82, 139, 235, 398, 674, 1140]  # log-espaciados hasta N_max


def main() -> None:
    df = experimento_variacion_N(
        l=L, rc=RC, r_min=R_MIN, r_max=R_MAX,
        valores_n=VALORES_N,
        m=M_IDEAL,
        n_repeticiones=N_REPETICIONES,
        max_intentos=5_000_000,  # necesario para poder generar N=1140
        seed=SEED,
    )

    ax = graficar_variacion_N(df, titulo=f"Punto 4.1: Tiempo vs N (L={L:g}, M={M_IDEAL} fijo)")
    guardar_figura(ax.figure, "punto4p1_variacion_N")

    print(df)


if __name__ == "__main__":
    main()
