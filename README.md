# TP1 - Cell Index Method (CIM)

Trabajo Práctico N°1 de la materia **Simulación de Sistemas** (72.25, FIUBA).

## Objetivo

Implementar y evaluar el algoritmo **Cell Index Method (CIM)** para la búsqueda
eficiente de partículas vecinas en un sistema de N partículas, comparando su
desempeño contra el método de fuerza bruta en función de la cantidad de
partículas (N) y la cantidad de celdas por lado (M).

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
sds-tp1-cim/
├── src/                  # Código fuente principal
│   ├── particles.py      # Generación de partículas
│   ├── cim.py            # Algoritmo Cell Index Method
│   ├── brute_force.py    # Búsqueda de vecinos por fuerza bruta
│   ├── io_utils.py       # Lectura/escritura de archivos de entrada/salida
│   ├── visualize.py      # Visualización de partículas y resultados
│   └── benchmark.py      # Experimentos de tiempo de ejecución
├── tests/                # Tests unitarios (pytest)
├── data/
│   ├── input/             # Archivos de entrada (estático/dinámico)
│   └── output/            # Resultados de benchmarks y ejecuciones
├── figures/              # Figuras y gráficos generados
└── notebooks/            # Notebooks de exploración (opcional)
```

## Uso

_(Sección a completar más adelante con instrucciones de ejecución)_
