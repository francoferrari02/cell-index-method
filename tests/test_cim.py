"""Tests para el módulo src.cim."""

import time

import numpy as np
import pytest

from src.cim import (
    MInvalidoError,
    buscar_vecinos_cim,
    buscar_vecinos_fuerza_bruta,
    calcular_M_max,
    construir_celdas,
)
from src.particles import generar_particulas


def _normalizar(vecinos):
    """Convierte {id: [vecinos]} a {id: frozenset(vecinos)} para comparar
    sin importar el orden en el que se agregaron los índices."""
    return {i: frozenset(v) for i, v in vecinos.items()}


def test_construir_celdas_asigna_todas_las_particulas():
    """Todas las partículas deben quedar asignadas a alguna celda."""
    resultado = generar_particulas(40, lado=10.0, seed=1)
    posiciones = resultado["posiciones"]

    celdas = construir_celdas(posiciones, l=10.0, m=4)

    indices_asignados = sorted(
        idx for indices in celdas.values() for idx in indices
    )
    assert indices_asignados == list(range(40))

    # Todas las claves deben ser celdas válidas dentro de la grilla.
    for fila, col in celdas:
        assert 0 <= fila < 4
        assert 0 <= col < 4


def test_construir_celdas_particula_en_borde_l():
    """Una partícula justo en x=L (o y=L) debe caer en la última celda."""
    posiciones = np.array([[10.0, 10.0], [0.0, 0.0]])
    celdas = construir_celdas(posiciones, l=10.0, m=5)

    # La partícula 0 (en x=L, y=L) debe estar en la celda (4, 4), no fuera
    # de rango.
    assert 0 in celdas[(4, 4)]
    assert 1 in celdas[(0, 0)]


@pytest.mark.parametrize("n", [10, 100])
@pytest.mark.parametrize("periodic", [False, True])
def test_cim_coincide_con_fuerza_bruta(n, periodic):
    """El CIM debe encontrar exactamente los mismos vecinos que fuerza bruta,
    para distintos M válidos (incluyendo M=1)."""
    lado = 10.0
    rc = 0.3
    resultado = generar_particulas(n, lado=lado, seed=n * 10 + int(periodic))
    posiciones = resultado["posiciones"]
    radios = resultado["radios"]

    r_max = float(np.max(radios))
    m_max = calcular_M_max(lado, rc, r_max)

    esperado = _normalizar(
        buscar_vecinos_fuerza_bruta(posiciones, radios, lado, rc, periodic=periodic)
    )

    for m in sorted({1, 2, m_max}):
        if m > m_max:
            continue
        obtenido = _normalizar(
            buscar_vecinos_cim(posiciones, radios, lado, m, rc, periodic=periodic)
        )
        assert obtenido == esperado, f"Difiere con M={m}, periodic={periodic}"


def test_m_mayor_a_m_max_lanza_excepcion():
    """Si M > M_max, buscar_vecinos_cim debe lanzar MInvalidoError."""
    lado = 10.0
    rc = 0.3
    resultado = generar_particulas(20, lado=lado, seed=99)
    posiciones = resultado["posiciones"]
    radios = resultado["radios"]

    r_max = float(np.max(radios))
    m_max = calcular_M_max(lado, rc, r_max)

    with pytest.raises(MInvalidoError):
        buscar_vecinos_cim(posiciones, radios, lado, m_max + 1, rc)


def test_calcular_m_max_valor_esperado():
    """calcular_M_max debe seguir rc_efectivo = rc + 2*r_max."""
    # L=10, rc=0.3, r_max=0.2 -> rc_efectivo=0.7 -> M_max=floor(10/0.7)=14
    assert calcular_M_max(l=10.0, rc=0.3, r_max=0.2) == 14

    # Caso degenerado donde rc_efectivo > L: M_max debe seguir siendo >= 1.
    assert calcular_M_max(l=1.0, rc=5.0, r_max=5.0) == 1


def test_caso_manual_borde_borde():
    """Caso armado a mano: 3 partículas en línea, se verifica el criterio
    de distancia borde-borde a ojo.

    p0 = (1.0, 1.0), r=0.5
    p1 = (2.5, 1.0), r=0.5  -> dist. centros con p0 = 1.5, borde-borde = 0.5
    p2 = (5.0, 1.0), r=0.5  -> dist. centros con p1 = 2.5, borde-borde = 1.5
                              -> dist. centros con p0 = 4.0, borde-borde = 3.0

    Con rc=0.6: solo (0, 1) son vecinas (0.5 < 0.6); (1, 2) y (0, 2) no
    (1.5 y 3.0, ambas >= 0.6).
    """
    posiciones = np.array([[1.0, 1.0], [2.5, 1.0], [5.0, 1.0]])
    radios = np.array([0.5, 0.5, 0.5])
    lado = 10.0
    rc = 0.6

    esperado = {0: frozenset({1}), 1: frozenset({0}), 2: frozenset()}

    obtenido_bf = _normalizar(buscar_vecinos_fuerza_bruta(posiciones, radios, lado, rc))
    assert obtenido_bf == esperado

    # M=2 hace que p2 (x=5.0, col=1) quede en una celda distinta a p0/p1
    # (x=1.0 y 2.5, col=0), ejercitando la comparación entre celdas
    # vecinas y el manejo del borde x=L/M=5.0 exacto.
    obtenido_cim = _normalizar(buscar_vecinos_cim(posiciones, radios, lado, m=2, rc=rc))
    assert obtenido_cim == esperado


def test_periodico_vecinas_por_borde_opuesto():
    """Dos partículas cerca de bordes opuestos deben ser vecinas solo si
    periodic=True (la distancia "corta" es a través del borde)."""
    lado = 10.0
    posiciones = np.array([[0.1, 5.0], [9.9, 5.0]])
    radios = np.array([0.1, 0.1])
    rc = 0.1

    # No periódico: distancia centros = 9.8, borde-borde = 9.6 -> no vecinas.
    no_periodico_bf = buscar_vecinos_fuerza_bruta(posiciones, radios, lado, rc, periodic=False)
    assert no_periodico_bf[0] == []
    assert no_periodico_bf[1] == []

    no_periodico_cim = buscar_vecinos_cim(posiciones, radios, lado, m=5, rc=rc, periodic=False)
    assert no_periodico_cim[0] == []
    assert no_periodico_cim[1] == []

    # Periódico: distancia mínima imagen = 0.2, borde-borde = 0.0 < rc -> vecinas.
    periodico_bf = buscar_vecinos_fuerza_bruta(posiciones, radios, lado, rc, periodic=True)
    assert periodico_bf[0] == [1]
    assert periodico_bf[1] == [0]

    periodico_cim = buscar_vecinos_cim(posiciones, radios, lado, m=5, rc=rc, periodic=True)
    assert periodico_cim[0] == [1]
    assert periodico_cim[1] == [0]


def test_buscar_vecinos_cim_m1_es_rapido_para_n_grande():
    """Regresión de performance: buscar_vecinos_cim con M=1 (fuerza bruta
    vía CIM) para N=1140 debe estar vectorizado, no ser un loop de Python
    puro sobre ~650k pares.

    Antes de vectorizar la comparación de distancias (ver diagnóstico:
    doble for en Python puro llamando a una función auxiliar por par),
    esta llamada tardaba ~0.55s. Vectorizada con numpy debería tardar
    milisegundos; se deja un margen amplio (0.05s, ~10x el tiempo
    vectorizado esperado) para no hacer el test frágil ante variaciones
    de hardware, pero sigue detectando si se reintroduce un loop puro.
    """
    lado, rc = 20.0, 1.0
    particulas = generar_particulas(
        1140, lado=lado, r_min=0.23, r_max=0.26, seed=42, max_intentos=2_000_000
    )
    posiciones, radios = particulas["posiciones"], particulas["radios"]

    inicio = time.perf_counter()
    buscar_vecinos_cim(posiciones, radios, lado, m=1, rc=rc)
    tiempo = time.perf_counter() - inicio

    assert tiempo < 0.05, f"buscar_vecinos_cim(M=1) tardó {tiempo:.4f}s (esperado < 0.05s)"
