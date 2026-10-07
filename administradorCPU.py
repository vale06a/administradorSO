# Inicializo

memoria = [
    {"id": 0, "base": 0,   "tam": 100, "proceso": "SO"},
    {"id": 1, "base": 100, "tam": 450, "proceso": "LIBRE"},
]

siguienteIdParticion = 2

colaNuevos = []
colaListos = []
colaListosYSusp = []
colaTerminados = []

totalEnListas = 0  # Ejecución + Listos + Listos/Susp (max 5)
procesoEnEjecucion = None  # dict del proceso corriendo, o None si la CPU está libre


# best-fit

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

    # Si quedó espacio, se crea una nueva partición libre a continuación
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


# ingresa a Listos o Listos y Susp, respetando TA y el tope de 5

def cargarNuevos(tiempoActual):
    global totalEnListas
    candidatos = [p for p in colaNuevos if p["TA"] <= tiempoActual]

    for proceso in candidatos:
        if totalEnListas >= 5:
            break

        idx = best_FIT(proceso["tam"])
        if idx == -1:
            colaListosYSusp.append(proceso)
        else:
            asignarParticion(idx, proceso)
            proceso["restante"] = proceso["TI"]
            colaListos.append(proceso)

        colaNuevos.remove(proceso)
        totalEnListas += 1


# revisa colaListosYSusp cuando se libera una partición, por si alguno ahora entra

def admitirSuspendidos(tiempoActual):
    pendientes = colaListosYSusp[:]
    for proceso in pendientes:
        idx = best_FIT(proceso["tam"])
        if idx == -1:
            continue  # sigue sin entrar, se queda en colaListosYSusp

        asignarParticion(idx, proceso)
        proceso["restante"] = proceso["TI"]
        colaListos.append(proceso)
        colaListosYSusp.remove(proceso)


# mueve un proceso a Terminado y libera su partición

def finalizarProceso(proceso, tiempoActual):
    global totalEnListas

    proceso["tFin"] = tiempoActual  # necesario para TR y TE
    colaTerminados.append(proceso)

    for part in memoria:
        if part["proceso"] == proceso["id"]:
            part["proceso"] = "LIBRE"
            break

    totalEnListas -= 1
