from administradorCPU import *
import xml.etree.ElementTree as ET
from pathlib import Path

def leerArchivo():


    NS = {"svg": "http://www.w3.org/2000/svg"}

    carpeta = Path.cwd().parent

    archivos = list(carpeta.rglob("*.svg")) #busca algun archivo .svg

    if not archivos:
        print("No se encontró ningún .svg. Directorio actual:", Path.cwd())

    NS = {"svg": "http://www.w3.org/2000/svg"}

    arbol = ET.parse(archivos[0]) #almacena solamente el primer archivo .svg
    raiz = arbol.getroot()

    print("PROCESOS:")
    count = 0
    for tspan in raiz.iterfind(".//svg:tspan", NS):
        print(tspan.text)
        linea = tspan.text.strip()

        #algoritmo para guardar en la cola de nuevos
        if count > 2:
            celdas = [c.strip() for c in linea.strip("|").split("|")]
            if celdas[0].isnumeric():          # descarta el encabezado ("ID")
                colaNuevos.append([int(c) for c in celdas]) #se carga la cola de nuevos con los procesos

        count += 1

    #cargo la cola de listos/memoria y la cola de listos/susp
    for procesos in colaNuevos[:]:
        mejorParticion = best_FIT(procesos[1]) 

        if mejorParticion == -1:
            colaListosYSusp.append(procesos)
            colaNuevos.remove(procesos)
            continue

        asignarParticion(mejorParticion, procesos)
        colaListos.append(procesos)
        colaNuevos.remove(procesos)

    def mostrarCPU():

        w_t, w_id, w_tam, w_ta, w_ti = 8, 5, 25, 7, 7

        def fila(t, id_, tam, ta, ti):
            return (f"│ {t:^{w_t}} │ {id_:^{w_id}} │ {tam:^{w_tam}} "
                    f"│ {ta:^{w_ta}} │ {ti:^{w_ti}} │")

        encabezado = fila("Tiempo", "ID", "Tamaño (KB)", "TA", "TI")
        ancho = len(encabezado)

        print("┌" + "─" * (ancho - 2) + "┐")
        print(encabezado)
        print("├" + "─" * (ancho - 2) + "┤")

        global procesoEnEjecucion
        tiempo = 0

        while colaListos or colaListosYSusp or procesoEnEjecucion is not None:

            if procesoEnEjecucion is not None and procesoEnEjecucion[3] == 0: #controlo si termino el proceso
                colaTerminados.append(procesoEnEjecucion)
                for part in memoria:
                    if part["proceso"] == procesoEnEjecucion[0]:
                        part["proceso"] = "LIBRE"
                        procesoEnEjecucion = None
                        admitirSuspendidos()

            #Si no hay nada listo ni en ejecución, intentar admitir suspendidos
            if procesoEnEjecucion is None and not colaListos:
                admitirSuspendidos()
                if not colaListos:
                    print("Procesos que no se ejecutaron por falta de memoria: ")
                    for procesos in colaNuevos:
                        print(fila(f"t = {tiempo}", procesos[0], procesos[1], procesos[2], procesos[4]))
                    break                        

                
            if colaListos:
                mejorProceso = min(colaListos, key=lambda p: p[3]) #toma el menor tiempo restante (SRTF)
                if procesoEnEjecucion is None:
                    procesoEnEjecucion = mejorProceso
                    procesoEnEjecucion[2] = tiempo
                    colaListos.remove(mejorProceso)
                elif mejorProceso[3] < procesoEnEjecucion[3]: #trata la expropiación
                    colaListos.append(procesoEnEjecucion)
                    procesoEnEjecucion = mejorProceso
                    procesoEnEjecucion[2] = tiempo
                    colaListos.remove(mejorProceso)

            p = procesoEnEjecucion
            print(fila(f"t = {tiempo}", p[0], p[1], p[2], p[3]))


            procesoEnEjecucion[3] -= 1
            tiempo += 1

            input(print("Presione ENTER para volver: "))
            interactuar()


    def mostrarMemoria():
        w_t, w_id, w_tam, w_ta = 8, 5, 25, 7
            
        def fila(t, id_, tam, ta):
            return (f"│ {t:^{w_t}} │ {id_:^{w_id}} │ {tam:^{w_tam}} │ {ta:^{w_ta}} │")
            
        encabezado = fila("Id_Particion", "dir_Particion", "Tamaño (KB)", "id_proceso")
        ancho = len(encabezado)
            
        print("┌" + "─" * (ancho - 2) + "┐")
        print("|" +" MEMORIA ".center(70)+" |")
        print("├" + "─" * (ancho - 2) + "┤")
        print(encabezado)
        print("├" + "─" * (ancho - 2) + "┤")
        
        for p in memoria:
            print("| "f"{str(p["id"]):^12}"" | "
                f"{str(p["base"]):^13}" " | "
                f"{str(p["tam"]):^25}" " | "
                f"{str(p["proceso"]):^10}"" | ")
        
        print("└ "+ "─" * (ancho - 3) + "┘")

        input(print("Presione ENTER para volver: "))
        interactuar()


    tabla_particiones = []

    def mostrarParticiones():
        frag_ext = 550
        totalMemoria = 0
        for proceso in range(len(memoria) - 1):
            nuevaParticion = {
                "id_particion": memoria[proceso]["id"],
                "dirParticion": memoria[proceso]["base"],
                "tamaño": memoria[proceso]["tam"],
                "id_proceso": memoria[proceso]["proceso"]
            }
            totalMemoria = totalMemoria + memoria[proceso]["tam"]
            frag_ext = frag_ext - memoria[proceso]["tam"]
            tabla_particiones.append(nuevaParticion)

        w_t, w_id, w_tam, w_ta = 8, 5, 25, 7
        
        def fila(t, id_, tam, ta):
            return (f"│ {t:^{w_t}} │ {id_:^{w_id}} │ {tam:^{w_tam}} │ {ta:^{w_ta}} │")
        
        encabezado = fila("Id_Particion", "dir_Particion", "Tamaño (KB)", "id_proceso")
        ancho = len(encabezado)
        
        print("┌" + "─" * (ancho - 2) + "┐")
        print("|" +" PARTICIONES ".center(70)+" |")
        print("├" + "─" * (ancho - 2) + "┤")
        print(encabezado)
        print("├" + "─" * (ancho - 2) + "┤")

        for p in tabla_particiones:
            print("| "f"{str(p["id_particion"]):^12}"" | "
                f"{str(p["dirParticion"]):^13}" " | "
                f"{str(p["tamaño"]):^25}" " | "
                f"{str(p["id_proceso"]):^10}"" | ")

        print("├ "+ "─" * (ancho - 3) + "┤")
        print(f"{'| MEMORIA TOTAL OCUPADA:'}{str(totalMemoria):>47}" " | ")
        print(f"{'| FRAGMENTACION EXTERNA:'}{str(frag_ext):>47}" " | ")
        print("└ "+ "─" * (ancho - 3) + "┘")

        input(print("Presione ENTER para volver: "))
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