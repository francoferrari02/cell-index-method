"""Exploración del N máximo generable con particles.generar_particulas().

Script exploratorio (no forma parte de la suite de tests) para el punto 4
del TP: busca, para L=20 y radios U[0.23, 0.26], el N más grande que el
rejection sampling de `particles.generar_particulas()` todavía puede
resolver en un tiempo razonable, antes de que la tasa de rechazo se
dispare (o directamente falle con GeneracionParticulasError).

Estrategia:
    1. Búsqueda exponencial: arranca en N=500 y va duplicando hasta
       encontrar un N que falle o tarde más que TIMEOUT_S segundos.
    2. Búsqueda binaria entre el último N exitoso y el primer N fallido,
       para acotar el N máximo con más precisión.
    3. Corrida final de confirmación en el N encontrado.

Cada intento de generación se corre con un timeout real de pared
(usando `signal.alarm`, disponible en macOS/Linux) para no quedar
esperando indefinidamente si el rejection sampling entra en una zona de
altísimo rechazo.
"""

import math
import signal
import time
from typing import Optional, Tuple

import numpy as np

from src.particles import GeneracionParticulasError, calcular_densidad, generar_particulas

L = 20.0
R_MIN, R_MAX = 0.23, 0.26
SEED = 42
TIMEOUT_S = 10
MAX_INTENTOS = 5_000_000  # límite alto: dejamos que el timeout de pared corte antes.
DENSIDAD_HEXAGONAL_COMPACTA = math.pi / (2 * math.sqrt(3))  # ~0.9069, fracción de ÁREA


class _TimeoutError(Exception):
    pass


def _manejador_alarma(signum, frame):
    raise _TimeoutError


def intentar_generar(
    n: int, timeout_s: int = TIMEOUT_S
) -> Tuple[bool, float, Optional[np.ndarray]]:
    """Intenta generar N partículas, con timeout de pared.

    Returns:
        (exito, tiempo_segundos, radios): exito=False si se superó el
        timeout o si generar_particulas lanzó GeneracionParticulasError;
        en ese caso radios es None.
    """
    signal.signal(signal.SIGALRM, _manejador_alarma)
    signal.alarm(timeout_s)
    inicio = time.perf_counter()
    try:
        resultado = generar_particulas(
            n, lado=L, r_min=R_MIN, r_max=R_MAX, seed=SEED, max_intentos=MAX_INTENTOS
        )
        return True, time.perf_counter() - inicio, resultado["radios"]
    except _TimeoutError:
        return False, time.perf_counter() - inicio, None
    except GeneracionParticulasError:
        return False, time.perf_counter() - inicio, None
    finally:
        signal.alarm(0)


def buscar_n_max() -> None:
    print(f"Buscando N máximo para L={L}, r in [{R_MIN}, {R_MAX}], "
          f"timeout por intento={TIMEOUT_S}s\n")

    # --- Fase 1: búsqueda exponencial ---
    n_ok = 0
    tiempo_ok = 0.0
    n = 500
    n_fail = None

    while True:
        print(f"Probando N={n}...", end=" ", flush=True)
        exito, tiempo, _ = intentar_generar(n)
        print(f"{'OK' if exito else 'FALLA/TIMEOUT'} ({tiempo:.2f}s)")

        if exito:
            n_ok, tiempo_ok = n, tiempo
            n *= 2
        else:
            n_fail = n
            break

    # --- Fase 2: búsqueda binaria entre n_ok (éxito) y n_fail (falla) ---
    print(f"\nAcotado entre N_ok={n_ok} y N_fail={n_fail}. Refinando con búsqueda binaria...\n")

    lo, hi = n_ok, n_fail
    while hi - lo > max(1, n_ok // 100):  # precisión ~1% del N_ok encontrado
        medio = (lo + hi) // 2
        print(f"Probando N={medio}...", end=" ", flush=True)
        exito, tiempo, _ = intentar_generar(medio)
        print(f"{'OK' if exito else 'FALLA/TIMEOUT'} ({tiempo:.2f}s)")

        if exito:
            lo, tiempo_ok = medio, tiempo
        else:
            hi = medio

    n_max = lo

    # --- Confirmación final ---
    print(f"\nConfirmando N_max={n_max}...")
    exito, tiempo_final, radios = intentar_generar(n_max, timeout_s=TIMEOUT_S * 2)

    densidad_numerica = calcular_densidad(n_max, L)  # N / L^2 (1/área, no adimensional)
    fraccion_area = float(np.sum(np.pi * radios**2) / L**2)  # área ocupada / área total

    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"N máximo generable (dentro de ~{TIMEOUT_S}s por intento): {n_max}")
    print(f"Tiempo de generación en la confirmación: {tiempo_final:.2f} s")
    print(f"Densidad numérica (N / L^2): {densidad_numerica:.4f} partículas/u²")
    print(f"Fracción de área ocupada (Σ π r_i² / L²): {fraccion_area:.4f}")
    print(f"Densidad de empaquetamiento hexagonal compacto (2D, círculos "
          f"iguales): {DENSIDAD_HEXAGONAL_COMPACTA:.4f}")
    print(f"Fracción del límite teórico alcanzada: "
          f"{fraccion_area / DENSIDAD_HEXAGONAL_COMPACTA * 100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    buscar_n_max()
