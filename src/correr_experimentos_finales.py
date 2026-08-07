"""Experimentos finales de los puntos 3 y 4 del enunciado del TP1.

Script exploratorio (no forma parte de la suite de tests). Se corre en
dos fases:

    1. estimar_tiempos_generacion(): genera (SIN buscar vecinos todavía)
       las partículas de los casos con N más alto de cada experimento,
       para dar una estimación rápida del costo antes de lanzar todo.
    2. correr_experimentos_finales(): corre los experimentos completos
       de los puntos 3, 4.1 y 4.2, genera y guarda las figuras finales.

Uso:
    python -m src.correr_experimentos_finales            # solo estimación
    python -m src.correr_experimentos_finales --full      # corrida completa

Parámetros y supuestos
-----------------------
- L=20, r ∈ [0.23, 0.26]: dados por el enunciado / usados en el resto
  del TP.
- rc=1.0: NO especificado explícitamente en este pedido. Se usa el mismo
  valor que quedó como default en `main_tp1.py` (`--rc` default 1.0),
  que es el que se usó en los ejemplos anteriores del TP. Si el rc real
  del enunciado es otro, hay que cambiar la constante RC de este archivo
  antes de correr la fase completa.
- N_max=1140: el encontrado en `explorar_n_max.py` para L=20.
- N_intermedio (punto 3) = 1140 // 2 = 570.
- valores_N (punto 4.1): 10 valores espaciados logarítmicamente entre 10
  y 1140 (sin duplicados tras redondear): [10, 17, 29, 48, 82, 139, 235,
  398, 674, 1140].
- Densidad de referencia (punto 4.2): se toma la densidad numérica
  (N/L^2, con L=20) de uno de los N intermedios de la lista de 4.1 (no
  el más alto, para no arrancar cerca del jamming limit): N=82 ->
  densidad_ref = 82/20^2 = 0.205 partículas/u² (fracción de área
  ≈ 0.039, muy lejos del límite práctico ~0.53 encontrado en
  explorar_n_max.py).
- factores_escala (punto 4.2): elegidos para que, partiendo de
  N_inicial=10 y L_inicial=sqrt(N_inicial/densidad_ref), el N resultante
  en cada punto (N_inicial * factor^2) reproduzca EXACTAMENTE los mismos
  10 valores de N que en 4.1, manteniendo la densidad constante en
  densidad_ref. Esto hace que la comparación densidad libre vs densidad
  fija en el gráfico final sea directa, punto a punto por N.
"""

import argparse
import math
import time
from typing import Any, Dict, List

import numpy as np

from src.benchmark import (
    experimento_variacion_M,
    experimento_variacion_N,
    experimento_variacion_N_densidad_fija,
    graficar_variacion_M,
    graficar_variacion_N,
)
from src.particles import generar_particulas
from src.visualize import guardar_figura

L = 20.0
RC = 1.0  # Ver nota de supuestos en el docstring del módulo.
R_MIN, R_MAX = 0.23, 0.26
SEED = 42

N_MAX = 1140
N_INTERMEDIO_P3 = N_MAX // 2  # 570

N_REPETICIONES_P3 = 300
N_REPETICIONES_P4 = 200

# El default de generar_particulas (100_000 intentos) no alcanza para
# N cercanos a N_MAX=1140 en L=20: en explorar_n_max.py hizo falta un
# límite mucho más alto (varios cientos de miles de intentos) para
# lograr generarlas en el tiempo esperado.
MAX_INTENTOS = 2_000_000

VALORES_N_41: List[int] = sorted(
    set(np.round(np.logspace(np.log10(10), np.log10(N_MAX), 10)).astype(int).tolist())
)

# Densidad de referencia para 4.2: uno de los N del medio de la lista de
# 4.1 (no el más alto), evaluado a L=20 (mismo L que en 4.1).
_IDX_DENSIDAD_REF = len(VALORES_N_41) // 2 - 1
N_DENSIDAD_REF = VALORES_N_41[_IDX_DENSIDAD_REF]
DENSIDAD_REF = N_DENSIDAD_REF / L**2

N_INICIAL_42 = VALORES_N_41[0]
L_INICIAL_42 = math.sqrt(N_INICIAL_42 / DENSIDAD_REF)
FACTORES_ESCALA_42: List[float] = [math.sqrt(n / N_INICIAL_42) for n in VALORES_N_41]


def estimar_tiempos_generacion() -> Dict[str, float]:
    """Genera (sin buscar vecinos) los casos de N más alto de cada
    experimento, para estimar el costo total antes de correr todo.

    Returns:
        Diccionario {nombre_caso: tiempo_segundos}.
    """
    print("Estimación de tiempos de generación (SIN búsqueda de vecinos)")
    print(f"L={L}, r=[{R_MIN}, {R_MAX}], seed={SEED}\n")

    l_max_42 = L_INICIAL_42 * FACTORES_ESCALA_42[-1]

    casos = [
        ("Punto 3 - N intermedio", N_INTERMEDIO_P3, L),
        ("Punto 3 - N máximo", N_MAX, L),
        ("Punto 4.1 - N máximo (L=20 fijo)", VALORES_N_41[-1], L),
        (
            "Punto 4.2 - N máximo equivalente (densidad fija, L escalado)",
            VALORES_N_41[-1],
            l_max_42,
        ),
    ]

    tiempos: Dict[str, float] = {}
    total = 0.0
    for nombre, n, l in casos:
        inicio = time.perf_counter()
        generar_particulas(
            n, lado=l, r_min=R_MIN, r_max=R_MAX, seed=SEED, max_intentos=MAX_INTENTOS
        )
        tiempo = time.perf_counter() - inicio
        tiempos[nombre] = tiempo
        total += tiempo
        print(f"  {nombre}: N={n}, L={l:.3f} -> {tiempo:.2f}s")

    print(f"\nSuma de tiempos de generación de estos {len(casos)} casos "
          f"puntuales (los N más altos de cada experimento): {total:.2f}s")
    print(
        "\nNota: esto NO incluye el tiempo de búsqueda de vecinos ni las "
        f"repeticiones ({N_REPETICIONES_P3} en punto 3, {N_REPETICIONES_P4} en "
        "punto 4), solo la "
        "generación de partículas de los casos más pesados."
    )
    return tiempos


def correr_experimentos_finales() -> Dict[str, Any]:
    """Corre los experimentos completos de los puntos 3, 4.1 y 4.2,
    genera y guarda las figuras finales, e imprime un resumen citable.

    Returns:
        Diccionario con los parámetros y tiempos usados en cada
        experimento, y las rutas de las figuras generadas.
    """
    resumen: Dict[str, Any] = {}
    t0_total = time.perf_counter()

    # ------------------------------------------------------------------
    # Punto 3: variación de M
    # ------------------------------------------------------------------
    print("=" * 60)
    print("PUNTO 3: variación de M")
    print("=" * 60)

    t0 = time.perf_counter()
    df_m_intermedio = experimento_variacion_M(
        n=N_INTERMEDIO_P3,
        l=L,
        rc=RC,
        r_min=R_MIN,
        r_max=R_MAX,
        n_repeticiones=N_REPETICIONES_P3,
        seed=SEED,
        max_intentos=MAX_INTENTOS,
    )
    t_m_intermedio = time.perf_counter() - t0
    print(f"N={N_INTERMEDIO_P3} (M de 1 a {df_m_intermedio['M'].max()}): "
          f"{t_m_intermedio:.2f}s")

    t0 = time.perf_counter()
    df_m_maximo = experimento_variacion_M(
        n=N_MAX,
        l=L,
        rc=RC,
        r_min=R_MIN,
        r_max=R_MAX,
        n_repeticiones=N_REPETICIONES_P3,
        seed=SEED,
        max_intentos=MAX_INTENTOS,
    )
    t_m_maximo = time.perf_counter() - t0
    print(f"N={N_MAX} (M de 1 a {df_m_maximo['M'].max()}): {t_m_maximo:.2f}s")

    ax_m = graficar_variacion_M(
        [df_m_intermedio, df_m_maximo],
        labels=[f"N={N_INTERMEDIO_P3}", f"N={N_MAX}"],
        escala_log_y=True,
        titulo="Punto 3: tiempo de búsqueda de vecinos vs M (CIM)",
    )
    path_m = guardar_figura(ax_m.figure, "figura_punto3_variacion_M")
    print(f"Figura guardada en: {path_m}")

    resumen["punto3"] = {
        "N_intermedio": N_INTERMEDIO_P3,
        "M_max_intermedio": int(df_m_intermedio["M"].max()),
        "tiempo_intermedio_s": t_m_intermedio,
        "N_maximo": N_MAX,
        "M_max_maximo": int(df_m_maximo["M"].max()),
        "tiempo_maximo_s": t_m_maximo,
        "n_repeticiones": N_REPETICIONES_P3,
        "rc": RC,
        "l": L,
        "figura": path_m,
    }

    # ------------------------------------------------------------------
    # Punto 4.1: variación de N, densidad libre (L=20 fijo)
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PUNTO 4.1: variación de N (densidad libre, L=20 fijo)")
    print("=" * 60)
    print(f"valores_N = {VALORES_N_41}")

    t0 = time.perf_counter()
    df_n_libre = experimento_variacion_N(
        l=L,
        rc=RC,
        r_min=R_MIN,
        r_max=R_MAX,
        valores_n=VALORES_N_41,
        m=None,
        n_repeticiones=N_REPETICIONES_P4,
        seed=SEED,
        max_intentos=MAX_INTENTOS,
    )
    t_41 = time.perf_counter() - t0
    print(df_n_libre)
    print(f"Tiempo total punto 4.1: {t_41:.2f}s")

    # ------------------------------------------------------------------
    # Punto 4.2: variación de N, densidad fija
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PUNTO 4.2: variación de N (densidad fija)")
    print("=" * 60)
    print(
        f"densidad_ref={DENSIDAD_REF:.4f} (de N={N_DENSIDAD_REF}, L={L}), "
        f"N_inicial={N_INICIAL_42}, L_inicial={L_INICIAL_42:.3f}"
    )
    print(f"factores_escala = {[round(f, 4) for f in FACTORES_ESCALA_42]}")

    t0 = time.perf_counter()
    df_n_fija = experimento_variacion_N_densidad_fija(
        l_inicial=L_INICIAL_42,
        n_inicial=N_INICIAL_42,
        rc=RC,
        r_min=R_MIN,
        r_max=R_MAX,
        factores_escala=FACTORES_ESCALA_42,
        m=None,
        n_repeticiones=N_REPETICIONES_P4,
        seed=SEED,
        max_intentos=MAX_INTENTOS,
    )
    t_42 = time.perf_counter() - t0
    print(df_n_fija)
    print(f"Tiempo total punto 4.2: {t_42:.2f}s")

    ax_n = graficar_variacion_N(
        df_n_fija,
        df_n_libre,
        titulo="Punto 4: tiempo de búsqueda vs N (densidad libre vs densidad fija)",
    )
    path_n = guardar_figura(ax_n.figure, "figura_punto4_completa")
    print(f"Figura guardada en: {path_n}")

    resumen["punto4_1"] = {
        "valores_N": VALORES_N_41,
        "M": "automático (calcular_M_max por punto)",
        "n_repeticiones": N_REPETICIONES_P4,
        "tiempo_total_s": t_41,
        "rc": RC,
        "l": L,
    }
    resumen["punto4_2"] = {
        "densidad_referencia": DENSIDAD_REF,
        "N_referencia_origen": N_DENSIDAD_REF,
        "N_inicial": N_INICIAL_42,
        "L_inicial": L_INICIAL_42,
        "factores_escala": FACTORES_ESCALA_42,
        "M": "automático (calcular_M_max por punto)",
        "n_repeticiones": N_REPETICIONES_P4,
        "tiempo_total_s": t_42,
        "rc": RC,
        "figura": path_n,
    }

    tiempo_total = time.perf_counter() - t0_total
    resumen["tiempo_total_script_s"] = tiempo_total

    print("\n" + "=" * 60)
    print("RESUMEN FINAL (para citar en el informe)")
    print("=" * 60)
    print(f"Parámetros comunes: L={L}, rc={RC}, r∈[{R_MIN}, {R_MAX}], seed={SEED}")
    print(
        f"Punto 3: N_intermedio={N_INTERMEDIO_P3} (tiempo {t_m_intermedio:.2f}s), "
        f"N_maximo={N_MAX} (tiempo {t_m_maximo:.2f}s), "
        f"n_repeticiones={N_REPETICIONES_P3}"
    )
    print(
        f"Punto 4.1: valores_N={VALORES_N_41}, M automático, "
        f"n_repeticiones={N_REPETICIONES_P4}, tiempo total={t_41:.2f}s"
    )
    print(
        f"Punto 4.2: densidad_ref={DENSIDAD_REF:.4f} (de N={N_DENSIDAD_REF}), "
        f"N_inicial={N_INICIAL_42}, L_inicial={L_INICIAL_42:.3f}, "
        f"M automático, n_repeticiones={N_REPETICIONES_P4}, "
        f"tiempo total={t_42:.2f}s"
    )
    print(f"\nFiguras: {path_m}, {path_n}")
    print(f"Tiempo total del script: {tiempo_total:.2f}s ({tiempo_total / 60:.1f} min)")
    print("=" * 60)

    return resumen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Experimentos finales (puntos 3 y 4) del TP1 - CIM."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Corre los experimentos completos. Sin este flag, solo estima "
        "tiempos de generación para los casos más pesados.",
    )
    args = parser.parse_args()

    if args.full:
        correr_experimentos_finales()
    else:
        estimar_tiempos_generacion()
