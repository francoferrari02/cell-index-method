# Bitácora de desarrollo — TP1 Cell Index Method

Este documento resume el proceso de implementación del TP1, los problemas
concretos con los que nos encontramos, cómo se resolvieron, y qué resultados
fuimos obteniendo en cada etapa. Sirve como registro técnico para el informe
y como explicación de las decisiones de diseño que no son obvias solo
leyendo el código final.

## 1. Andamiaje inicial

Se armó la estructura del repo (`src/`, `tests/`, `data/`, `figures/`) con
stubs documentados (`particles.py`, `cim.py`, `brute_force.py`, `io_utils.py`,
`visualize.py`, `benchmark.py`) antes de implementar nada. Sin conflictos en
esta etapa; fue la base sobre la que se construyó todo lo demás.

## 2. `particles.py` — generación de partículas

Se implementó `generar_particulas()` con **rejection sampling**: se generan
posiciones candidatas al azar y se descartan si se superponen con alguna
partícula ya colocada (comparación vectorizada con numpy contra todas las
partículas colocadas hasta el momento, no partícula por partícula).

No hubo conflictos de diseño relevantes acá, pero esta implementación
resultó clave más adelante para entender el **límite práctico de densidad**
del sistema (ver sección 6).

## 3. `cim.py` — Cell Index Method

### 3.1. Elección de `M_max` con partículas de radio no nulo

El criterio clásico de CIM (`L/M > rc`) asume partículas puntuales. Acá el
criterio de vecindad es sobre distancia **borde-borde**, no centro-centro,
así que se usó un radio efectivo `rc_efectivo = rc + 2*r_max` (peor caso:
dos partículas del radio máximo) para garantizar que dos partículas vecinas
siempre caigan en celdas iguales o adyacentes. De ahí:
`M_max = max(1, floor(L / rc_efectivo))` (el `max(1, ...)` para que M=1
—equivalente a fuerza bruta— sea siempre válido).

### 3.2. Bug: wraparound periódico con M chico

**Problema encontrado durante el desarrollo** (antes de correr los tests,
al razonar sobre el semi-stencil de celdas vecinas): con condiciones
periódicas y M=1 o M=2, el módulo de índices de celda rompía el supuesto de
"cada par de celdas se visita una sola vez":

- **M=1**: la única celda vecina calculada mod M terminaba siendo la
  celda propia → se recontaban pares ya cubiertos por el loop intra-celda.
- **M=2**: los offsets diagonales `(1,-1)` y `(1,1)` colisionaban en la
  misma celda destino (mod 2) → un mismo par de celdas se procesaba dos
  veces, duplicando vecinos.

**Resolución**: se agregó un `set` de pares de celdas ya procesados
(`frozenset` de las dos celdas) y se salta si la celda vecina calculada
coincide con la celda actual. Cubierto por el test parametrizado que
incluye M=1, M=2 y M=M_max con `periodic=True`.

### 3.3. Bug: extensión de figura mal detectada

Al integrar `main_tp1.py` con `visualize.guardar_figura()`, nombres de
archivo con puntos por los parámetros (ej. `"...rc1.0"`) hacían que
`os.path.splitext` interpretara `.0` como extensión, y matplotlib fallaba
con `ValueError: Format '0' is not supported`.

**Resolución**: se cambió `guardar_figura` para validar contra una lista
de extensiones de imagen reconocidas en vez de confiar en "lo que hay
después del último punto".

## 4. Vectorización de `cim.py` — el cuello de botella más importante

### 4.1. Diagnóstico

Al preparar la corrida final de los experimentos del punto 3/4 con
`n_repeticiones=1000`, el script tardaba **más de 10 minutos sin terminar**
con N=1140. Se investigó y se confirmó que tanto `buscar_vecinos_fuerza_bruta`
como el loop interno de `buscar_vecinos_cim` comparaban pares de partículas
**uno por uno en Python puro** (doble `for` llamando a una función auxiliar
por cada par), sin ninguna vectorización con numpy.

Benchmark aislado (N=1140, L=20, rc=1, una sola llamada, sin repeticiones):

| M | Tiempo (antes) |
|---|---|
| 1 (fuerza bruta, ~649.230 pares) | **554.6 ms** |
| 13 (M óptimo teórico) | 29.0 ms |

Proyectado a 300 repeticiones, solo el punto N=1140 del experimento de
variación de M sumaba **~11.3 minutos** — explicaba exactamente por qué el
script no terminaba.

### 4.2. Resolución

Se reescribió el cálculo de distancias con **broadcasting de numpy**:
matriz completa de diferencias (`pos_a[:, None, :] - pos_b[None, :, :]`),
norma vectorizada (`np.linalg.norm(..., axis=-1)`), resta de la matriz de
suma de radios, máscara booleana `< rc`, y extracción de pares con
`np.nonzero` (con `np.triu` para no duplicar ni auto-comparar cuando el
conjunto se compara contra sí mismo). Se mantuvo intacta toda la lógica de
celdas/offsets/deduplicación periódica — solo cambió *cómo* se comparan las
partículas dentro de cada par de celdas o en fuerza bruta.

Resultado (mismo caso, N=1140):

| M | Antes | Después | Speedup |
|---|---|---|---|
| 1 | 554.6 ms | ~30 ms | **~18x** |
| 13 | 29.0 ms | ~12 ms | **~2.4x** |

Se agregó un test de regresión de performance
(`test_buscar_vecinos_cim_m1_es_rapido_para_n_grande`) que falla si en el
futuro se reintroduce un loop puro sin vectorizar.

### 4.3. Interfaz faltante descubierta en el camino

Al intentar generar N=1140 dentro de los experimentos de `benchmark.py`,
las funciones `experimento_variacion_M/N/N_densidad_fija` no exponían el
parámetro `max_intentos` de `generar_particulas()`; el default (100.000
intentos) no alcanza cerca del límite de densidad (ver sección 6). Se
agregó `max_intentos` como parámetro opcional (default 100.000, no rompe
nada existente) a las tres funciones.

## 5. Estimación de tiempos: expectativa vs. realidad

Antes de la vectorización se hizo una estimación de tiempos basada
**solo en el costo de generación de partículas** (~17.89s para los casos
más pesados) más una extrapolación lineal aproximada del costo de
búsqueda, dando una proyección de **~2.2 minutos** para la corrida
completa. La corrida real (antes de vectorizar) **no terminó en 10
minutos**.

**Causa del error de estimación**: la extrapolación lineal usó datos de
calibración de N=20 (~70-190 microsegundos por llamada), muy chico para
representar el comportamiento a N=1140, donde el costo por-llamada del
loop puro de Python escala peor que lo asumido (overhead de interprete
por par comparado, no solo el trabajo aritmético). Esto es exactamente lo
que la vectorización eliminó.

**Lección**: para estimar tiempos de un algoritmo con loops en Python
puro, calibrar con el N objetivo real (o uno cercano), no extrapolar desde
un N mucho más chico — el overhead de intérprete no escala igual que el
trabajo aritmético subyacente.

## 6. `explorar_n_max.py` — límite práctico de densidad (jamming)

Se buscó, por búsqueda exponencial + binaria con timeout real de pared
(`signal.alarm`), el N máximo generable en tiempo razonable para L=20,
r∈[0.23, 0.26]:

- **N_max ≈ 1140**, generado en ~8.83s, con hasta ~2.000.000 de intentos
  de rejection sampling necesarios cerca de ese límite (evidencia directa
  de que el rechazo se dispara, no una falla de implementación).

**Conflicto detectado y corregido en el análisis**: la primera comparación
propuesta fue densidad numérica (`N/L²`, unidades 1/área) contra la
densidad de empaquetamiento hexagonal compacto (`≈0.9069`, una **fracción
de área**, adimensional) — comparación dimensionalmente inválida. Se
corrigió calculando la fracción de área real ocupada
(`Σ π rᵢ² / L²`) con los radios efectivamente generados:

| Métrica | Valor |
|---|---|
| Densidad numérica (N/L²) | 2.85 partículas/u² |
| **Fracción de área ocupada** | **0.5308** |
| Límite hexagonal compacto (círculos iguales) | 0.9069 |
| % del límite teórico alcanzado | **58.5%** |

**Análisis**: el resultado (~0.53 de fracción de área) es consistente con
el fenómeno conocido de **jamming en Random Sequential Adsorption (RSA)**:
para discos colocados al azar sin reacomodo posterior, la densidad de
saturación práctica ronda 0.54–0.55, muy por debajo del empaquetamiento
ordenado (hexagonal) de 0.9069, que requiere una disposición regular
imposible de alcanzar por colocación puramente aleatoria. No es un
artefacto del código: es el comportamiento físico/estadístico esperado del
algoritmo de rejection sampling.

## 7. Corrida final de los experimentos (puntos 3 y 4)

Con `cim.py` ya vectorizado, se relanzó `correr_experimentos_finales.py`
con la calidad estadística original (`n_repeticiones=1000` en los tres
experimentos), agregando logging de progreso en vivo (`benchmark.py`
ahora imprime una línea por cada M/N/factor terminado, con `flush=True`)
para poder seguir la corrida sin esperar a ciegas — necesario después de
la experiencia de la sección 5.

**Resultado: 316.74s (~5.3 min) de punta a punta**, con L=20, rc=1.0,
r∈[0.23, 0.26], seed=42:

| Experimento | Detalle | Tiempo |
|---|---|---|
| Punto 3 | N=570 (13 valores de M) | 68.44s |
| Punto 3 | N=1140 (13 valores de M) | 158.43s |
| Punto 4.1 | 10 valores de N, densidad libre (L=20 fijo) | 45.85s |
| Punto 4.2 | 10 valores de N, densidad fija (ref. 0.205) | 43.48s |

### Hallazgo no trivial: el M óptimo no es M_max

La curva tiempo-vs-M (punto 3) tiene **forma de U**, no es monótona
decreciente: cae fuerte de M=1 a M≈6-7 (mínimo), y **vuelve a subir**
hacia M=13 (el M_max teórico permitido por el criterio de vecindad).

**Análisis**: a mayor M hay más celdas (M² en total), y aunque cada
comparación de partículas es más barata (menos partículas por celda), el
overhead de Python por celda —iterar el diccionario de celdas, evaluar los
4 offsets del semi-stencil, hacer lookups y construir `frozenset` para la
deduplicación periódica— crece con la cantidad de celdas. Pasado cierto
punto, ese overhead de bookkeeping domina sobre el ahorro de trabajo
aritmético. Es un dato relevante para el informe: el M "matemáticamente
permitido" más alto no es necesariamente el M más rápido en la práctica;
hay un punto dulce intermedio.

## 8. `io_utils.py` — formato de archivos (punto 5)

Implementación de lectura/escritura de archivos estático, dinámico y de
vecinos según el formato del enunciado. No presentó conflictos de diseño
mayores — el único cuidado particular fue el parser del archivo dinámico,
que debe distinguir una línea de timestamp (un solo valor) de una línea de
partícula (4 valores) para soportar múltiples bloques de tiempo pensando
en TPs futuros con dinámica real.

Se generaron los archivos de ejemplo reales (N=10, L=5, rc=1) en
`data/input/ejemplo_estatico.txt`, `data/input/ejemplo_dinamico.txt` y
`data/output/ejemplo_vecinos.txt`, como caso de referencia legible para la
demo y el informe.

## 9. Estado final

- **33 tests**, todos pasando (`particles`, `cim`, `benchmark`,
  `main_tp1`, `io_utils`).
- Suite completa corre en ~10s (incluye la generación real de N=1140 para
  el test de regresión de performance).
- Figuras finales: `figures/figura_punto3_variacion_M.png`,
  `figures/figura_punto4_completa.png`.

## Resumen de conflictos y resoluciones

| # | Conflicto | Causa raíz | Resolución |
|---|---|---|---|
| 1 | Vecinos duplicados/auto-comparados con M=1/M=2 periódico | Wraparound de índices de celda colisiona con el semi-stencil "hacia adelante" | Set de pares de celdas ya procesados |
| 2 | `ValueError: Format '0' is not supported` al guardar figuras | `os.path.splitext` interpreta cualquier `.N` final como extensión | Whitelist de extensiones de imagen válidas |
| 3 | Corrida no termina en 10 min | Loops de Python puro (no vectorizados) en `cim.py`, ~649k pares en Python interpretado | Vectorización con broadcasting de numpy (~18x speedup) |
| 4 | `generar_particulas` falla para N=1140 dentro de los experimentos | `max_intentos` no expuesto en `benchmark.py` | Parámetro agregado, default no invasivo |
| 5 | Estimación de tiempo (~2.2 min) muy por debajo de la realidad | Calibración extrapolada desde N muy chico (N=20) | Medición directa en el N objetivo antes de proyectar |
| 6 | Comparación de densidad sin sentido dimensional | N/L² (1/área) comparado contra fracción de área (adimensional) | Cálculo de fracción de área real (Σπrᵢ²/L²) |

## Conclusión

El desarrollo siguió un patrón repetido y saludable: implementar con
tests → diagnosticar con datos concretos (no suposiciones) cuando algo no
cuadraba → corregir con el cambio más quirúrgico posible sin tocar
interfaces públicas innecesariamente. Los dos hallazgos más valiosos para
el informe del TP son el **límite de jamming (~0.53 de fracción de área,
consistente con RSA)** y el **mínimo no trivial de tiempo en función de M**
(el M óptimo real es menor que el M_max teórico), ambos resultado directo
de haber corrido los experimentos a escala real y no solo confiado en el
análisis asintótico de la complejidad.
