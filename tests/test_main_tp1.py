"""Tests para src.main_tp1 (integración end-to-end del punto 1 del TP1)."""

import os

from src.cim import buscar_vecinos_fuerza_bruta
from src.main_tp1 import main
from src.particles import generar_particulas


def test_main_estructura_resultado_y_tiempo_positivo():
    """main() debe devolver la estructura esperada con un tiempo positivo."""
    resultado = main(n=20, l=10.0, rc=1.0, seed=7)

    assert set(resultado.keys()) == {
        "vecinos",
        "todos_los_vecinos",
        "tiempo_segundos",
        "particula_id",
        "m",
        "path_figura",
    }
    assert isinstance(resultado["vecinos"], list)
    assert isinstance(resultado["particula_id"], int)
    assert 0 <= resultado["particula_id"] < 20
    assert resultado["m"] >= 1
    assert resultado["tiempo_segundos"] > 0


def test_main_vecinos_coinciden_con_fuerza_bruta():
    """Los vecinos que reporta main() deben coincidir con fuerza bruta."""
    n, l, rc, seed = 20, 10.0, 1.0, 7

    resultado = main(n=n, l=l, rc=rc, seed=seed)

    # Regeneramos las mismas partículas (mismo seed) para comparar contra
    # el resultado de fuerza bruta de forma independiente al CIM.
    particulas = generar_particulas(n, lado=l, seed=seed)
    esperado = buscar_vecinos_fuerza_bruta(
        particulas["posiciones"], particulas["radios"], l, rc
    )

    particula_id = resultado["particula_id"]
    assert set(resultado["vecinos"]) == set(esperado[particula_id])

    for i in range(n):
        assert set(resultado["todos_los_vecinos"][i]) == set(esperado[i])


def test_main_genera_archivo_de_figura():
    """main() debe generar el archivo de figura en la carpeta figures/."""
    resultado = main(n=20, l=10.0, rc=1.0, seed=7)

    assert os.path.isfile(resultado["path_figura"])
