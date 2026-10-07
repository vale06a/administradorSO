from administradorCPU import *
import csv
from pathlib import Path


def leerArchivo():

    carpeta = Path.cwd().parent
    archivos = sorted(carpeta.rglob("*.csv"))

    if not archivos:
        print("No se encontró ningún .csv. Directorio actual:", Path.cwd())
        return

    with open(archivos[0], newline="", encoding="utf-8") as f:
        filas = list(csv.reader(f))

    print("PROCESOS:")
    for fila in filas:
        if not fila or not fila[0].strip().isnumeric():
            continue  # salta encabezado o líneas vacías
        id_, tam, ta, ti = (int(v) for v in fila[:4])
        proceso = {"id": id_, "tam": tam, "TA": ta, "TI": ti}
        colaNuevos.append(proceso)
        print(proceso)

    # Los procesos quedan en colaNuevos. Se admiten progresivamente según
    # su TA y el límite de 5 (Ejecución + Listos + Listos/Susp) dentro
    # del loop tick a tick de mostrarCPU, vía cargarNuevos().

    def mostrarCPU():
        global procesoEnEjecucion

        w_t, w_id, w_tam, w_ta, w_ti = 8, 5, 25, 7, 7

        def fila(t, id_, tam, ta, ti):
            return (f"│ {t:^{w_t}} │ {id_:^{w_id}} │ {tam:^{w_tam}} "
                    f"│ {ta:^{w_ta}} │ {ti:^{w_ti}} │")

        encabezado = fila("Tiempo", "ID", "Tamaño (KB)", "TA", "TI")
        ancho = len(encabezado)

        print("┌" + "─" * (ancho - 2) + "┐")
        print(encabezado)
        print("├" + "─" * (ancho - 2) + "┤")

        tiempo = 0

        while colaNuevos or colaListos or colaListosYSusp or procesoEnEjecucion is not None:

            # admite procesos cuyo TA ya llegó, respetando el límite de 5
            cargarNuevos(tiempo)

            # si terminó el proceso en ejecución, lo libero y reviso suspendidos
            if procesoEnEjecucion is not None and procesoEnEjecucion["restante"] == 0:
                finalizarProceso(procesoEnEjecucion, tiempo)
                procesoEnEjecucion = None
                admitirSuspendidos(tiempo)

            # si no hay nada corriendo ni en Listos, intento habilitar suspendidos
            if procesoEnEjecucion is None and not colaListos:
                admitirSuspendidos(tiempo)

            # selección / expropiación SRTF
            if colaListos:
                mejorProceso = min(colaListos, key=lambda p: p["restante"])
                if procesoEnEjecucion is None:
                    colaListos.remove(mejorProceso)
                    procesoEnEjecucion = mejorProceso
                elif mejorProceso["restante"] < procesoEnEjecucion["restante"]:
                    colaListos.append(procesoEnEjecucion)
                    colaListos.remove(mejorProceso)
                    procesoEnEjecucion = mejorProceso

            if procesoEnEjecucion is None:
                if not colaNuevos:
                    # no queda nada por llegar ni nada para correr: quedó trabado
                    break
                tiempo += 1
                continue

            p = procesoEnEjecucion
            print(fila(f"t = {tiempo}", p["id"], p["tam"], p["TA"], p["restante"]))

            procesoEnEjecucion["restante"] -= 1
            tiempo += 1

        if colaListosYSusp:
            print("Procesos que no llegaron a ejecutarse por falta de memoria:")
            for proceso in colaListosYSusp:
                print(proceso)

        input("Presione ENTER para volver: ")
        interactuar()

    def mostrarMemoria():
        w_t, w_id, w_tam, w_ta = 8, 5, 25, 7

        def fila(t, id_, tam, ta):
            return (f"│ {t:^{w_t}} │ {id_:^{w_id}} │ {tam:^{w_tam}} │ {ta:^{w_ta}} │")

        encabezado = fila("Id_Particion", "dir_Particion", "Tamaño (KB)", "id_proceso")
        ancho = len(encabezado)

        print("┌" + "─" * (ancho - 2) + "┐")
        print("|" + " MEMORIA ".center(70) + " |")
        print("├" + "─" * (ancho - 2) + "┤")
        print(encabezado)
        print("├" + "─" * (ancho - 2) + "┤")

        for p in memoria:
            print("| " f"{str(p['id']):^12}" " | "
                  f"{str(p['base']):^13}" " | "
                  f"{str(p['tam']):^25}" " | "
                  f"{str(p['proceso']):^10}" " | ")

        print("└ " + "─" * (ancho - 3) + "┘")

        input("Presione ENTER para volver: ")
        interactuar()

    def mostrarParticiones():
        tabla_particiones = []
        frag_ext = 0
        totalMemoria = 0

        for part in memoria:
            if part["proceso"] == "SO":
                continue  # la partición del SO no es parte del área de usuarios

            tabla_particiones.append({
                "id_particion": part["id"],
                "dirParticion": part["base"],
                "tamaño": part["tam"],
                "id_proceso": part["proceso"],
            })

            if part["proceso"] == "LIBRE":
                frag_ext += part["tam"]
            else:
                totalMemoria += part["tam"]

        w_t, w_id, w_tam, w_ta = 8, 5, 25, 7

        def fila(t, id_, tam, ta):
            return (f"│ {t:^{w_t}} │ {id_:^{w_id}} │ {tam:^{w_tam}} │ {ta:^{w_ta}} │")

        encabezado = fila("Id_Particion", "dir_Particion", "Tamaño (KB)", "id_proceso")
        ancho = len(encabezado)

        print("┌" + "─" * (ancho - 2) + "┐")
        print("|" + " PARTICIONES ".center(70) + " |")
        print("├" + "─" * (ancho - 2) + "┤")
        print(encabezado)
        print("├" + "─" * (ancho - 2) + "┤")

        for p in tabla_particiones:
            print("| " f"{str(p['id_particion']):^12}" " | "
                  f"{str(p['dirParticion']):^13}" " | "
                  f"{str(p['tamaño']):^25}" " | "
                  f"{str(p['id_proceso']):^10}" " | ")

        print("├ " + "─" * (ancho - 3) + "┤")
        print(f"{'| MEMORIA TOTAL OCUPADA:'}{str(totalMemoria):>47}" " | ")
        print(f"{'| FRAGMENTACION EXTERNA:'}{str(frag_ext):>47}" " | ")
        print("└ " + "─" * (ancho - 3) + "┘")

        input("Presione ENTER para volver: ")
        interactuar()

    from main import inicio

    def interactuar():
        bandera = True
        while bandera:
            bandera = False
            print("\n¿Que desea ver?")
            print("Presione 1 si quiere ver las particiones")
            print("Presione 2 si quiere ver que procesos estan cargados en memoria")
            print("Presiones 3 si quiere ver que proceso esta en ejecucion")
            print("Presione 4 para volver al menu principal")
            op = int(input())

            if op == 1:
                mostrarParticiones()
            elif op == 2:
                mostrarMemoria()
            elif op == 3:
                mostrarCPU()
            elif op == 4:
                inicio()
            else:
                bandera = True
                print("Ingrese una opcion valida\n")

    interactuar()
