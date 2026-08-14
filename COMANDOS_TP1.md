# TP1 - Comandos para generar gráficos y figuras

Antes de correr cualquier comando, activar el entorno virtual:

```bash
cd /Users/francoferrari/Desktop/ITBA/Simu
source venv/bin/activate
```

Todos los comandos siguientes son de la forma `python3 -m src.<script>` — cada uno corre un script standalone (parámetros hardcodeados arriba de cada archivo).

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

**Qué hace:** con N fijo, prueba TODOS los M válidos (de 1 hasta M_max) y mide el tiempo promedio de búsqueda (repitiendo `n_repeticiones` veces cada M). Se corre dos veces: una con N intermedio (570) y otra con N máximo (1140, del paso 2), y se superponen en el mismo gráfico.

**Script:** `src/punto3_variacion_M.py` (parámetros hardcodeados arriba del archivo: `L`, `RC`, `R_MIN`/`R_MAX`, `N_REPETICIONES`, `N_INTERMEDIO`, `N_MAXIMO`)

```bash
python3 -m src.punto3_variacion_M
```

**Cómo leer el resultado:** el M donde el tiempo es mínimo es el "M ideal". En las corridas ya hechas dio M≈4-7 (el mínimo de la curva).

---

## 4.1 Gráfico tiempo vs N, con M fijo y L fijo = 20 (densidad libre)

**Qué hace:** fija M en el valor ideal encontrado en el punto 3 (M=5) y L=20, y varía N desde 10 hasta el N_max encontrado en el paso 2. Como L no cambia, a medida que N crece la densidad (N/L²) también crece — por eso se llama "densidad libre".

**Script:** `src/punto4_1_variacion_N.py` (parámetros hardcodeados arriba del archivo: `L`, `M_IDEAL`, `VALORES_N`)

```bash
python3 -m src.punto4_1_variacion_N
```

**Nota:** si `m=None` en vez de un valor fijo, `experimento_variacion_N` recalcula el M óptimo para cada N (que es otra cosa — no es lo que pide 4.1).

---

## 4.2 Gráfico tiempo vs N, con densidad constante (L crece junto con N)

**Qué hace:** elige una densidad intermedia (constante) y, para cada N de la misma lista usada en 4.1, calcula el L que le corresponde para mantener esa densidad. Superpone esta curva con la del punto 4.1 para comparar.

**Script:** `src/punto4_2_densidad_fija.py` (parámetros hardcodeados arriba del archivo: `L`, `M_IDEAL`, `VALORES_N`, `N_INICIAL`, `L_INICIAL`, `FACTORES_ESCALA`)

```bash
python3 -m src.punto4_2_densidad_fija
```

**⚠️ Dos errores ya evitados en el script (por eso las constantes de arriba están fijadas así):**

1. **`m` no puede quedar en `None`.** Si se omite, la función recalcula el M óptimo (`M_max`) en cada punto — deja de ser una comparación "a M fijo", que es lo que pide el enunciado (mismo M ideal encontrado en el punto 3, para ambas curvas).
2. **La densidad de referencia no puede ser muy alta.** Con una densidad alta (ej. N=82, L=20 → densidad=0.205), el L correspondiente al N más chico de la lista (N=10) da un M_max menor a 5, y `buscar_vecinos_cim` tira `MInvalidoError`. La densidad de referencia usada, **N=48, L=20 → densidad=0.12**, deja M_max entre 6 y 64 en los 10 puntos, siempre ≥ 5.

**Resultado ya verificado (con `n_repeticiones=20`, para chequear rápido):** con esta corrección, la curva de densidad fija sale consistentemente **más rápida** que la de densidad libre, y la diferencia crece con N — tiene sentido, porque en densidad libre el sistema termina mucho más empaquetado (densidad final 2.85 vs 0.12 constante), hay muchos más pares que son vecinos reales, y eso cuesta más tiempo de cómputo. Para la entrega final, subir `n_repeticiones` a 100.

---

## Resumen de scripts por punto del enunciado

| Punto del TP | Comando |
|---|---|
| 1 (CIM + figura de partícula y vecinos) | `python3 -m src.main_tp1 --n ... --l ... --rc ...` |
| 4 (N máximo generable) | `python3 -m src.explorar_n_max` |
| 3 (variación de M) | `python3 -m src.punto3_variacion_M` |
| 4.1 (variación de N, densidad libre) | `python3 -m src.punto4_1_variacion_N` |
| 4.2 (variación de N, densidad fija) | `python3 -m src.punto4_2_densidad_fija` |

También existe `src/correr_experimentos_finales.py`, que intenta automatizar 3, 4.1 y 4.2 juntos con parámetros ya definidos (`python3 -m src.correr_experimentos_finales --full`), pero conviene revisar sus constantes internas (L, RC, N_MAX, valores_N) antes de confiar en su salida, ya que fueron fijadas a mano en el archivo.
