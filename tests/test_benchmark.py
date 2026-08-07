"""Tests para el módulo src.benchmark."""

import time

import numpy as np
import pytest

from src.benchmark import (
    correr_experimento_repetido,
    experimento_variacion_M,
    experimento_variacion_N,
    experimento_variacion_N_densidad_fija,
)
from src.cim import calcular_M_max
from src.particles import generar_particulas


def _funcion_dummy(duracion: float) -> None:
    """Función de prueba que tarda aproximadamente `duracion` segundos."""
    time.sleep(duracion)


def test_correr_experimento_repetido_con_funcion_dummy():
    """El promedio medido debe acercarse a la duración conocida de la
    función dummy, y el desvío estándar debe ser un número no negativo."""
    duracion = 0.02
    promedio, std = correr_experimento_repetido(
        _funcion_dummy, (duracion,), n_repeticiones=5
    )

    assert promedio == pytest.approx(duracion, abs=0.02)
    assert std >= 0


def test_experimento_variacion_M_estructura_resultado():
    """El DataFrame debe tener una fila por cada M de 1 a M_max, con
    tiempos positivos."""
    n, l, rc = 15, 8.0, 0.5
    r_min, r_max = 0.23, 0.26
    seed = 1

    df = experimento_variacion_M(
        n=n, l=l, rc=rc, r_min=r_min, r_max=r_max, n_repeticiones=3, seed=seed
    )

    # Recalculamos M_max de forma independiente, regenerando las mismas
    # partículas (mismo seed => mismos radios, por reproducibilidad).
    particulas = generar_particulas(n, lado=l, r_min=r_min, r_max=r_max, seed=seed)
    m_max_esperado = calcular_M_max(l, rc, float(particulas["radios"].max()))

    assert list(df["M"]) == list(range(1, m_max_esperado + 1))
    assert (df["tiempo_promedio"] > 0).all()
    assert (df["tiempo_std"] >= 0).all()


def test_experimento_variacion_N_estructura_resultado():
    """El DataFrame debe tener una fila por cada N pedido, con las
    columnas esperadas."""
    valores_n = [10, 15, 20]
    l, rc = 8.0, 0.5

    df = experimento_variacion_N(
        l=l,
        rc=rc,
        r_min=0.23,
        r_max=0.26,
        valores_n=valores_n,
        n_repeticiones=3,
        seed=2,
    )

    assert list(df["N"]) == valores_n
    assert {"N", "M_usado", "tiempo_promedio", "tiempo_std", "densidad", "alcanzado"} <= set(
        df.columns
    )
    assert df["alcanzado"].all()
    assert (df["tiempo_promedio"] > 0).all()
    assert (df["tiempo_std"] >= 0).all()

    densidades_esperadas = [n / l**2 for n in valores_n]
    np.testing.assert_allclose(df["densidad"].to_numpy(), densidades_esperadas)


def test_experimento_variacion_N_densidad_fija_mantiene_densidad():
    """Al escalar N y L juntos, la densidad debe mantenerse (aprox) igual
    en todas las filas."""
    l_inicial, n_inicial = 5.0, 10
    densidad_esperada = n_inicial / l_inicial**2

    df = experimento_variacion_N_densidad_fija(
        l_inicial=l_inicial,
        n_inicial=n_inicial,
        rc=0.5,
        r_min=0.23,
        r_max=0.26,
        factores_escala=[1, 2],
        n_repeticiones=2,
        seed=3,
    )

    assert df["alcanzado"].all()
    np.testing.assert_allclose(
        df["densidad"].to_numpy(), [densidad_esperada] * len(df), rtol=1e-9
    )
    assert (df["tiempo_promedio"] > 0).all()
