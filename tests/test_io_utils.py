"""Tests para el módulo src.io_utils."""

import os

import numpy as np
import pytest

from src.cim import buscar_vecinos_cim, calcular_M_max
from src.io_utils import (
    escribir_archivo_dinamico,
    escribir_archivo_estatico,
    escribir_vecinos,
    leer_archivo_dinamico,
    leer_archivo_estatico,
    leer_vecinos,
)
from src.particles import generar_particulas


def test_roundtrip_archivo_estatico_propiedades_default(tmp_path):
    """Escribir y releer un archivo estático sin propiedades explícitas
    debe dar radios idénticos y propiedades en 0.0."""
    resultado = generar_particulas(8, lado=5.0, seed=1)
    radios = resultado["radios"]
    path = tmp_path / "estatico.txt"

    escribir_archivo_estatico(str(path), n=8, l=5.0, radios=radios)
    leido = leer_archivo_estatico(str(path))

    assert leido["n"] == 8
    assert leido["l"] == pytest.approx(5.0)
    np.testing.assert_allclose(leido["radios"], radios)
    np.testing.assert_allclose(leido["propiedades"], np.zeros(8))


def test_roundtrip_archivo_estatico_con_propiedades():
    """Escribir y releer un archivo estático con propiedades explícitas
    debe preservarlas."""
    radios = np.array([0.23, 0.24, 0.25, 0.26])
    propiedades = np.array([1.5, -2.0, 0.0, 3.75])
    path = "/tmp/test_estatico_propiedades.txt"

    escribir_archivo_estatico(path, n=4, l=10.0, radios=radios, propiedades=propiedades)
    leido = leer_archivo_estatico(path)

    assert leido["n"] == 4
    assert leido["l"] == pytest.approx(10.0)
    np.testing.assert_allclose(leido["radios"], radios)
    np.testing.assert_allclose(leido["propiedades"], propiedades)

    os.remove(path)


def test_archivo_estatico_n_no_coincide_lanza_error(tmp_path):
    """Si la cantidad de líneas de partículas no coincide con N declarado,
    debe lanzar ValueError con mensaje claro."""
    path = tmp_path / "estatico_malo.txt"
    path.write_text("3\n10.0\n0.23 0.0\n0.24 0.0\n")  # declara N=3, solo 2 líneas

    with pytest.raises(ValueError, match="N=3"):
        leer_archivo_estatico(str(path))


def test_roundtrip_archivo_dinamico_un_bloque(tmp_path):
    """Escribir y releer un archivo dinámico de un solo timestamp debe
    preservar posiciones y velocidades."""
    resultado = generar_particulas(6, lado=5.0, seed=2)
    posiciones = resultado["posiciones"]
    velocidades = np.zeros((6, 2))
    path = tmp_path / "dinamico.txt"

    escribir_archivo_dinamico(str(path), [{"t": 0.0, "posiciones": posiciones, "velocidades": velocidades}])
    bloques = leer_archivo_dinamico(str(path))

    assert len(bloques) == 1
    assert bloques[0]["t"] == pytest.approx(0.0)
    np.testing.assert_allclose(bloques[0]["posiciones"], posiciones)
    np.testing.assert_allclose(bloques[0]["velocidades"], velocidades)


def test_leer_archivo_dinamico_multiples_bloques(tmp_path):
    """El parser debe soportar correctamente múltiples bloques de tiempo."""
    contenido = (
        "0.0\n"
        "1.0 2.0 0.1 0.2\n"
        "3.0 4.0 -0.1 0.0\n"
        "5.0 6.0 0.0 0.3\n"
        "1.0\n"
        "1.1 2.1 0.1 0.2\n"
        "3.1 4.1 -0.1 0.0\n"
        "5.1 6.1 0.0 0.3\n"
    )
    path = tmp_path / "dinamico_multi.txt"
    path.write_text(contenido)

    bloques = leer_archivo_dinamico(str(path))

    assert len(bloques) == 2
    assert bloques[0]["t"] == pytest.approx(0.0)
    assert bloques[1]["t"] == pytest.approx(1.0)
    assert bloques[0]["posiciones"].shape == (3, 2)
    assert bloques[1]["posiciones"].shape == (3, 2)
    np.testing.assert_allclose(bloques[0]["posiciones"][0], [1.0, 2.0])
    np.testing.assert_allclose(bloques[1]["velocidades"][2], [0.0, 0.3])


def test_leer_archivo_dinamico_bloques_con_distinto_n_lanza_error(tmp_path):
    """Si dos bloques tienen distinta cantidad de partículas, ValueError."""
    contenido = (
        "0.0\n"
        "1.0 2.0 0.0 0.0\n"
        "3.0 4.0 0.0 0.0\n"
        "1.0\n"
        "1.1 2.1 0.0 0.0\n"
    )
    path = tmp_path / "dinamico_inconsistente.txt"
    path.write_text(contenido)

    with pytest.raises(ValueError, match="se esperaban 2"):
        leer_archivo_dinamico(str(path))


def test_roundtrip_vecinos_con_cim_real(tmp_path):
    """Escribir y releer vecinos calculados con el CIM real debe dar
    exactamente el mismo diccionario (comparando como conjuntos, ya que
    el orden dentro de cada lista no es relevante)."""
    n, l, rc = 30, 8.0, 0.8
    resultado = generar_particulas(n, lado=l, seed=3)
    posiciones, radios = resultado["posiciones"], resultado["radios"]
    m = calcular_M_max(l, rc, float(radios.max()))

    vecinos = buscar_vecinos_cim(posiciones, radios, l, m, rc)
    path = tmp_path / "vecinos.txt"

    escribir_vecinos(str(path), vecinos)
    leido = leer_vecinos(str(path))

    assert set(leido.keys()) == set(vecinos.keys())
    for id_particula in vecinos:
        assert set(leido[id_particula]) == set(vecinos[id_particula])


def test_leer_vecinos_valores_no_enteros_lanza_error(tmp_path):
    """Si una línea del archivo de vecinos tiene valores no enteros,
    debe lanzar ValueError."""
    path = tmp_path / "vecinos_malo.txt"
    path.write_text("0 1 2\n1 0.5 2\n")

    with pytest.raises(ValueError, match="no enteros"):
        leer_vecinos(str(path))


def test_generar_archivos_de_ejemplo_reales():
    """Genera los archivos de ejemplo reales del TP (N=10) en data/input/
    y data/output/, usando particles.py y cim.py, y verifica que son
    consistentes al releerlos."""
    n, l, rc = 10, 5.0, 1.0
    resultado = generar_particulas(n, lado=l, seed=42)
    posiciones, radios = resultado["posiciones"], resultado["radios"]
    velocidades = np.zeros((n, 2))

    path_estatico = "data/input/ejemplo_estatico.txt"
    path_dinamico = "data/input/ejemplo_dinamico.txt"
    path_vecinos = "data/output/ejemplo_vecinos.txt"

    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)

    escribir_archivo_estatico(path_estatico, n=n, l=l, radios=radios)
    escribir_archivo_dinamico(
        path_dinamico, [{"t": 0.0, "posiciones": posiciones, "velocidades": velocidades}]
    )

    m = calcular_M_max(l, rc, float(radios.max()))
    vecinos = buscar_vecinos_cim(posiciones, radios, l, m, rc)
    escribir_vecinos(path_vecinos, vecinos)

    # Verificación de consistencia round-trip entre los 3 archivos.
    estatico_leido = leer_archivo_estatico(path_estatico)
    assert estatico_leido["n"] == n
    np.testing.assert_allclose(estatico_leido["radios"], radios)

    bloques = leer_archivo_dinamico(path_dinamico)
    assert len(bloques) == 1
    np.testing.assert_allclose(bloques[0]["posiciones"], posiciones)

    vecinos_leidos = leer_vecinos(path_vecinos)
    assert set(vecinos_leidos.keys()) == set(vecinos.keys())

    assert os.path.isfile(path_estatico)
    assert os.path.isfile(path_dinamico)
    assert os.path.isfile(path_vecinos)
