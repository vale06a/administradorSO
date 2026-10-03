# Inicializo
#Cuado este tabla, permitir correr segundo a segundo o seleccionar parametros de avance
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

tiempoActual = 0  # reloj de la simulación

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
    global diferencia
    part = memoria[idxParticion]
    diferencia = part["tam"] - proceso[1]

    # La partición se recorta al tamaño exacto del proceso
    part["tam"] = proceso[1]
    part["proceso"] = proceso[0]

    # Si quedo espacio, se crea una nueva partición libre a continuación
    if diferencia >= 0:
        nuevaBase = part["base"] + part["tam"]
        nuevaParticion = {
            "id": siguienteIdParticion,
            "base": nuevaBase,
            "tam": diferencia,
            "proceso": "LIBRE",
        }

        siguienteIdParticion += 1
        memoria.insert(idxParticion + 1, nuevaParticion)
    

#ingresa a Listos o listos y susp, con decisión manual del usuario por cada candidato

def cargarNuevos(tiempoActual):
    global totalEnListas
    candidatos = [p for p in colaNuevos if p["TA"] <= tiempoActual]

    for proceso in candidatos:
        if totalEnListas >= 5:
            print("Listas llenas, no se admiten más procesos por ahora")
            break

        respuesta = input(
            f"Proceso {proceso['id']} disponible en t={tiempoActual} "
            f"(TA={proceso['TA']}, TI={proceso['TI']}). ¿Admitir a Listos ahora? (s/n): "
        )
        if respuesta.strip().lower() != "s":
            continue  # el usuario decide no admitirlo todavía, sigue en colaNuevos

        idx = best_FIT(proceso["tam"])
        #Si es -1 no hay particiones disponibles y va a listos y susp
        if idx == -1:
            colaListosYSusp.append(proceso)
        else:
            asignarParticion(idx, proceso)
            proceso["restante"] = proceso["TI"]
            proceso["tUltimaActualizacion"] = tiempoActual
            colaListos.append(proceso)
            #algoritmo_SRTF(proceso, tiempoActual)  # acá puede ocurrir la interrupción

        colaNuevos.remove(proceso)
        totalEnListas += 1


#revisa colaListosYSusp cada vez que se libera una partición, por si alguno ahora entra en memoria

def admitirSuspendidos():
    pendientes = colaListosYSusp[:]
    for proceso in pendientes:
        idx = best_FIT(proceso[1])
        if idx == -1:
            continue  # sigue sin entrar, se queda en colaListosYSusp

        asignarParticion(idx, proceso)
        colaListos.append(proceso)
        colaListosYSusp.remove(proceso)


#elige de colaListos al de menor tiempo remanente, cuando la CPU queda libre sin arribo simultáneo

def elegirSiguienteProceso(tiempoActual):
    global procesoEnEjecucion

    if procesoEnEjecucion is not None or not memoria:
        return  # la CPU ya está ocupada, o no hay nadie esperando

    siguiente = min(memoria, key=lambda p: p["restante"])
    memoria.remove(siguiente)
    siguiente["tUltimaActualizacion"] = tiempoActual
    procesoEnEjecucion = siguiente


# ---------- Reloj de la simulación ----------

def pausar():
    input("\nPresione ENTER para avanzar la simulación...")


def obtenerProximoEvento():
    """
    Calcula el próximo instante en el que hay que detener el reloj:
    el arribo pendiente más próximo, o la finalización del proceso en ejecución.
    Devuelve None si no queda ningún evento por procesar.
    """
    candidatos = []

    arribosPendientes = [p["TA"] for p in colaNuevos if p["TA"] > tiempoActual]
    if arribosPendientes:
        candidatos.append(min(arribosPendientes))

    if procesoEnEjecucion is not None:
        tiempoFinalizacion = tiempoActual + procesoEnEjecucion["restante"]
        candidatos.append(tiempoFinalizacion)

    if not candidatos:
        return None
    return min(candidatos)


def avanzarReloj():
    global tiempoActual, procesoEnEjecucion

    proximoEvento = obtenerProximoEvento()
    if proximoEvento is None:
        return False  # no queda nada por procesar

    pausar()

    # actualizo el remanente del proceso en ejecución hasta el nuevo instante
    procesoQueTermina = None
    if procesoEnEjecucion is not None:
        transcurrido = proximoEvento - procesoEnEjecucion["tUltimaActualizacion"]
        procesoEnEjecucion["restante"] -= transcurrido
        procesoEnEjecucion["tUltimaActualizacion"] = proximoEvento
        if procesoEnEjecucion["restante"] == 0:
            procesoQueTermina = procesoEnEjecucion

    tiempoActual = proximoEvento

    # si terminó, lo finalizo, libero memoria y reviso si algún suspendido entra ahora
    if procesoQueTermina is not None:
        #finalizarProceso(procesoQueTermina, tiempoActual)
        procesoEnEjecucion = None
        admitirSuspendidos(tiempoActual)

    # el usuario decide, uno por uno, si admite a Listos los procesos ya arribados
    cargarNuevos(tiempoActual)

    # red de contención: si la CPU sigue libre, elijo el de menor remanente en Listos
    elegirSiguienteProceso(tiempoActual)

    return True


def simular():
    global tiempoActual
    print(f"Inicio de la simulación en t={tiempoActual}")
    while avanzarReloj():
        print(f"\n--- Estado en t={tiempoActual} ---")
        # acá después va mostrarEstado()
    print("Simulación finalizada: no quedan más eventos.")