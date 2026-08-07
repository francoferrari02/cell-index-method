"""Experimentos de desempeño del Cell Index Method (puntos 3 y 4 del TP1).

Este módulo orquesta la ejecución de benchmarks para comparar los tiempos
de ejecución del CIM en función de la cantidad de celdas por lado (M,
punto 3) y de la cantidad de partículas (N, punto 4), tanto con L fijo
como manteniendo la densidad N/L^2 constante (punto 4.2).

Todas las funciones de experimento generan las partículas UNA sola vez
por punto experimental (fuera del bucle de repeticiones), de forma que el
tiempo medido corresponda únicamente al algoritmo de búsqueda de vecinos
y no a la generación del sistema.
"""

from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from src.cim import buscar_vecinos_cim, calcular_M_max, medir_tiempo_busqueda
from src.particles import GeneracionParticulasError, calcular_densidad, generar_particulas
from src.visualize import guardar_figura

_UMBRAL_ESCALA_LOG = 100.0


def correr_experimento_repetido(
    func_busqueda: Callable[..., Any],
    args_busqueda: Sequence[Any],
    n_repeticiones: int,
) -> Tuple[float, float]:
    """Corre una función de búsqueda varias veces y promedia el tiempo.

    Las partículas (y cualquier otro dato de entrada) deben venir ya
    generadas dentro de `args_busqueda`; esta función no genera nada, solo
    mide tiempos de ejecución repetidos de `func_busqueda`, para que el
    tiempo de generación de partículas no contamine la medición.

    Args:
        func_busqueda: Función a cronometrar (por ejemplo,
            `cim.buscar_vecinos_cim`).
        args_busqueda: Argumentos posicionales fijos a pasarle en cada
            corrida (por ejemplo, `(posiciones, radios, L, M, rc)`).
        n_repeticiones: Cantidad de veces que se repite la medición.

    Returns:
        Tupla (tiempo_promedio, tiempo_std) en segundos.
    """
    tiempos = np.empty(n_repeticiones, dtype=float)

    for k in range(n_repeticiones):
        _, tiempo = medir_tiempo_busqueda(func_busqueda, *args_busqueda)
        tiempos[k] = tiempo

    return float(np.mean(tiempos)), float(np.std(tiempos))


def experimento_variacion_M(
    n: int,
    l: float,
    rc: float,
    r_min: float,
    r_max: float,
    n_repeticiones: int = 100,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Mide el tiempo del CIM en función de M, con N fijo (punto 3 del TP).

    M=1 corresponde a una única celda (equivalente a fuerza bruta), así
    que no hace falta llamar por separado a `buscar_vecinos_fuerza_bruta`.

    Args:
        n: Cantidad de partículas (fija para todo el experimento).
        l: Longitud del lado del espacio de simulación.
        rc: Radio de interacción.
        r_min: Cota inferior del radio de las partículas.
        r_max: Cota superior del radio de las partículas.
        n_repeticiones: Repeticiones por cada valor de M.
        seed: Semilla para la generación de partículas.

    Returns:
        DataFrame con columnas: M, tiempo_promedio, tiempo_std.
    """
    resultado = generar_particulas(n, lado=l, r_min=r_min, r_max=r_max, seed=seed)
    posiciones = resultado["posiciones"]
    radios = resultado["radios"]

    m_max = calcular_M_max(l, rc, float(radios.max()))

    filas = []
    for m in range(1, m_max + 1):
        args_busqueda = (posiciones, radios, l, m, rc)
        promedio, std = correr_experimento_repetido(
            buscar_vecinos_cim, args_busqueda, n_repeticiones
        )
        filas.append({"M": m, "tiempo_promedio": promedio, "tiempo_std": std})

    return pd.DataFrame(filas)


def experimento_variacion_N(
    l: float,
    rc: float,
    r_min: float,
    r_max: float,
    valores_n: Iterable[int],
    m: Optional[int] = None,
    n_repeticiones: int = 100,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Mide el tiempo del CIM en función de N, con L fijo (punto 4 del TP).

    Args:
        l: Longitud del lado del espacio de simulación (fija).
        rc: Radio de interacción.
        r_min: Cota inferior del radio de las partículas.
        r_max: Cota superior del radio de las partículas.
        valores_n: Valores de N a evaluar.
        m: Cantidad de celdas por lado a usar. Si es None, se usa el M
            óptimo (`calcular_M_max`) para cada N.
        n_repeticiones: Repeticiones por cada valor de N.
        seed: Semilla para la generación de partículas.

    Returns:
        DataFrame con columnas: N, M_usado, tiempo_promedio, tiempo_std,
        densidad, alcanzado. Las filas donde no fue posible generar las N
        partículas pedidas (densidad demasiado alta) quedan con
        `alcanzado=False` y los tiempos en NaN, sin interrumpir el resto
        del experimento.
    """
    filas = []

    for n in valores_n:
        densidad = calcular_densidad(n, l)
        try:
            resultado = generar_particulas(n, lado=l, r_min=r_min, r_max=r_max, seed=seed)
        except GeneracionParticulasError:
            filas.append(
                {
                    "N": n,
                    "M_usado": None,
                    "tiempo_promedio": np.nan,
                    "tiempo_std": np.nan,
                    "densidad": densidad,
                    "alcanzado": False,
                }
            )
            continue

        posiciones = resultado["posiciones"]
        radios = resultado["radios"]
        m_usado = m if m is not None else calcular_M_max(l, rc, float(radios.max()))

        args_busqueda = (posiciones, radios, l, m_usado, rc)
        promedio, std = correr_experimento_repetido(
            buscar_vecinos_cim, args_busqueda, n_repeticiones
        )

        filas.append(
            {
                "N": n,
                "M_usado": m_usado,
                "tiempo_promedio": promedio,
                "tiempo_std": std,
                "densidad": densidad,
                "alcanzado": True,
            }
        )

    return pd.DataFrame(filas)


def experimento_variacion_N_densidad_fija(
    l_inicial: float,
    n_inicial: int,
    rc: float,
    r_min: float,
    r_max: float,
    factores_escala: Sequence[float],
    m: Optional[int] = None,
    n_repeticiones: int = 100,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Mide el tiempo del CIM escalando N y L juntos, a densidad constante
    (punto 4.2 del TP): densidad = N_inicial / L_inicial^2.

    Para cada factor de escala k en `factores_escala`, se usa
    L = L_inicial * k y N = round(N_inicial * k^2), de forma que
    N / L^2 se mantiene igual a N_inicial / L_inicial^2.

    Args:
        l_inicial: Lado de referencia.
        n_inicial: Cantidad de partículas de referencia.
        rc: Radio de interacción.
        r_min: Cota inferior del radio de las partículas.
        r_max: Cota superior del radio de las partículas.
        factores_escala: Factores k a aplicar sobre L_inicial y N_inicial.
        m: Cantidad de celdas por lado a usar. Si es None, se usa el M
            óptimo (`calcular_M_max`) para cada punto.
        n_repeticiones: Repeticiones por cada factor de escala.
        seed: Semilla para la generación de partículas.

    Returns:
        DataFrame con columnas: N, L, factor_escala, M_usado,
        tiempo_promedio, tiempo_std, densidad, alcanzado (mismo tipo de
        salida que `experimento_variacion_N`, con L y factor_escala como
        columnas adicionales de contexto).
    """
    filas = []

    for factor in factores_escala:
        l_actual = l_inicial * factor
        n_actual = int(round(n_inicial * factor**2))
        densidad = calcular_densidad(n_actual, l_actual)

        try:
            resultado = generar_particulas(
                n_actual, lado=l_actual, r_min=r_min, r_max=r_max, seed=seed
            )
        except GeneracionParticulasError:
            filas.append(
                {
                    "N": n_actual,
                    "L": l_actual,
                    "factor_escala": factor,
                    "M_usado": None,
                    "tiempo_promedio": np.nan,
                    "tiempo_std": np.nan,
                    "densidad": densidad,
                    "alcanzado": False,
                }
            )
            continue

        posiciones = resultado["posiciones"]
        radios = resultado["radios"]
        m_usado = m if m is not None else calcular_M_max(l_actual, rc, float(radios.max()))

        args_busqueda = (posiciones, radios, l_actual, m_usado, rc)
        promedio, std = correr_experimento_repetido(
            buscar_vecinos_cim, args_busqueda, n_repeticiones
        )

        filas.append(
            {
                "N": n_actual,
                "L": l_actual,
                "factor_escala": factor,
                "M_usado": m_usado,
                "tiempo_promedio": promedio,
                "tiempo_std": std,
                "densidad": densidad,
                "alcanzado": True,
            }
        )

    return pd.DataFrame(filas)


def _decidir_escala_log(valores: np.ndarray, umbral: float = _UMBRAL_ESCALA_LOG) -> bool:
    """Decide si conviene escala logarítmica según el rango de valores.

    Usa escala log si todos los valores son positivos y el ratio
    máximo/mínimo supera `umbral` (por defecto ~100).
    """
    valores = np.asarray(valores, dtype=float)
    valores = valores[~np.isnan(valores)]
    if valores.size == 0 or np.any(valores <= 0):
        return False
    return (valores.max() / valores.min()) > umbral


def graficar_variacion_M(
    dfs: Union[pd.DataFrame, Sequence[pd.DataFrame]],
    labels: Optional[Sequence[Optional[str]]] = None,
    escala_log_x: Optional[bool] = None,
    escala_log_y: Optional[bool] = None,
    ax: Optional[Axes] = None,
    titulo: Optional[str] = None,
) -> Axes:
    """Grafica tiempo vs M (con barras de error), una o varias curvas.

    Args:
        dfs: Un DataFrame (de `experimento_variacion_M`) o una lista de
            ellos, para superponer varias curvas (por ejemplo, distintos
            N) en el mismo gráfico.
        labels: Etiquetas para cada curva, en el mismo orden que `dfs`.
            Se ignora si `dfs` es un único DataFrame y no se pasa label.
        escala_log_x: Forzar (True/False) escala logarítmica en el eje M.
            Si es None, se decide automáticamente según el rango de M.
        escala_log_y: Forzar (True/False) escala logarítmica en el eje de
            tiempo. Si es None, se decide automáticamente según el rango
            de los tiempos medidos.
        ax: Axes de matplotlib donde dibujar. Si es None, se crea uno.
        titulo: Título opcional del gráfico.

    Returns:
        El Axes utilizado.
    """
    if isinstance(dfs, pd.DataFrame):
        lista_dfs: List[pd.DataFrame] = [dfs]
    else:
        lista_dfs = list(dfs)

    if labels is None:
        lista_labels: List[Optional[str]] = [None] * len(lista_dfs)
    else:
        lista_labels = list(labels)

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    for df, label in zip(lista_dfs, lista_labels):
        ax.errorbar(
            df["M"],
            df["tiempo_promedio"],
            yerr=df["tiempo_std"],
            marker="o",
            capsize=3,
            label=label,
        )

    todos_m = np.concatenate([df["M"].to_numpy(dtype=float) for df in lista_dfs])
    todos_tiempos = np.concatenate([df["tiempo_promedio"].to_numpy(dtype=float) for df in lista_dfs])

    if escala_log_x is None:
        escala_log_x = _decidir_escala_log(todos_m)
    if escala_log_y is None:
        escala_log_y = _decidir_escala_log(todos_tiempos)

    if escala_log_x:
        ax.set_xscale("log")
    if escala_log_y:
        ax.set_yscale("log")

    ax.set_xlabel("M (celdas por lado)")
    ax.set_ylabel("Tiempo de búsqueda (s)")
    if any(label is not None for label in lista_labels):
        ax.legend()
    if titulo is not None:
        ax.set_title(titulo)

    return ax


def graficar_variacion_N(
    df_densidad_fija: pd.DataFrame,
    df_densidad_libre: Optional[pd.DataFrame] = None,
    escala_log_x: Optional[bool] = None,
    escala_log_y: Optional[bool] = None,
    ax: Optional[Axes] = None,
    titulo: Optional[str] = None,
) -> Axes:
    """Grafica tiempo vs N (con barras de error), a densidad fija y/o libre.

    Args:
        df_densidad_fija: DataFrame de `experimento_variacion_N_densidad_fija`.
        df_densidad_libre: DataFrame opcional de `experimento_variacion_N`
            (L fijo, densidad creciente), para superponer con el anterior.
        escala_log_x: Forzar (True/False) escala logarítmica en el eje N.
            Si es None, se decide automáticamente.
        escala_log_y: Forzar (True/False) escala logarítmica en el eje de
            tiempo. Si es None, se decide automáticamente.
        ax: Axes de matplotlib donde dibujar. Si es None, se crea uno.
        titulo: Título opcional del gráfico.

    Returns:
        El Axes utilizado.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    df_fija = df_densidad_fija[df_densidad_fija["alcanzado"]]
    ax.errorbar(
        df_fija["N"],
        df_fija["tiempo_promedio"],
        yerr=df_fija["tiempo_std"],
        marker="o",
        capsize=3,
        label="Densidad fija",
    )

    todos_n = [df_fija["N"].to_numpy(dtype=float)]
    todos_tiempos = [df_fija["tiempo_promedio"].to_numpy(dtype=float)]

    if df_densidad_libre is not None:
        df_libre = df_densidad_libre[df_densidad_libre["alcanzado"]]
        ax.errorbar(
            df_libre["N"],
            df_libre["tiempo_promedio"],
            yerr=df_libre["tiempo_std"],
            marker="s",
            capsize=3,
            label="Densidad libre",
        )
        todos_n.append(df_libre["N"].to_numpy(dtype=float))
        todos_tiempos.append(df_libre["tiempo_promedio"].to_numpy(dtype=float))

    if escala_log_x is None:
        escala_log_x = _decidir_escala_log(np.concatenate(todos_n))
    if escala_log_y is None:
        escala_log_y = _decidir_escala_log(np.concatenate(todos_tiempos))

    if escala_log_x:
        ax.set_xscale("log")
    if escala_log_y:
        ax.set_yscale("log")

    ax.set_xlabel("N (cantidad de partículas)")
    ax.set_ylabel("Tiempo de búsqueda (s)")
    ax.legend()
    if titulo is not None:
        ax.set_title(titulo)

    return ax


if __name__ == "__main__":
    # Smoke test rápido: parámetros chicos y pocas repeticiones, solo para
    # verificar que el flujo completo (experimentos + gráficos + guardado)
    # funciona de punta a punta.
    L_SMOKE = 8.0
    RC_SMOKE = 0.5
    R_MIN_SMOKE, R_MAX_SMOKE = 0.23, 0.26
    N_REPETICIONES_SMOKE = 5

    print("Corriendo experimento_variacion_M (smoke test)...")
    df_m = experimento_variacion_M(
        n=20,
        l=L_SMOKE,
        rc=RC_SMOKE,
        r_min=R_MIN_SMOKE,
        r_max=R_MAX_SMOKE,
        n_repeticiones=N_REPETICIONES_SMOKE,
        seed=1,
    )
    print(df_m)

    ax_m = graficar_variacion_M(df_m, titulo="Tiempo vs M (N=20, smoke test)")
    guardar_figura(ax_m.figure, "benchmark_variacion_M")

    print("\nCorriendo experimento_variacion_N (smoke test, densidad libre)...")
    df_n_libre = experimento_variacion_N(
        l=L_SMOKE,
        rc=RC_SMOKE,
        r_min=R_MIN_SMOKE,
        r_max=R_MAX_SMOKE,
        valores_n=[10, 20, 30, 40],
        n_repeticiones=N_REPETICIONES_SMOKE,
        seed=1,
    )
    print(df_n_libre)

    print("\nCorriendo experimento_variacion_N_densidad_fija (smoke test)...")
    df_n_fija = experimento_variacion_N_densidad_fija(
        l_inicial=5.0,
        n_inicial=10,
        rc=RC_SMOKE,
        r_min=R_MIN_SMOKE,
        r_max=R_MAX_SMOKE,
        factores_escala=[1, 2, 3],
        n_repeticiones=N_REPETICIONES_SMOKE,
        seed=1,
    )
    print(df_n_fija)

    ax_n = graficar_variacion_N(
        df_n_fija, df_n_libre, titulo="Tiempo vs N (smoke test)"
    )
    guardar_figura(ax_n.figure, "benchmark_variacion_N")

    print("\nFiguras guardadas en figures/benchmark_variacion_M.png y "
          "figures/benchmark_variacion_N.png")
