"""Visualización de partículas y resultados de las simulaciones.

Este módulo contiene funciones para graficar la disposición espacial de las
partículas (dibujando cada una como un círculo a escala real, según su
radio), resaltar una partícula y sus vecinas, y guardar las figuras
generadas en disco.
"""

import os
from typing import List, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle

COLOR_NEUTRO = "steelblue"
COLOR_VECINO = "orange"
COLOR_SELECCIONADA = "red"


def graficar_particulas(
    posiciones: np.ndarray,
    radios: np.ndarray,
    l: float,
    particula_id: Optional[int] = None,
    vecinos: Optional[Sequence[int]] = None,
    ax: Optional[Axes] = None,
    mostrar_grilla: bool = False,
    m: Optional[int] = None,
    titulo: Optional[str] = None,
) -> Axes:
    """Grafica las partículas como círculos a escala real en el espacio L x L.

    Cada partícula se dibuja con `matplotlib.patches.Circle`, usando su
    radio real, para poder verificar visualmente superposiciones y
    relaciones de vecindad. Opcionalmente resalta una partícula puntual
    (`particula_id`) y su conjunto de vecinas (`vecinos`), y puede
    superponer las líneas de la grilla de celdas usada por el CIM.

    Args:
        posiciones: Array (N, 2) con las coordenadas (x, y) de cada
            partícula (mismo formato que devuelve
            `particles.generar_particulas()["posiciones"]`).
        radios: Array (N,) con el radio de cada partícula (mismo formato
            que `particles.generar_particulas()["radios"]`).
        l: Longitud del lado del espacio de simulación (cuadrado L x L).
        particula_id: Índice opcional de una partícula a resaltar con un
            color distinto (rojo).
        vecinos: Lista opcional de índices de partículas vecinas de
            `particula_id`, a resaltar con otro color (naranja). El resto
            de las partículas se dibuja en un color neutro.
        ax: Axes de matplotlib donde dibujar. Si es None, se crea una
            figura y un Axes nuevos.
        mostrar_grilla: Si es True (y se pasa `m`), dibuja las líneas de
            la grilla de celdas L/M en cada dirección, como referencia
            visual para debug del CIM.
        m: Cantidad de celdas por lado de la grilla, usado únicamente si
            `mostrar_grilla=True`.
        titulo: Título opcional para el gráfico.

    Returns:
        El Axes de matplotlib utilizado, para poder seguir customizando
        el gráfico desde afuera.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    vecinos_set = set(vecinos) if vecinos is not None else set()

    for i, (pos, radio) in enumerate(zip(posiciones, radios)):
        if i == particula_id:
            color = COLOR_SELECCIONADA
        elif i in vecinos_set:
            color = COLOR_VECINO
        else:
            color = COLOR_NEUTRO

        circulo = Circle(pos, radio, facecolor=color, edgecolor="black", linewidth=0.5, alpha=0.8)
        ax.add_patch(circulo)

    if mostrar_grilla and m is not None:
        paso = l / m
        for k in range(m + 1):
            ax.axvline(k * paso, color="gray", linewidth=0.5, linestyle="--", zorder=0)
            ax.axhline(k * paso, color="gray", linewidth=0.5, linestyle="--", zorder=0)

    ax.set_xlim(0, l)
    ax.set_ylim(0, l)
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if titulo is not None:
        ax.set_title(titulo)

    return ax


_EXTENSIONES_VALIDAS = {".png", ".jpg", ".jpeg", ".pdf", ".svg", ".eps", ".tif", ".tiff"}


def guardar_figura(fig: Figure, nombre: str, carpeta: str = "figures") -> str:
    """Guarda una figura de matplotlib en disco con buena resolución.

    Args:
        fig: Figura de matplotlib a guardar.
        nombre: Nombre del archivo a generar (con o sin extensión de
            imagen; si no termina en una extensión reconocida se le
            agrega .png). Nombres con puntos que no forman una extensión
            de imagen válida (por ejemplo "rc1.0") no se confunden con
            una extensión.
        carpeta: Carpeta donde guardar la figura. Se crea si no existe.

    Returns:
        La ruta completa del archivo generado.
    """
    os.makedirs(carpeta, exist_ok=True)

    extension = os.path.splitext(nombre)[1].lower()
    if extension not in _EXTENSIONES_VALIDAS:
        nombre = f"{nombre}.png"

    path = os.path.join(carpeta, nombre)
    fig.savefig(path, dpi=150, bbox_inches="tight")

    return path


if __name__ == "__main__":
    from src.cim import buscar_vecinos_cim, calcular_M_max
    from src.particles import generar_particulas

    n = 30
    lado = 10.0
    rc = 1.0
    resultado = generar_particulas(n, lado=lado, seed=42)
    posiciones = resultado["posiciones"]
    radios = resultado["radios"]

    rng = np.random.default_rng(42)
    particula_id = int(rng.integers(0, n))

    m = calcular_M_max(lado, rc, float(radios.max()))
    vecinos_por_particula = buscar_vecinos_cim(posiciones, radios, lado, m, rc)
    vecinos_ejemplo: List[int] = vecinos_por_particula[particula_id]

    ax = graficar_particulas(
        posiciones,
        radios,
        lado,
        particula_id=particula_id,
        vecinos=vecinos_ejemplo,
        mostrar_grilla=True,
        m=m,
        titulo=f"Ejemplo: partícula {particula_id} y sus vecinas (rc={rc}, M={m})",
    )

    path_generado = guardar_figura(ax.figure, "ejemplo_visualize")
    print(f"Figura guardada en: {path_generado}")
