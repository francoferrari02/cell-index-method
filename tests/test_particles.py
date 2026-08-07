"""Tests para el módulo src.particles."""

import itertools

import numpy as np
import pytest

from src.particles import (
    GeneracionParticulasError,
    calcular_densidad,
    generar_particulas,
)


def test_generar_particulas_cantidad():
    """La cantidad de partículas generadas debe coincidir con N."""
    n = 50
    resultado = generar_particulas(n, lado=10.0, seed=1)

    assert resultado["posiciones"].shape == (n, 2)
    assert resultado["radios"].shape == (n,)


def test_generar_particulas_dentro_del_espacio():
    """Todas las partículas generadas deben estar dentro del lado L."""
    lado = 10.0
    resultado = generar_particulas(50, lado=lado, seed=2)
    posiciones = resultado["posiciones"]
    radios = resultado["radios"]

    # No periódico: cada partícula debe quedar completamente dentro del
    # dominio, es decir su borde no debe salir de [0, L].
    assert np.all(posiciones[:, 0] - radios >= 0)
    assert np.all(posiciones[:, 0] + radios <= lado)
    assert np.all(posiciones[:, 1] - radios >= 0)
    assert np.all(posiciones[:, 1] + radios <= lado)


def test_generar_particulas_sin_superposicion():
    """Ninguna partícula debe superponerse con otra."""
    resultado = generar_particulas(60, lado=10.0, seed=3)
    posiciones = resultado["posiciones"]
    radios = resultado["radios"]
    n = posiciones.shape[0]

    for i, j in itertools.combinations(range(n), 2):
        distancia = np.hypot(*(posiciones[i] - posiciones[j]))
        assert distancia > radios[i] + radios[j]


def test_generar_particulas_reproducibilidad():
    """Con el mismo seed se deben obtener los mismos resultados."""
    resultado_a = generar_particulas(40, lado=10.0, seed=123)
    resultado_b = generar_particulas(40, lado=10.0, seed=123)

    np.testing.assert_array_equal(
        resultado_a["posiciones"], resultado_b["posiciones"]
    )
    np.testing.assert_array_equal(resultado_a["radios"], resultado_b["radios"])


def test_generar_particulas_densidad_imposible_lanza_excepcion():
    """Pedir una densidad imposible debe lanzar GeneracionParticulasError."""
    with pytest.raises(GeneracionParticulasError):
        generar_particulas(
            n=1000,
            lado=0.5,
            r_min=0.23,
            r_max=0.26,
            seed=4,
            max_intentos=2000,
        )


def test_calcular_densidad():
    """calcular_densidad debe devolver N / L^2."""
    assert calcular_densidad(100, 10.0) == pytest.approx(1.0)
    assert calcular_densidad(50, 5.0) == pytest.approx(2.0)
