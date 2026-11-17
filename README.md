# Simulador de Asignación de Memoria y Planificación de Procesos

Trabajo Práctico Integrador - Sistemas Operativos
Universidad Tecnológica Nacional - Facultad Regional Resistencia
Departamento de Ingeniería en Sistemas de Información

**Comisión 2.2 - Equipo 3**

- Aranda Galissier, Agustina Milagros
- Dali, Tania Yazmin
- Guillen, Alexis de Jesus
- Lopez Yaccuzzi, Lourdes Anali
- Maciel, Julieta Andrea
- Robles, Francisco
- Vargas, Valentina

---

## Descripción

Simulador de un sistema monoprocesador que muestra la **planificación de CPU a corto plazo** y la **gestión de memoria con particiones variables (MVT)**, siguiendo el ciclo de vida completo de un proceso desde que ingresa al sistema hasta que termina.

### Características

- **Memoria:** 100K reservados para el Sistema Operativo y 450K para trabajos de usuario.
- **Asignación de memoria:** particiones variables (MVT) con política **Best-Fit**. La partición se recorta al tamaño exacto del proceso y, al liberarse, se fusionan los huecos libres adyacentes.
- **Planificación de CPU:** **SRTF** (Shortest Remaining Time First), con expropiación.
- **Estados de un proceso:** Nuevo, Listo, Listo y Suspendido, Ejecución y Terminado.
- **Límites:** máximo de 10 procesos por simulación y máximo de 5 procesos simultáneos entre Ejecución, Listos y Listos/Suspendidos. Los procesos que no entran por ese tope esperan en la cola de Nuevos.
- **Procesos suspendidos:** si un proceso llega y no hay un hueco libre donde entre, pasa a Listos/Suspendidos y se reintenta cuando se libera memoria.

### Salida del simulador

En cada evento relevante (ingreso de un proceso, finalización de un proceso, cambios en memoria) se muestra:

- El estado del procesador (proceso en ejecución o CPU ociosa).
- La tabla de particiones de memoria (id de partición, dirección de inicio, tamaño, proceso asignado, fragmentación interna).
- El estado de las colas de Nuevos, Listos y Listos/Suspendidos.
- La tabla de procesos con su estado, tiempo restante, TR y TE.

Al finalizar se presenta el **informe estadístico**: tiempo de retorno (TR) y tiempo de espera (TE) de cada proceso, sus promedios y el rendimiento del sistema (procesos terminados por unidad de tiempo).

---

## Requisitos

- Python 3.8 o superior.
- Debe ejecutarse en una máquina de escritorio (no funciona on-line).
- No requiere librerías ni dependencias externas. El proyecto usa únicamente módulos de la biblioteca estandar de Python.
- Bibliotecas estandar usadas:
  - csv: crearArchivo.py, leerArchivo.py y simuladorGUI.py.
  - random: crearArchivo.py.
  - pathlib (Path): leerArchivo.py y simuladorGUI.py.
  - copy: motorSnapshot.py (deepcopy de la memoria en cada snapshot).
  - tkinter para la interfaz gráfica que viene incluido con Python en Windows y macOS. En Linux puede requerir instalarlo (por ejemplo `sudo apt install python3-tk`): simuladorGUI.py.
  - msvcrt: simulacionPrueba.py, con try/except ImportError. Es un módulo exclusivo de Windows, y si no existe usa input() como alternativa.


---

## Cómo ejecutarlo
Para clonar el proyecto desde la terminal ejecutamos el comando `git clone https://github.com/vale06a/administradorSO.git`, luego nos posicionamos en la pocision del proyecto con `cd administradorSO`

## Ejecutable (.exe)
Además del código fuente, el paquete incluye una versión ejecutable para Windows (SimuladorMVT.exe), para poder correr el simulador sin ejecutar los scripts de Python manualmente.

Para usarlo:
- Descargar y descomprimir el paquete de entrega.
- Hacer doble clic sobre el archivo SimuladorMVT.exe incluido (o ejecutarlo desde una terminal).
- Seguir el menú del simulador.

Notas:
- La aplicación solo funciona en Windows. En otros sistemas operativos hay que ejecutar el código fuente con Python, como se explica en la sección siguiente.
- El archivo .csv de procesos se selecciona desde el propio simulador (opcion 2 - Cargar procesos desde .csv)

### Interfaz de consola

```
python main.py
```

Menú principal:

| Opción | Acción |
|--------|--------|
| 1 | Leer un archivo `.csv` de procesos ya cargado y abrir el submenú de visualización |
| 2 | Crear un archivo con procesos generados aleatoriamente |
| 3 | Mostrar la información del equipo |
| 4 | Iniciar una simulación de prueba con 10 procesos fijos |

Submenú luego de leer un archivo (opción 1):

| Opción | Acción |
|--------|--------|
| 1 | Ver la tabla de particiones |
| 2 | Ver qué procesos están cargados en memoria |
| 3 | Ver la simulación tick a tick |
| 4 | Ejecutar la simulación paso a paso con avance manual |
| 5 | Volver al menú principal |

En la simulación paso a paso, el simulador se detiene en cada evento y espera que el usuario avance:

- En Windows: presionar `a` o la barra espaciadora.
- En otros sistemas: escribir `a` (o espacio) y presionar Enter.

### Interfaz gráfica (Tkinter)

```
python simuladorGUI.py
```

Menú principal:

1. Iniciar simulación precargada (10 procesos fijos).
2. Cargar procesos desde un `.csv`.
3. Cargar procesos manualmente (grilla editable de hasta 10 filas).
4. Información del grupo.

En la ventana de simulación se puede navegar libremente entre los instantes de la simulación con los botones, el slider o las teclas (`←` `→` `Inicio` `Fin`). El último instante navegable es el informe final. La memoria se muestra como una barra con un color por proceso.

---

## Formato del archivo de procesos (.csv)

Archivo de texto plano con extensión `.csv`, separador coma. La primera línea con los nombres de las columnas es opcional. Cada línea restante es **un proceso** con 4 columnas, en este orden:

```
Proceso,TA,TI,Tamaño
```

| Campo | Significado | Restricción |
|-------|-------------|-------------|
| Proceso | Identificador del proceso. Acepta `P1` o directamente `1` | Entero mayor o igual a 0 |
| TA | Tiempo de arribo | Entero mayor o igual a 0 |
| TI | Tiempo de irrupción (ráfaga de CPU) | Entero mayor a 0 |
| Tamaño | Tamaño del proceso en KB | Entero entre 1 y 450 |

Máximo 10 procesos por archivo.

Ejemplo válido:

```
Proceso,TA,TI,Tamaño
P1,3,2,120
P2,10,4,130
P3,10,1,40
```

El simulador valida el archivo antes de empezar. Si hay errores de formato, valores fuera de rango, más de 10 procesos o un proceso de más de 450K (que no podría cargarse ni con la memoria vacía), muestra el error con la línea afectada y no ejecuta la simulación.

---

## Estructura del proyecto

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Punto de entrada de la interfaz de consola y menú principal |
| `administradorCPU.py` | Núcleo del simulador: memoria, colas, Best-Fit, asignación y liberación de particiones, métricas e informe final |
| `leerArchivo.py` | Lectura y validación del `.csv` y submenú de visualización por consola |
| `crearArchivo.py` | Generación de un archivo de procesos aleatorios |
| `simulacionPrueba.py` | Simulación por eventos con avance manual (10 procesos de prueba o los del archivo cargado) |
| `motorSnapshot.py` | Corre la simulación completa y guarda una foto del estado en cada instante, para la interfaz gráfica |
| `simuladorGUI.py` | Interfaz gráfica en Tkinter |
| `getInformacion.py` | Información del equipo |

---

## Decisiones de diseño

- **Fragmentación interna:** como Best-Fit recorta cada partición al tamaño exacto del proceso, la fragmentación interna de las particiones ocupadas es siempre 0. El espacio sobrante queda como una partición libre (fragmentación externa).
- **Salto de tiempo con CPU ociosa:** si no hay procesos listos, el reloj salta directamente al próximo arribo en lugar de avanzar de a una unidad.
- **Cálculo de TR y TE:** se miden desde el instante en que el proceso entra efectivamente a la cola de Listos, no desde el TA del archivo. Un proceso puede demorar su ingreso por el tope de 5 procesos o por falta de memoria.
  - TR = instante de finalización - instante de ingreso a Listos
  - TE = TR - TI
  - Rendimiento = procesos terminados / instante de finalización del último proceso
- **Procesos que no llegan a ejecutarse:** si al final queda algún proceso en Listos/Suspendidos sin haber conseguido memoria, se informa como no ejecutado.

---

## Seguimiento del proyecto

El avance del proyecto se gestiona con Trello, con acceso compartido a los docentes de la cátedra.
