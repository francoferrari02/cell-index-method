"""Utilidades de entrada/salida para los archivos del TP1 (punto 5).

Formatos soportados:

Archivo ESTÁTICO (configuración fija del sistema)::

    N
    L
    r1 pr1
    r2 pr2
    ...
    rN prN

`N` es la cantidad de partículas, `L` el lado del área de simulación, y
cada línea siguiente tiene el radio y una "propiedad" (numérica,
genérica, no usada por el CIM) de esa partícula.

Archivo DINÁMICO (uno o más estados en el tiempo)::

    t0
    x1 y1 vx1 vy1
    x2 y2 vx2 vy2
    ...
    xN yN vxN vyN
    t1
    x1 y1 vx1 vy1
    ...

Una línea con un único valor numérico marca el inicio de un nuevo bloque
de tiempo; las líneas siguientes (con 4 valores: posición y velocidad)
pertenecen a ese bloque, hasta la próxima línea de timestamp o el fin del
archivo. Este TP solo usa un t0, pero el parser soporta múltiples
bloques pensando en la reutilización en TPs futuros con dinámica real.

Archivo de VECINOS (salida de cim.buscar_vecinos_cim /
buscar_vecinos_fuerza_bruta)::

    id_particula_i [ids de vecinas separados por espacio]
    ...

Una línea por partícula (en orden ascendente de id), con el id seguido
de los ids de sus vecinas separados por espacios (o solo el id, si no
tiene vecinas).
"""

from typing import Any, Dict, List, Optional

import numpy as np


def _leer_lineas_no_vacias(path: str) -> List[str]:
    """Lee un archivo y devuelve sus líneas no vacías, sin el salto de línea."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lineas = [linea.strip() for linea in f]
    except OSError as exc:
        raise ValueError(f"No se pudo abrir '{path}': {exc}") from exc
    return [linea for linea in lineas if linea != ""]


def _parsear_floats(partes: List[str], cantidad_esperada: int, contexto: str) -> List[float]:
    """Convierte una lista de tokens a floats, con mensaje de error claro."""
    if len(partes) != cantidad_esperada:
        raise ValueError(
            f"{contexto}: se esperaban {cantidad_esperada} valores, se "
            f"encontraron {len(partes)}: {' '.join(partes)!r}"
        )
    try:
        return [float(p) for p in partes]
    except ValueError as exc:
        raise ValueError(f"{contexto}: valores no numéricos ({' '.join(partes)!r})") from exc


def leer_archivo_estatico(path: str) -> Dict[str, Any]:
    """Lee un archivo estático (N, L, y radio+propiedad por partícula).

    Args:
        path: Ruta al archivo estático de entrada.

    Returns:
        Diccionario {"n": int, "l": float, "radios": np.ndarray (N,),
        "propiedades": np.ndarray (N,)}.

    Raises:
        ValueError: si el archivo no tiene al menos las líneas de N y L,
            si N o L no son numéricos, si la cantidad de líneas de
            partículas no coincide con N, o si alguna línea de partícula
            no tiene exactamente 2 valores numéricos (radio, propiedad).
    """
    lineas = _leer_lineas_no_vacias(path)

    if len(lineas) < 2:
        raise ValueError(
            f"'{path}': archivo estático inválido, se esperaban al menos "
            f"2 líneas (N y L), se encontraron {len(lineas)}"
        )

    try:
        n = int(float(lineas[0]))
    except ValueError as exc:
        raise ValueError(f"'{path}': N (primera línea) no es un entero válido: {lineas[0]!r}") from exc

    try:
        l = float(lineas[1])
    except ValueError as exc:
        raise ValueError(f"'{path}': L (segunda línea) no es un número válido: {lineas[1]!r}") from exc

    lineas_particulas = lineas[2:]
    if len(lineas_particulas) != n:
        raise ValueError(
            f"'{path}': el archivo declara N={n} partículas pero tiene "
            f"{len(lineas_particulas)} líneas de datos de partículas"
        )

    radios = np.empty(n, dtype=float)
    propiedades = np.empty(n, dtype=float)
    for i, linea in enumerate(lineas_particulas):
        r, pr = _parsear_floats(
            linea.split(), 2, f"'{path}': línea de partícula #{i} ('{linea}')"
        )
        radios[i] = r
        propiedades[i] = pr

    return {"n": n, "l": l, "radios": radios, "propiedades": propiedades}


def escribir_archivo_estatico(
    path: str,
    n: int,
    l: float,
    radios: np.ndarray,
    propiedades: Optional[np.ndarray] = None,
) -> None:
    """Escribe un archivo estático con el formato N / L / (radio, propiedad)*.

    Args:
        path: Ruta del archivo a generar.
        n: Cantidad de partículas.
        l: Lado del área de simulación.
        radios: Array (N,) con el radio de cada partícula.
        propiedades: Array (N,) con la propiedad de cada partícula. Si es
            None, se escribe 0.0 para todas.

    Raises:
        ValueError: si `radios` (o `propiedades`, si se pasa) no tienen
            longitud N.
    """
    if len(radios) != n:
        raise ValueError(f"len(radios)={len(radios)} no coincide con n={n}")

    if propiedades is None:
        propiedades = np.zeros(n, dtype=float)
    elif len(propiedades) != n:
        raise ValueError(f"len(propiedades)={len(propiedades)} no coincide con n={n}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{n}\n")
        f.write(f"{l}\n")
        for r, pr in zip(radios, propiedades):
            f.write(f"{r} {pr}\n")


def leer_archivo_dinamico(path: str) -> List[Dict[str, Any]]:
    """Lee un archivo dinámico con uno o más bloques de tiempo.

    Args:
        path: Ruta al archivo dinámico de entrada.

    Returns:
        Lista de diccionarios, uno por bloque de tiempo, cada uno con
        {"t": float, "posiciones": np.ndarray (N,2), "velocidades":
        np.ndarray (N,2)}.

    Raises:
        ValueError: si el archivo está vacío, si una línea de timestamp
            esperada no tiene exactamente un valor numérico, si una
            línea de partícula no tiene exactamente 4 valores numéricos
            (x, y, vx, vy), o si los bloques de tiempo no tienen todos la
            misma cantidad de partículas.
    """
    lineas = _leer_lineas_no_vacias(path)
    if not lineas:
        raise ValueError(f"'{path}': archivo dinámico vacío")

    bloques: List[Dict[str, Any]] = []
    n_esperado: Optional[int] = None
    i = 0

    while i < len(lineas):
        partes_t = lineas[i].split()
        if len(partes_t) != 1:
            raise ValueError(
                f"'{path}': se esperaba una línea de timestamp (un único "
                f"valor) en la posición {i}, se encontró: {lineas[i]!r}"
            )
        try:
            t = float(partes_t[0])
        except ValueError as exc:
            raise ValueError(f"'{path}': timestamp no numérico: {lineas[i]!r}") from exc
        i += 1

        filas_bloque: List[str] = []
        while i < len(lineas) and len(lineas[i].split()) != 1:
            filas_bloque.append(lineas[i])
            i += 1

        if not filas_bloque:
            raise ValueError(f"'{path}': el bloque de tiempo t={t} no tiene partículas")

        n_bloque = len(filas_bloque)
        if n_esperado is None:
            n_esperado = n_bloque
        elif n_bloque != n_esperado:
            raise ValueError(
                f"'{path}': el bloque t={t} tiene {n_bloque} partículas, "
                f"se esperaban {n_esperado} (según el primer bloque leído)"
            )

        posiciones = np.empty((n_bloque, 2), dtype=float)
        velocidades = np.empty((n_bloque, 2), dtype=float)
        for j, fila in enumerate(filas_bloque):
            x, y, vx, vy = _parsear_floats(
                fila.split(), 4, f"'{path}': línea de partícula #{j} del bloque t={t} ('{fila}')"
            )
            posiciones[j] = (x, y)
            velocidades[j] = (vx, vy)

        bloques.append({"t": t, "posiciones": posiciones, "velocidades": velocidades})

    return bloques


def escribir_archivo_dinamico(path: str, tiempos_datos: List[Dict[str, Any]]) -> None:
    """Escribe un archivo dinámico a partir de una lista de bloques de tiempo.

    Args:
        path: Ruta del archivo a generar.
        tiempos_datos: Lista de diccionarios {"t": float, "posiciones":
            np.ndarray (N,2), "velocidades": np.ndarray (N,2)} (mismo
            formato que devuelve `leer_archivo_dinamico`).

    Raises:
        ValueError: si en algún bloque `posiciones` y `velocidades` no
            tienen la misma cantidad de filas.
    """
    with open(path, "w", encoding="utf-8") as f:
        for bloque in tiempos_datos:
            posiciones = bloque["posiciones"]
            velocidades = bloque["velocidades"]
            if len(posiciones) != len(velocidades):
                raise ValueError(
                    f"Bloque t={bloque['t']}: posiciones tiene "
                    f"{len(posiciones)} filas y velocidades {len(velocidades)}"
                )
            f.write(f"{bloque['t']}\n")
            for (x, y), (vx, vy) in zip(posiciones, velocidades):
                f.write(f"{x} {y} {vx} {vy}\n")


def escribir_vecinos(path: str, dict_vecinos: Dict[int, List[int]]) -> None:
    """Escribe el diccionario de vecinos en el formato "id v1 v2 ...".

    Args:
        path: Ruta del archivo a generar.
        dict_vecinos: Diccionario {id_particula: [ids de vecinas]}, como
            el que devuelven `cim.buscar_vecinos_cim` /
            `cim.buscar_vecinos_fuerza_bruta`.
    """
    with open(path, "w", encoding="utf-8") as f:
        for id_particula in sorted(dict_vecinos.keys()):
            vecinas = dict_vecinos[id_particula]
            tokens = [str(id_particula)] + [str(v) for v in vecinas]
            f.write(" ".join(tokens) + "\n")


def leer_vecinos(path: str) -> Dict[int, List[int]]:
    """Lee un archivo de vecinos generado por `escribir_vecinos`.

    Args:
        path: Ruta del archivo a leer.

    Returns:
        Diccionario {id_particula: [ids de vecinas]}.

    Raises:
        ValueError: si alguna línea tiene valores no enteros, o está vacía
            (sin ni siquiera el id de partícula).
    """
    lineas = _leer_lineas_no_vacias(path)
    dict_vecinos: Dict[int, List[int]] = {}

    for i, linea in enumerate(lineas):
        partes = linea.split()
        if not partes:
            raise ValueError(f"'{path}': línea #{i} vacía, se esperaba al menos el id de partícula")
        try:
            valores = [int(p) for p in partes]
        except ValueError as exc:
            raise ValueError(f"'{path}': línea #{i} tiene valores no enteros: {linea!r}") from exc

        id_particula, *vecinas = valores
        dict_vecinos[id_particula] = vecinas

    return dict_vecinos
