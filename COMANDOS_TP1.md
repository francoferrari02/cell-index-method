# TP1 - Comandos para generar gráficos y figuras

Antes de correr cualquier comando, activar el entorno virtual:

```bash
cd /Users/francoferrari/Desktop/ITBA/Simu
source venv/bin/activate
```

Todos los comandos siguientes se pegan directo en la terminal (usan `python3 << 'EOF' ... EOF`).

---

## 1. Gráfico de partículas + vecinos de una partícula (Punto 1)

**Qué hace:** genera N partículas, busca los vecinos de una partícula (con CIM), imprime el tiempo de ejecución y guarda una figura con la partícula elegida en rojo y sus vecinas en naranja.

**Script:** `src/main_tp1.py`

```bash
python3 -m src.main_tp1 --n 100 --l 20 --rc 1.0
```

**Parámetros:**

| Parámetro | Qué es | Default |
|---|---|---|
| `--n` | Cantidad de partículas (requerido) | - |
| `--l` | Lado del área L | 20.0 |
| `--rc` | Radio de interacción | 1.0 |
| `--m` | Celdas por lado (M). Si no se pasa, usa el M máximo válido | auto |
| `--particula-id` | Partícula a resaltar. Si no se pasa, se sortea | aleatorio |
| `--periodic` | Activa condiciones de borde periódicas | False |
| `--seed` | Semilla para reproducibilidad | None |

**Ejemplo con bordes periódicos y M fijo:**

```bash
python3 -m src.main_tp1 --n 100 --l 20 --rc 1.0 --m 10 --periodic --seed 42
```

**Salida:** figura en `figures/main_tp1_N{n}_L{l}_rc{rc}.png` + tiempo impreso en consola.

---

## 2. Calcular N máximo generable (para saber hasta dónde llegar en el punto 4)

**Qué hace:** busca (por búsqueda exponencial + binaria) el N más grande que se puede generar sin superposición en L=20, antes de que el rejection sampling tarde demasiado (timeout de 10s por intento).

**Script:** `src/explorar_n_max.py`

```bash
python3 -m src.explorar_n_max
```

**Parámetros:** están hardcodeados dentro del script (`L=20.0`, `R_MIN, R_MAX = 0.23, 0.26`, `TIMEOUT_S=10`). Si querés otro L, hay que editar el archivo.

**Salida esperada (ejemplo real ya corrido):**
```
N máximo generable: 1140
Densidad numérica (N / L^2): 2.8500
Fracción de área ocupada: 0.5308
```

Este N_max se usa como último valor en las listas de N del punto 4.

---

## 3. Gráfico tiempo vs M, para encontrar el M ideal (Punto 3)

**Qué hace:** con N fijo, prueba TODOS los M válidos (de 1 hasta M_max) y mide el tiempo promedio de búsqueda (repitiendo `n_repeticiones` veces cada M). Se corre dos veces: una con N intermedio y otra con N máximo, y se superponen en el mismo gráfico.

**Funciones:** `experimento_variacion_M` y `graficar_variacion_M` de `src/benchmark.py`

```bash
python3 << 'EOF'
from src.benchmark import experimento_variacion_M, graficar_variacion_M
from src.visualize import guardar_figura

# N intermedio = N_max / 2 = 570
df_n570 = experimento_variacion_M(
    n=570,
    l=20.0,
    rc=1.0,
    r_min=0.23,
    r_max=0.26,
    n_repeticiones=100,
    seed=42,
)

# N máximo, encontrado en el paso 2 = 1140
df_n1140 = experimento_variacion_M(
    n=1140,
    l=20.0,
    rc=1.0,
    r_min=0.23,
    r_max=0.26,
    n_repeticiones=100,
    seed=42,
    max_intentos=5_000_000,  # N=1140 necesita más intentos que el default (100_000)
)

ax = graficar_variacion_M(
    [df_n570, df_n1140],
    labels=["N=570", "N=1140"],
    titulo="Punto 3: tiempo de búsqueda de vecinos vs M (CIM)",
)
guardar_figura(ax.figure, "punto3_variacion_M")
print(df_n570)
print(df_n1140)
EOF
```

**Parámetros:**

| Parámetro | Qué es |
|---|---|
| `n` | Cantidad de partículas, fija durante todo el experimento |
| `l`, `rc`, `r_min`, `r_max` | Valores del enunciado (L=20, rc=1, r∈[0.23,0.26]) |
| `n_repeticiones` | Cuántas veces se repite la búsqueda para cada M (para promediar y sacar desvío estándar) |
| `max_intentos` | Límite de intentos del rejection sampling al generar las partículas. Con N alto (cerca de 1140) hay que subirlo de 100_000 a 5_000_000, si no puede fallar la generación |

**Cómo leer el resultado:** el M donde el tiempo es mínimo es el "M ideal". En las corridas ya hechas dio M≈4-7 (el mínimo de la curva).

---

## 4.1 Gráfico tiempo vs N, con M fijo y L fijo = 20 (densidad libre)

**Qué hace:** fija M en el valor ideal encontrado en el punto 3 (ej. M=5) y L=20, y varía N desde 10 hasta el N_max encontrado en el paso 2. Como L no cambia, a medida que N crece la densidad (N/L²) también crece — por eso se llama "densidad libre".

**Función:** `experimento_variacion_N` de `src/benchmark.py`

```bash
python3 << 'EOF'
from src.benchmark import experimento_variacion_N, graficar_variacion_N
from src.visualize import guardar_figura

df_libre = experimento_variacion_N(
    l=20.0,
    rc=1.0,
    r_min=0.23,
    r_max=0.26,
    valores_n=[10, 17, 29, 48, 82, 139, 235, 398, 674, 1140],  # 10 valores, log-espaciados, hasta N_max
    m=5,  # M ideal encontrado en el punto 3
    n_repeticiones=100,
    max_intentos=5_000_000,  # necesario para poder generar N=1140
    seed=42,
)

ax = graficar_variacion_N(df_libre, titulo="Punto 4.1: Tiempo vs N (L=20, M=5 fijo)")
guardar_figura(ax.figure, "punto4p1_variacion_N")
print(df_libre)
EOF
```

**Parámetros:**

| Parámetro | Qué es |
|---|---|
| `l` | L fijo en 20 (no cambia) |
| `valores_n` | Lista de al menos 10 valores de N, desde 10 hasta el N_max del paso 2 |
| `m` | M ideal fijo, encontrado en el punto 3 (no `None`, porque si no recalcula M_max en cada N) |
| `n_repeticiones`, `max_intentos` | Mismo criterio que en el punto 3 |

**Nota:** si `m=None` en vez de un valor fijo, la función recalcula el M óptimo para cada N (que es otra cosa — no es lo que pide 4.1).

---

## 4.2 Gráfico tiempo vs N, con densidad constante (L crece junto con N)

**Qué hace:** elige una densidad intermedia (constante) y, para cada N de la misma lista usada en 4.1, calcula el L que le corresponde para mantener esa densidad. Superpone esta curva con la del punto 4.1 para comparar.

**Función:** `experimento_variacion_N_densidad_fija` de `src/benchmark.py`

**⚠️ Dos errores a evitar (ya nos pasaron y el gráfico salía mal):**

1. **Olvidar pasar `m=5` explícito.** Si se omite, `m` queda en `None` y la función recalcula el M óptimo (`M_max`) en cada punto — es decir, deja de ser una comparación "a M fijo", que es lo que pide el enunciado (mismo M ideal encontrado en el punto 3, para ambas curvas). Sin esto, la comparación no es justa y el resultado no tiene interpretación clara.
2. **Elegir una densidad de referencia demasiado alta.** Si la densidad elegida es alta (por ejemplo la de N=82, L=20 → densidad=0.205), el L correspondiente al N más chico de la lista (N=10) da un M_max menor a 5, y `buscar_vecinos_cim` tira `MInvalidoError` al querer usar M=5. Hay que elegir una densidad tal que M=5 sea válido (M ≤ M_max) en **todos** los puntos, incluido el N más chico.

Con `L=20, rc=1.0, r_max=0.26` (⇒ `rc_efectivo=1.52`), la densidad de referencia **N=48, L=20 → densidad=0.12** cumple esto (verificado: `M_max` da entre 6 y 64 en los 10 puntos, siempre ≥ 5).

```bash
python3 << 'EOF'
from src.benchmark import experimento_variacion_N, experimento_variacion_N_densidad_fija, graficar_variacion_N
from src.visualize import guardar_figura

VALORES_N = [10, 17, 29, 48, 82, 139, 235, 398, 674, 1140]
M_IDEAL = 5  # el M ideal encontrado en el punto 3 - debe ser el MISMO en 4.1 y 4.2

# 4.1 (densidad libre, L=20 fijo)
df_libre = experimento_variacion_N(
    l=20.0,
    rc=1.0,
    r_min=0.23,
    r_max=0.26,
    valores_n=VALORES_N,
    m=M_IDEAL,
    n_repeticiones=100,
    max_intentos=5_000_000,
    seed=42,
)

# 4.2 (densidad fija = 48/20^2 = 0.12)
# factor = sqrt(N_objetivo / n_inicial), calculados para que los N generados
# coincidan exactamente con los mismos 10 valores usados en 4.1
FACTORES = [0.4564, 0.5951, 0.7773, 1.0, 1.3070, 1.7017, 2.2127, 2.8795, 3.7472, 4.8734]
df_fija = experimento_variacion_N_densidad_fija(
    l_inicial=20.0,
    n_inicial=48,       # densidad de referencia elegida (0.12), válida en todo el rango
    rc=1.0,
    r_min=0.23,
    r_max=0.26,
    factores_escala=FACTORES,
    m=M_IDEAL,          # <- clave: mismo M que en 4.1, si no la comparación no vale
    n_repeticiones=100,
    max_intentos=5_000_000,
    seed=42,
)

ax = graficar_variacion_N(
    df_densidad_fija=df_fija,
    df_densidad_libre=df_libre,
    titulo="Punto 4: Tiempo vs N (Densidad fija vs Densidad libre)",
)
guardar_figura(ax.figure, "punto4_completo")
print(df_fija[["N", "L", "M_usado", "tiempo_promedio", "densidad"]])
print(df_libre[["N", "M_usado", "tiempo_promedio", "densidad"]])
EOF
```

**Parámetros:**

| Parámetro | Qué es |
|---|---|
| `n_inicial`, `l_inicial` | El punto de referencia cuya densidad (`n_inicial / l_inicial²`) se mantiene constante. Elegir uno cuya densidad sea baja, para que M_ideal siga siendo válido incluso en el N más chico de la lista |
| `factores_escala` | Multiplican a `n_inicial` (al cuadrado) y a `l_inicial` para generar cada punto: `N = n_inicial * factor²`, `L = l_inicial * factor`. Calculados con `factor = sqrt(N_objetivo / n_inicial)` para que coincidan exactamente con los N de 4.1 |
| `m` | **Fijarlo explícitamente en el M ideal del punto 3** (no dejarlo en `None`), para que 4.1 y 4.2 sean comparables |

**Resultado ya verificado (con `n_repeticiones=20`, para chequear rápido):** con esta corrección, la curva de densidad fija sale consistentemente **más rápida** que la de densidad libre, y la diferencia crece con N — tiene sentido, porque en densidad libre el sistema termina mucho más empaquetado (densidad final 2.85 vs 0.12 constante), hay muchos más pares que son vecinos reales, y eso cuesta más tiempo de cómputo. Para la entrega final, subir `n_repeticiones` a 100.

---

## Resumen de scripts por punto del enunciado

| Punto del TP | Script / función | Archivo |
|---|---|---|
| 1 (CIM + figura de partícula y vecinos) | `main` (CLI) | `src/main_tp1.py` |
| 3 (variación de M) | `experimento_variacion_M` + `graficar_variacion_M` | `src/benchmark.py` |
| 4 (N máximo generable) | script standalone | `src/explorar_n_max.py` |
| 4.1 (variación de N, densidad libre) | `experimento_variacion_N` + `graficar_variacion_N` | `src/benchmark.py` |
| 4.2 (variación de N, densidad fija) | `experimento_variacion_N_densidad_fija` + `graficar_variacion_N` | `src/benchmark.py` |

También existe `src/correr_experimentos_finales.py`, que intenta automatizar 3, 4.1 y 4.2 juntos con parámetros ya definidos (`python3 -m src.correr_experimentos_finales --full`), pero conviene revisar sus constantes internas (L, RC, N_MAX, valores_N) antes de confiar en su salida, ya que fueron fijadas a mano en el archivo.
