"""Punto 4.2 del TP: tiempo de busqueda vs N, a densidad constante (L crece con N).

Compara contra la curva de densidad libre del punto 4.1 (mismo M y mismos
N). La densidad de referencia es N=48, L=20 (=0.12), elegida porque deja
M_max >= M_IDEAL en todos los puntos de VALORES_N, incluido el mas chico.
"""

from src.benchmark import (
    experimento_variacion_N,
    experimento_variacion_N_densidad_fija,
    graficar_variacion_N,
)
from src.visualize import guardar_figura

L = 20.0
RC = 1.0
R_MIN, R_MAX = 0.23, 0.26
N_REPETICIONES = 100
SEED = 42
M_IDEAL = 5  # mismo M que en el punto 4.1, para que la comparacion sea valida
VALORES_N = [10, 17, 29, 48, 82, 139, 235, 398, 674, 1140]

N_INICIAL = 48  # densidad de referencia (0.12), valida en todo el rango
L_INICIAL = 20.0
# factor = sqrt(N_objetivo / N_INICIAL), para que los N generados coincidan
# exactamente con VALORES_N
FACTORES_ESCALA = [0.4564, 0.5951, 0.7773, 1.0, 1.3070, 1.7017, 2.2127, 2.8795, 3.7472, 4.8734]


def main() -> None:
    df_libre = experimento_variacion_N(
        l=L, rc=RC, r_min=R_MIN, r_max=R_MAX,
        valores_n=VALORES_N,
        m=M_IDEAL,
        n_repeticiones=N_REPETICIONES,
        max_intentos=5_000_000,
        seed=SEED,
    )

    df_fija = experimento_variacion_N_densidad_fija(
        l_inicial=L_INICIAL,
        n_inicial=N_INICIAL,
        rc=RC, r_min=R_MIN, r_max=R_MAX,
        factores_escala=FACTORES_ESCALA,
        m=M_IDEAL,
        n_repeticiones=N_REPETICIONES,
        max_intentos=5_000_000,
        seed=SEED,
    )

    ax = graficar_variacion_N(
        df_densidad_fija=df_fija,
        df_densidad_libre=df_libre,
        titulo="Punto 4: Tiempo vs N (Densidad fija vs Densidad libre)",
    )
    guardar_figura(ax.figure, "punto4_completo")

    print(df_fija[["N", "L", "M_usado", "tiempo_promedio", "densidad"]])
    print(df_libre[["N", "M_usado", "tiempo_promedio", "densidad"]])


if __name__ == "__main__":
    main()
