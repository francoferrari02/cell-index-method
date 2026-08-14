Simulación de Sistemas
Trabajo Práctico Nro. 1: Búsqueda Eficiente de Partículas Vecinas
Sea un área cuadrada de lado L que contiene N partículas con radios ri distintos de cero y con un
radio de interacción rc. Si no se especifica lo contrario, considerar: L=20, rc=1 y ri = U[0.23, 0.26].
1- Implementar el algoritmo "Cell Index Method" que tome como input: las posiciones y radios de
N partículas y los parámetros N, L, M y rc (ver punto 5). Las N partículas deben ser generadas en
forma aleatoria pero no superpuestas dentro del área de lado L.
Y como output:
- Una lista tal que para cada partícula indique cuales son las vecinas que distan menos de rc.
- El tiempo de ejecución.
- Además se debe generar una figura que muestre las posiciones de todas las partículas, y que
identifique una de ellas (pasada como input) de un color y sus vecinos correspondientes de otro
color.
Las distancias entre partículas deben medirse borde a borde, es decir, considerando el radio ri
además del centro de masa de las mismas. ¿Cómo se modifica el criterio L/M > rc cuando la
partícula no es puntual, es decir tiene un radio (ri > 0) ? (considerar que sucede cuando el borde de
una partícula está en el una celda vecina pero no su centro).
Como parámetro adicional considerar dos versiones del algoritmo:
a- Sin condiciones periódicas de contorno (considerando distancia a los bordes del área: paredes).
b- Con condiciones periódicas de contorno.
2- Demostración en vivo.
Se realizarán en clase, a medida que los grupos vayan finalizando el T.P. dentro de las fechas
estipuladas (ver 7).
Las demostraciones en vivo serán dinámicas, y deberán generarse partículas para distintos valores
de los parámetros (N, L, M y rc) para mostrar los outputs definidos en el punto 1.
3- Variación de M.
Considerando L=20, rc=1 y ri = U[0.23, 0.26], tomar dos valores de N, uno intermedio y el mas alto
posible. Para cada uno variar el valor de M desde 1 (fuerza bruta) hasta el máximo permitido por el
método (si M supera este máximo debe dar un error) y graficar el tiempo de computo en función de
M. Para ello, realizar varias veces (10, 100, o 1000) la búsqueda de vecinos y registrar los tiempos
para luego graficar el promedio y desvío estándar (barra de error) en función del input estudiado. En
caso que uno o los dos ejes varíen en distintos órdenes de magnitud, hacer las figuras con los ejes
que correspondan en escala logarítmica.
4- Variación de N.
Para el valor óptimo de M encontrado en 3, estudiar variaciones del tiempo de computo en función
de N (por lo menos 10 valores desde N =10 hasta el máximo que se puede generar en la geometría).
4.1 Considerar L=20, rc=1 y ri = U[0.23, 0.26] y graficar el tiempo de ejecución promedio en
función de N con el mismo método que se indicó en el punto 3.
4.2 Elegir una densidad intermedia del punto anterior (4.1). Luego, incrementar L, a la vez
que se incrementa N, de tal forma de mantener constante dicha densidad. También graficar el
tiempo de ejecución promedio en función de N. Superponer esta curva a la figura del punto 4.1 para
comparar (usar distintos colores o símbolos y leyendas para indicar "densidad fija" o "densidad
libre".
5. Formato tentativo de los archivos:
- Input:
En general para una simulación, el sistema se puede describir con 2 archivos de texto: el estático y
el dinámico (consideraremos a estos archivos como el Input para el CIM).
Estático:
N (Heading con el Nro. total de Partículas)
L (Longitud del lado del área de simulación)
r1 pr1 (radio y propiedad de la partícula 1)
r2 pr2 (radio y propiedad de la partícula 2)
....
rN prN (radio y propiedad de la partícula N)
Dinámico:
t0 (tiempo)
x1 y1 vx1 vy1 (partícula 1)
x2 y2 vx2 vy2 (partícula 2)
....
xN yN vxN vyN (partícula N)
t1 (tiempo)
x1 y1 vx1 vy1 (partícula 1)
x2 y2 vx2 vy2 (partícula 2)
....
xN yN vxN vyN (partícula N)
Otra forma de imprimir archivos dinámicos, puede ser generando un archivo por cada tiempo, el
cual deberá ser nombrado con las cifras numéricas del tiempo correspondiente (por ejemplo: 1.txt;
5.txt; 10.txt; 15.txt; ...., si se guardan datos cada 5 unidades de tiempo).
A los fines del presente trabajo se considera un único tiempo (t0) ya que el método de detección de
vecinos se aplica en un determinado estado del sistema en un dado instante.
- Output:
[id de la partícula "i" id's de las partículas cuya distancia borde-borde es menos de rc].
...
6- Para visualizar las partículas coloreadas se recomienda usar alguna herramienta existente que
puede ser independiente del código implementado, como por ejemplo: Ovito (www.ovito.org),
Python, Matlab, Octave, etc.
7- Fecha de Entrega:
Las fechas para la demostración en vivo descripta en el punto 4 se realizará durante las clases de los
días 7 y 10 de Agosto 2026.