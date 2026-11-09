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
            # TA_listos: instante real en que el proceso entra a Listos.
            # No siempre coincide con TA: puede demorar por el tope de 5
            # procesos simultáneos o por falta de partición libre.
            proceso["taListos"] = tiempoActual
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
        # recién ahora entra efectivamente a Listos (estuvo suspendido un tiempo)
        proceso["taListos"] = tiempoActual
        colaListos.append(proceso)
        colaListosYSusp.remove(proceso)


# mueve un proceso a Terminado, libera su partición y calcula sus métricas

def finalizarProceso(proceso, tiempoActual):
    global totalEnListas

    proceso["tFin"] = tiempoActual  # necesario para TR y TE

    # TR y TE se calculan desde taListos (arribo EFECTIVO a la cola de Listos),
    # no desde TA del archivo: un proceso puede quedar esperando antes de
    # conseguir memoria (tope de 5 simultáneos o falta de partición libre),
    # y ese tiempo de espera previo no es parte de su tiempo en el sistema.
    proceso["TR"] = proceso["tFin"] - proceso["taListos"]
    proceso["TE"] = proceso["TR"] - proceso["TI"]

    colaTerminados.append(proceso)

    # Liberar la partición del proceso y fusionar huecos libres adyacentes
    # (consolidación de memoria en MVT). Si la partición siguiente o la
    # anterior ya están LIBRE, se unen en un único hueco más grande.
    for i, part in enumerate(memoria):
        if part["proceso"] == proceso["id"]:
            part["proceso"] = "LIBRE"

            # 1) fusión con la partición de la derecha si está libre
            if i + 1 < len(memoria) and memoria[i + 1]["proceso"] == "LIBRE":
                part["tam"] += memoria[i + 1]["tam"]
                memoria.pop(i + 1)

            # 2) fusión con la partición de la izquierda si está libre
            # (la del SO nunca entra acá porque su ocupante es "SO", no "LIBRE")
            if i > 0 and memoria[i - 1]["proceso"] == "LIBRE":
                memoria[i - 1]["tam"] += part["tam"]
                memoria.pop(i)

            break

    totalEnListas -= 1


# informe final: TR y TE por proceso, promedios y rendimiento del sistema

def generarInformeFinal():
    if not colaTerminados:
        print("No hay procesos terminados para informar.")
        return

    print("\n=== INFORME FINAL ===")
    print(f"{'ID':^5} | {'TR':^6} | {'TE':^6}")
    print("-" * 24)

    sumaTR = 0
    sumaTE = 0
    for proceso in colaTerminados:
        print(f"{proceso['id']:^5} | {proceso['TR']:^6} | {proceso['TE']:^6}")
        sumaTR += proceso["TR"]
        sumaTE += proceso["TE"]

    n = len(colaTerminados)
    promedioTR = sumaTR / n
    promedioTE = sumaTE / n
    tiempoTotal = max(p["tFin"] for p in colaTerminados)
    rendimiento = n / tiempoTotal if tiempoTotal > 0 else 0

    print("-" * 24)
    print(f"Promedio TR: {promedioTR:.2f}")
    print(f"Promedio TE: {promedioTE:.2f}")
    print(f"Rendimiento del sistema: {rendimiento:.3f} procesos por unidad de tiempo")


# vuelve el simulador a su estado inicial (útil para correr la simulación
# más de una vez en la misma ejecución del programa, sin arrastrar datos
# de una corrida anterior)

def reiniciarSimulador():
    global memoria, siguienteIdParticion, colaNuevos, colaListos
    global colaListosYSusp, colaTerminados, totalEnListas, procesoEnEjecucion

    memoria = [
        {"id": 0, "base": 0,   "tam": 100, "proceso": "SO"},
        {"id": 1, "base": 100, "tam": 450, "proceso": "LIBRE"},
    ]
    siguienteIdParticion = 2
    colaNuevos = []
    colaListos = []
    colaListosYSusp = []
    colaTerminados = []
    totalEnListas = 0
    procesoEnEjecucion = None
