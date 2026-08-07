# TP1 - Cell Index Method (CIM)

Trabajo Práctico N°1 de la materia **Simulación de Sistemas** (FIUBA).

## Objetivo

Implementar y evaluar el algoritmo **Cell Index Method (CIM)** para la búsqueda
eficiente de partículas vecinas en un sistema de N partículas, comparando su
desempeño contra el método de fuerza bruta en función de la cantidad de
partículas (N) y la cantidad de celdas por lado (M). Las partículas tienen
radio, y el criterio de vecindad es sobre distancia **borde-borde**
(`||centro_i - centro_j|| - (r_i + r_j) < rc`), no centro-centro.

Parámetros por defecto del TP (salvo que se indique lo contrario): `L=20`,
`rc=1`.

## Instalación

1. Crear y activar un entorno virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

## Estructura del proyecto

```
  /
├── src/
│   ├── particles.py                  # Generación de partículas (rejection sampling)
│   ├── cim.py                        # Cell Index Method + fuerza bruta (vectorizados con numpy)
│   ├── brute_force.py                # Stub sin usar: la fuerza bruta terminó viviendo en cim.py
│   ├── io_utils.py                   # Lectura/escritura de archivos estático, dinámico y de vecinos
│   ├── visualize.py                  # Graficado de partículas (círculos a escala real) y guardado de figuras
│   ├── benchmark.py                  # Experimentos de tiempo vs M (punto 3) y vs N (punto 4)
│   ├── main_tp1.py                   # Flujo end-to-end del punto 1 (CLI con argparse)
│   ├── explorar_n_max.py             # Búsqueda del N máximo generable (límite de jamming), script exploratorio
│   └── correr_experimentos_finales.py # Corrida completa de los experimentos de los puntos 3 y 4
├── tests/                            # Tests unitarios (pytest), uno por módulo de src/
├── data/
│   ├── input/                        # Archivos de entrada de ejemplo (estático/dinámico)
│   └── output/                       # Resultados de ejemplo (vecinos, benchmarks)
├── figures/                          # Figuras generadas (partículas, benchmarks)
├── notebooks/                        # Notebooks de exploración (opcional)
├── DESARROLLO.md                     # Bitácora: conflictos encontrados, resoluciones y resultados
└── requirements.txt
```

## Uso

### Correr los tests

```bash
python -m pytest -v
```

### Punto 1 — búsqueda de vecinos de una partícula + gráfico

```bash
python -m src.main_tp1 --n 30 --l 10 --rc 1 --seed 42
```

Genera N partículas, corre el CIM, imprime el tiempo de búsqueda y los
vecinos de una partícula (elegida al azar o con `--particula-id`), y guarda
una figura en `figures/`. Ver `python -m src.main_tp1 --help` para todas las
opciones (`--m`, `--periodic`, etc.).

### N máximo generable

```bash
python -m src.explorar_n_max
```

Busca (búsqueda exponencial + binaria, con timeout real por intento) el N
máximo que `particles.generar_particulas()` puede generar en tiempo
razonable para `L=20`, antes de que el rejection sampling se vuelva
inviable por el límite de *jamming*. Ver `DESARROLLO.md` para el resultado
obtenido y su análisis.

### Experimentos completos (benchmark)

```bash
# Smoke test rápido (parámetros chicos)
python -m src.benchmark

# Corrida completa de los experimentos finales
python -m src.correr_experimentos_finales            # solo estima tiempos de generación
python -m src.correr_experimentos_finales --full      # corre los experimentos completos y guarda las figuras
```

Genera `figures/figura_punto3_variacion_M.png` y
`figures/figura_punto4_completa.png`, e imprime un resumen de tiempos y
parámetros usados en consola (progreso en vivo por cada punto medido).

### Formato de archivos 

`src/io_utils.py` lee y escribe:

- **Estático**: `N`, `L`, y una línea `radio propiedad` por partícula.
- **Dinámico**: uno o más bloques `t`, seguido de `x y vx vy` por partícula.
- **Vecinos**: una línea `id_particula vecino1 vecino2 ...` por partícula.

Hay un caso de ejemplo real (N=10) en `data/input/ejemplo_estatico.txt`,
`data/input/ejemplo_dinamico.txt` y `data/output/ejemplo_vecinos.txt`.

## Resultados y análisis

El desarrollo completo — problemas encontrados (bugs de condiciones
periódicas, cuello de botella de performance y su vectorización, límite de
densidad/jamming, etc.), cómo se resolvieron, y los resultados obtenidos en
cada etapa — está documentado en **[`DESARROLLO.md`](DESARROLLO.md)**.
