# motorSnapshot.py — corre la simulación entera UNA sola vez y devuelve la
# lista completa de snapshots (uno por instante) + informe final.
# Reutiliza las funciones y el estado global de administradorCPU.
import copy
import administradorCPU as cpu


def _snapshot(t, evento, todosLosProcesos):
    """Toma una foto del estado del simulador en el instante t."""
    return {
        "t": t,
        "evento": evento,
        "memoria": copy.deepcopy(cpu.memoria),
        "colaNuevos":      [p["id"] for p in cpu.colaNuevos],
        "colaListos":      [p["id"] for p in cpu.colaListos],
        "colaListosYSusp": [p["id"] for p in cpu.colaListosYSusp],
        "colaTerminados":  [p["id"] for p in cpu.colaTerminados],
        "procesoEnEjecucion": (cpu.procesoEnEjecucion["id"]
                               if cpu.procesoEnEjecucion else None),
        "procesos": [dict(p) for p in todosLosProcesos],  # con TR, TE, estado
        "totalEnListas": cpu.totalEnListas,
    }


def correrSimulacion(procesos):
    """Corre la simulación completa y devuelve (snapshots, informeFinal).

    snapshots: lista de snapshots (uno por instante relevante, desde t=0 hasta
    el instante en que termina el último proceso) más un snapshot extra
    'informe final' que la UI usa como último punto navegable.

    informeFinal: dict con terminados, no-ejecutados, promedios, rendimiento.
    """
    cpu.reiniciarSimulador()

    # Trabajamos sobre copias para no modificar la lista que el usuario pasó
    todosLosProcesos = [dict(p) for p in procesos]
    cpu.colaNuevos.extend(todosLosProcesos)

    snapshots = [_snapshot(0, "Inicio de la simulación", todosLosProcesos)]

    tiempo = 0
    maxIter = 100000
    it = 0

    while (cpu.colaNuevos or cpu.colaListos or cpu.colaListosYSusp
           or cpu.procesoEnEjecucion is not None) and it < maxIter:
        it += 1
        eventos = []

        # Detectar ingresos de procesos nuevos
        idsNuevosAntes = {p["id"] for p in cpu.colaNuevos}
        susAntes = [p["id"] for p in cpu.colaListosYSusp]

        cpu.cargarNuevos(tiempo)

        idsIngresados = sorted(idsNuevosAntes
                               - {p["id"] for p in cpu.colaNuevos})
        if idsIngresados:
            etiquetas = ", ".join(f"P{i}" for i in idsIngresados)
            eventos.append(f"Ingresó {etiquetas}")

        # Finalización del proceso en ejecución
        if (cpu.procesoEnEjecucion is not None
                and cpu.procesoEnEjecucion["restante"] == 0):
            idTerm = cpu.procesoEnEjecucion["id"]
            cpu.finalizarProceso(cpu.procesoEnEjecucion, tiempo)
            cpu.procesoEnEjecucion = None
            eventos.append(f"Finalizó P{idTerm}")
            cpu.admitirSuspendidos(tiempo)

        if cpu.procesoEnEjecucion is None and not cpu.colaListos:
            cpu.admitirSuspendidos(tiempo)

        # Detectar swap-in
        susDespues = [p["id"] for p in cpu.colaListosYSusp]
        swapIn = [i for i in susAntes if i not in susDespues]
        if swapIn:
            etiquetas = ", ".join(f"P{i}" for i in swapIn)
            eventos.append(f"Swap-in: {etiquetas} entró a memoria")

        # Selección / expropiación SRTF
        if cpu.colaListos:
            mejor = min(cpu.colaListos, key=lambda p: p["restante"])
            if cpu.procesoEnEjecucion is None:
                cpu.colaListos.remove(mejor)
                cpu.procesoEnEjecucion = mejor
                eventos.append(f"CPU toma P{mejor['id']}")
            elif mejor["restante"] < cpu.procesoEnEjecucion["restante"]:
                anterior = cpu.procesoEnEjecucion["id"]
                cpu.colaListos.append(cpu.procesoEnEjecucion)
                cpu.colaListos.remove(mejor)
                cpu.procesoEnEjecucion = mejor
                eventos.append(
                    f"Preempción SRTF: P{mejor['id']} desplaza a P{anterior}")

        # CPU ociosa: saltar al próximo arribo
        if cpu.procesoEnEjecucion is None:
            if not cpu.colaNuevos:
                snapshots.append(_snapshot(
                    tiempo, "; ".join(eventos) or "CPU ociosa",
                    todosLosProcesos))
                break
            proximoTA = min(p["TA"] for p in cpu.colaNuevos)
            if proximoTA > tiempo:
                eventos.append(
                    f"CPU OCIOSA — salto al próximo arribo t={proximoTA}")
                snapshots.append(_snapshot(
                    tiempo, "; ".join(eventos), todosLosProcesos))
                tiempo = proximoTA
                continue
            tiempo += 1
            continue

        # Snapshot del instante actual (antes de consumir el tick)
        descripcion = "; ".join(eventos) if eventos else "Ejecución en curso"
        snapshots.append(_snapshot(tiempo, descripcion, todosLosProcesos))

        cpu.procesoEnEjecucion["restante"] -= 1
        tiempo += 1

    # Informe final
    informeFinal = {
        "terminados": [dict(p) for p in cpu.colaTerminados],
        "noEjecutados": [dict(p) for p in cpu.colaListosYSusp],
        "tiempoTotal": max((p["tFin"] for p in cpu.colaTerminados),
                           default=0),
    }
    if informeFinal["terminados"]:
        n = len(informeFinal["terminados"])
        informeFinal["promedioTR"] = (
            sum(p["TR"] for p in informeFinal["terminados"]) / n)
        informeFinal["promedioTE"] = (
            sum(p["TE"] for p in informeFinal["terminados"]) / n)
        informeFinal["rendimiento"] = (
            n / informeFinal["tiempoTotal"]
            if informeFinal["tiempoTotal"] > 0 else 0)
    else:
        informeFinal["promedioTR"] = 0
        informeFinal["promedioTE"] = 0
        informeFinal["rendimiento"] = 0

    return snapshots, informeFinal
