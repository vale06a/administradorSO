# Inicializo

memoria = [
    {"id": 0, "base": 0,   "tam": 100, "proceso": "SO"},
    {"id": 1, "base": 100, "tam": 450, "proceso": "LIBRE"},
]

tabla_particiones = [
    {"id_particion": None, "dirParticion": None, "tamaño": None, "id_proceso": None, "frag_ext": None}
]


siguienteIdParticion = 2

colaNuevos = []
colaListos = []
colaListosYSusp = []
colaTerminados = []

totalEnListas = 0  # Ejecución + Listos + Listos/Susp (max 5)
procesoEnEjecucion = None  # dict del proceso corriendo, o None si la CPU está libre


#carga de procesos

def cargarProcesosDesdeEntrada(cantidad):
    for _ in range(cantidad):
        datos = list(map(int, input().split()))
        proceso = {
            "id": datos[0],
            "tam": datos[1],
            "TA": datos[2],
            "TI": datos[3],
        }
        colaNuevos.append(proceso)

#best-fit

def best_FIT(tamProceso):
    mejorIndex = -1
    mejorDiferencia = None
    for i, part in enumerate(memoria):
        if part["proceso"] == "LIBRE" and part["tam"] >= tamProceso:
            diferencia = part["tam"] - tamProceso
            if mejorDiferencia is None or diferencia < mejorDiferencia:
                mejorDiferencia = diferencia
                mejorIndex = i
    return mejorIndex


def asignarParticion(idxParticion, proceso):
    global siguienteIdParticion
    part = memoria[idxParticion]
    diferencia = part["tam"] - proceso["tam"]

    # La partición se recorta al tamaño exacto del proceso
    part["tam"] = proceso["tam"]
    part["proceso"] = proceso["id"]

    # Si quedo espacio, se crea una nueva partición libre a continuación
    if diferencia > 0:
        nuevaBase = part["base"] + part["tam"]
        nuevaParticion = {
            "id": siguienteIdParticion,
            "base": nuevaBase,
            "tam": diferencia,
            "proceso": "LIBRE",
        }
        siguienteIdParticion += 1
        memoria.insert(idxParticion + 1, nuevaParticion)


#revisa si el proceso que acaba de llegar a Listos expropia al que está en CPU (SRTF)

def algoritmo_SRTF(procesoNuevo, tiempoActual):
    global procesoEnEjecucion

    if procesoEnEjecucion is None:
        # no hay nadie corriendo: este proceso pasa directo a ejecución
        procesoNuevo["restante"] = procesoNuevo["TI"]
        procesoNuevo["tUltimaActualizacion"] = tiempoActual
        colaListos.remove(procesoNuevo)
        procesoEnEjecucion = procesoNuevo
        return

    # actualizo cuanto le queda al que está corriendo, hasta este instante
    transcurrido = tiempoActual - procesoEnEjecucion["tUltimaActualizacion"]
    procesoEnEjecucion["restante"] -= transcurrido
    procesoEnEjecucion["tUltimaActualizacion"] = tiempoActual

    if procesoNuevo["TI"] < procesoEnEjecucion["restante"]:
        # expropiacion: el que estaba corriendo vuelve a Listos
        colaListos.append(procesoEnEjecucion)

        procesoNuevo["restante"] = procesoNuevo["TI"]
        procesoNuevo["tUltimaActualizacion"] = tiempoActual
        colaListos.remove(procesoNuevo)
        procesoEnEjecucion = procesoNuevo
    # si no es menor, procesoNuevo se queda esperando en colaListos


#ingresa a Listos o listos y susp

def cargarNuevos(tiempoActual):
    global totalEnListas
    pendientes = colaNuevos[:]
    for proceso in pendientes:
        if totalEnListas >= 5:
            print("Listas llenas, no se admiten más procesos por ahora")
            break

        idx = best_FIT(proceso["tam"])
        #Si es -1 no hay particiones disponibles y va a listos y susp
        if idx == -1:
            colaListosYSusp.append(proceso)
        else:
            asignarParticion(idx, proceso)
            colaListos.append(proceso)
            algoritmo_SRTF(proceso, tiempoActual)

        colaNuevos.remove(proceso)
        totalEnListas += 1


# Finalización de proceso

def finalizarProceso(proceso, tiempoActual):
    global totalEnListas

    proceso["tFin"] = tiempoActual  # necesario para TR y TE después
    colaTerminados.append(proceso)

    # liberar la partición que tenía asignada
    for part in memoria:
        if part["proceso"] == proceso["id"]:
            part["proceso"] = "LIBRE"
            break

    totalEnListas -= 1

#cada vez que se finaliza un proceso se va a a compactar la memoria
def compactar():
    global memoria

    #llevo las particiones libres al final
    bandera = True

    while bandera:
        bandera = False

        for particion in range(1, len(memoria) - 1):

            if memoria[particion]["proceso"] == "LIBRE":
                particionLibre = memoria[particion]
                memoria[particion] = memoria[particion + 1]
                memoria[particion + 1] = particionLibre

                bandera = True

    #vuelvo a calcular las bases
    baseActual = 0

    for particion in range(len(memoria)):

        memoria[particion]["base"] = baseActual

        baseActual += memoria[particion]["tam"]

    #unifico las bases
    tamañoLibre = 0
    indiceLibre = None

    for particion in range(len(memoria)):

        if memoria[particion]["proceso"] == "LIBRE":

            if indiceLibre is None:
                indiceLibre = particion

            tamañoLibre += memoria[particion]["tam"]

    #si existe al menos una partición libre
    if indiceLibre is not None:

        #elimino todas las particiones LIBRE excepto la primera
        memoria = memoria[:indiceLibre] + [
            {
                "id": memoria[indiceLibre]["id"],
                "base": memoria[indiceLibre]["base"],
                "tam": tamañoLibre,
                "proceso": "LIBRE"
            }
        ]
