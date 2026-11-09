# simulacionPrueba.py — interfaz de consola para probar el simulador con
# 10 procesos ya determinados. Avanza por sucesos relevantes (inicio,
# ingreso de un proceso, finalización de un proceso, o cualquier cambio
# en memoria), no tick a tick.

import administradorCPU as cpu

try:
    import msvcrt
except ImportError:
    msvcrt = None


# 10 procesos fijos: id, tamaño (KB), TA (arribo), TI (ráfaga/irrupción)
PROCESOS_DEMO = [
    {"id": 0, "tam": 100, "TA": 0,  "TI": 5},
    {"id": 1, "tam": 150, "TA": 1,  "TI": 8},
    {"id": 2, "tam": 80,  "TA": 2,  "TI": 3},
    {"id": 3, "tam": 200, "TA": 3,  "TI": 10},
    {"id": 4, "tam": 60,  "TA": 4,  "TI": 4},
    {"id": 5, "tam": 120, "TA": 6,  "TI": 6},
    {"id": 6, "tam": 90,  "TA": 8,  "TI": 7},
    {"id": 7, "tam": 150, "TA": 10, "TI": 5},
    {"id": 8, "tam": 70,  "TA": 12, "TI": 9},
    {"id": 9, "tam": 110, "TA": 14, "TI": 4},
]


def esperarAvance():
    if msvcrt:
        print("(presione 'a' o barra espaciadora para avanzar al próximo evento)")
        while True:
            tecla = msvcrt.getch()
            if tecla in (b"a", b"A", b" "):
                return
    else:
        # alternativa para sistemas sin msvcrt (no Windows)
        while True:
            tecla = input("Presione 'a' o espacio y Enter para avanzar: ")
            if tecla.lower() in ("a", " ", ""):
                return


def obtenerEstado(proceso):
    if proceso is cpu.procesoEnEjecucion:
        return "EJECUCION"
    if proceso in cpu.colaListos:
        return "LISTO"
    if proceso in cpu.colaListosYSusp:
        return "LISTO/SUSP"
    if proceso in cpu.colaTerminados:
        return "TERMINADO"
    return "NUEVO"


def imprimirEstadoProcesador(tiempoActual):
    # Estado explícito del procesador en el instante t (requerido por la
    # devolución general): quién ejecuta o si la CPU está ociosa.
    print(f"\n>>> ESTADO DEL PROCESADOR (t={tiempoActual}) <<<")
    if cpu.procesoEnEjecucion is None:
        print("    Procesador: CPU OCIOSA")
    else:
        p = cpu.procesoEnEjecucion
        print(f"    Procesador: ejecutando P{p['id']} "
              f"(restante={p['restante']}, TI={p['TI']})")


def imprimirTablaProcesos(procesos, tiempoActual):
    print(f"\n--- ESTADO DE PROCESOS (t={tiempoActual}) ---")
    encabezado = (f"{'ID':^4} | {'Tam':^5} | {'TA':^4} | {'TI':^4} | "
                  f"{'Estado':^12} | {'Rest':^5} | {'TR':^5} | {'TE':^5}")
    print(encabezado)
    print("-" * len(encabezado))
    for p in procesos:
        estado = obtenerEstado(p)
        restante = p.get("restante", "-")
        tr = p.get("TR", "-")
        te = p.get("TE", "-")
        print(f"{p['id']:^4} | {p['tam']:^5} | {p['TA']:^4} | {p['TI']:^4} | "
              f"{estado:^12} | {restante:^5} | {tr:^5} | {te:^5}")


def imprimirTablaMemoria():
    # En MVT con best-fit que recorta al tamaño exacto, la fragmentación
    # interna es siempre 0 (se incluye la columna igual porque forma parte
    # de lo que se pide mostrar en la tabla de particiones).
    print("\n--- ESTADO DE MEMORIA (particiones) ---")
    encabezado = (f"{'Particion':^10} | {'Base':^6} | {'Tam':^5} | "
                  f"{'Ocupante':^10} | {'Frag.Int':^9}")
    print(encabezado)
    print("-" * len(encabezado))
    for part in cpu.memoria:
        if part["proceso"] == "SO":
            frag_int = 0
        elif part["proceso"] == "LIBRE":
            frag_int = "-"
        else:
            frag_int = 0  # best-fit recorta al tamaño exacto → nunca hay sobrante
        print(f"{part['id']:^10} | {part['base']:^6} | {part['tam']:^5} | "
              f"{str(part['proceso']):^10} | {str(frag_int):^9}")


def imprimirColas():
    # Vista compacta de las colas requerida por la devolución general.
    listos = [f"P{p['id']}" for p in cpu.colaListos]
    susp = [f"P{p['id']}" for p in cpu.colaListosYSusp]
    nuevos = [f"P{p['id']}" for p in cpu.colaNuevos]
    print("\n--- COLAS ---")
    print(f"    Nuevos            : {nuevos if nuevos else '(vacía)'}")
    print(f"    Listos            : {listos if listos else '(vacía)'}")
    print(f"    Listos/Suspendidos: {susp if susp else '(vacía)'}")


def imprimirEstadoCompleto(procesos, tiempoActual):
    imprimirEstadoProcesador(tiempoActual)
    imprimirTablaMemoria()
    imprimirColas()
    imprimirTablaProcesos(procesos, tiempoActual)


def simulacionEventos():
    cpu.reiniciarSimulador()

    todosLosProcesos = [dict(p) for p in PROCESOS_DEMO]
    cpu.colaNuevos.extend(todosLosProcesos)

    tiempo = 0
    print("\n>>> INICIO DE LA SIMULACIÓN (t=0) <<<")
    imprimirEstadoCompleto(todosLosProcesos, tiempo)
    esperarAvance()

    while cpu.colaNuevos or cpu.colaListos or cpu.colaListosYSusp or cpu.procesoEnEjecucion is not None:

        # 1) ingreso de procesos cuyo TA ya llegó (solo cuenta si realmente
        # salieron de colaNuevos: si el tope de 5 los frena, siguen ahí)
        candidatosAntes = {p["id"] for p in cpu.colaNuevos if p["TA"] <= tiempo}
        cpu.cargarNuevos(tiempo)
        idsEnNuevosDespues = {p["id"] for p in cpu.colaNuevos}
        idsIngresando = [pid for pid in candidatosAntes if pid not in idsEnNuevosDespues]
        ingresoAlgo = bool(idsIngresando)

        # 2) finalización del proceso en ejecución
        terminoAlgo = False
        idTerminado = None
        susAntes = len(cpu.colaListosYSusp)

        if cpu.procesoEnEjecucion is not None and cpu.procesoEnEjecucion["restante"] == 0:
            idTerminado = cpu.procesoEnEjecucion["id"]
            cpu.finalizarProceso(cpu.procesoEnEjecucion, tiempo)
            cpu.procesoEnEjecucion = None
            terminoAlgo = True
            cpu.admitirSuspendidos(tiempo)

        if cpu.procesoEnEjecucion is None and not cpu.colaListos:
            cpu.admitirSuspendidos(tiempo)

        # 3) ¿algún suspendido consiguió memoria recién ahora?
        memoriaCambioPorSuspendido = len(cpu.colaListosYSusp) != susAntes

        # 4) selección / expropiación SRTF (no es un "evento" en sí mismo,
        # pero puede dejar a un proceso distinto en ejecución)
        if cpu.colaListos:
            mejor = min(cpu.colaListos, key=lambda p: p["restante"])
            if cpu.procesoEnEjecucion is None:
                cpu.colaListos.remove(mejor)
                cpu.procesoEnEjecucion = mejor
            elif mejor["restante"] < cpu.procesoEnEjecucion["restante"]:
                cpu.colaListos.append(cpu.procesoEnEjecucion)
                cpu.colaListos.remove(mejor)
                cpu.procesoEnEjecucion = mejor

        if ingresoAlgo or terminoAlgo or memoriaCambioPorSuspendido:
            if ingresoAlgo:
                print(f"\n>>> t={tiempo}: ingresó proceso(s) {idsIngresando} <<<")
            if terminoAlgo:
                print(f"\n>>> t={tiempo}: finalizó el proceso P{idTerminado} <<<")
            if memoriaCambioPorSuspendido and not terminoAlgo:
                print(f"\n>>> t={tiempo}: un proceso suspendido consiguió memoria <<<")
            imprimirEstadoCompleto(todosLosProcesos, tiempo)
            esperarAvance()

        # Si la CPU está ociosa y no hay nada en Listos, saltamos directo
        # al próximo arribo en lugar de avanzar tick a tick: el reloj
        # avanza pero no se descuenta tiempo de ejecución a nadie.
        if cpu.procesoEnEjecucion is None:
            if not cpu.colaNuevos:
                break
            proximoTA = min(p["TA"] for p in cpu.colaNuevos)
            if proximoTA > tiempo:
                print(f"\n>>> t={tiempo}: CPU OCIOSA — se salta al próximo "
                      f"arribo (t={proximoTA}) <<<")
                tiempo = proximoTA
            else:
                tiempo += 1
            continue

        cpu.procesoEnEjecucion["restante"] -= 1
        tiempo += 1

    print("\n>>> SIMULACIÓN FINALIZADA <<<")
    imprimirEstadoCompleto(todosLosProcesos, tiempo)
    cpu.generarInformeFinal()

    input("\nPresione ENTER para volver al menú principal: ")


if __name__ == "__main__":
    simulacionEventos()
