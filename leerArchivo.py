from administradorCPU import *
import csv
from pathlib import Path


def _mostrarFormatoEsperado():
    print()
    print("Formato esperado del archivo .csv:")
    print("  - Archivo de texto plano con extensión .csv y separador coma.")
    print("  - (Opcional) una primera línea con los nombres de las columnas.")
    print("  - Cada línea restante representa UN proceso con 4 columnas:")
    print("        id, tam, TA, TI")
    print("    donde:")
    print("        id  = número entero identificador del proceso")
    print("        tam = tamaño del proceso en KB  (entero mayor a 0)")
    print("        TA  = tiempo de arribo          (entero mayor o igual a 0)")
    print("        TI  = tiempo de irrupción       (entero mayor a 0)")
    print("  - Máximo 10 procesos en total.")
    print()
    print("Ejemplo valido:")
    print("        id,tam,TA,TI")
    print("        0,100,0,5")
    print("        1,150,1,8")
    print("        2,80,2,3")
    print()


def leerArchivo():

    # Pedir la ruta del archivo al usuario. Si deja vacío (solo ENTER),
    # se intenta buscar automáticamente un .csv en la carpeta padre,
    # para no romper el flujo anterior.
    print("\nIngrese la ruta completa del archivo .csv")
    print("(o presione ENTER para buscar automáticamente en la carpeta padre):")
    rutaIngresada = input().strip().strip('"').strip("'")

    if rutaIngresada:
        archivo = Path(rutaIngresada)
        if not archivo.exists():
            print(f"ERROR: no se encontró el archivo en la ruta indicada:")
            print(f"       {rutaIngresada}")
            return
        if not archivo.is_file():
            print(f"ERROR: la ruta indicada no apunta a un archivo:")
            print(f"       {rutaIngresada}")
            return
        if archivo.suffix.lower() != ".csv":
            print(f"ERROR: el archivo debe tener extensión .csv "
                  f"(recibí '{archivo.suffix}').")
            _mostrarFormatoEsperado()
            return
    else:
        carpeta = Path.cwd().parent
        archivos = sorted(carpeta.rglob("*.csv"))
        if not archivos:
            print(f"No se encontró ningún .csv en {carpeta}")
            _mostrarFormatoEsperado()
            return
        archivo = archivos[0]
        print(f"Se usará automáticamente el archivo: {archivo}")

    try:
        with open(archivo, newline="", encoding="utf-8") as f:
            filas = list(csv.reader(f))
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERROR al abrir/leer el archivo: {e}")
        _mostrarFormatoEsperado()
        return

    # Primero recolectamos los procesos del archivo en una lista temporal
    # para poder validar cantidad y formato ANTES de empezar la simulación.
    # El enunciado establece un máximo de 10 procesos.
    procesosArchivo = []
    for nroLinea, fila in enumerate(filas, start=1):
        if not fila or all(not c.strip() for c in fila):
            continue  # línea vacía: se ignora
        # Si la primera columna no es un número entero, asumimos cabecera
        # y saltamos (solo si estamos en las primeras líneas; si aparece en
        # el medio, es un error de formato que se detecta más abajo).
        if not fila[0].strip().isnumeric():
            if not procesosArchivo:
                continue  # cabecera inicial, OK
            print(f"ERROR en la línea {nroLinea}: se esperaba un proceso con "
                  f"4 valores numéricos pero la primera columna no es un entero.")
            print(f"       Línea leída: {fila}")
            _mostrarFormatoEsperado()
            return

        if len(fila) < 4:
            print(f"ERROR en la línea {nroLinea}: se esperan 4 columnas "
                  f"(id, tam, TA, TI) pero se encontraron {len(fila)}.")
            print(f"       Línea leída: {fila}")
            _mostrarFormatoEsperado()
            return

        try:
            id_, tam, ta, ti = (int(v.strip()) for v in fila[:4])
        except ValueError:
            print(f"ERROR en la línea {nroLinea}: las 4 columnas "
                  f"(id, tam, TA, TI) deben ser números enteros.")
            print(f"       Línea leída: {fila[:4]}")
            _mostrarFormatoEsperado()
            return

        if tam <= 0 or ti <= 0 or ta < 0 or id_ < 0:
            print(f"ERROR en la línea {nroLinea}: valores fuera de rango. "
                  f"Se requiere id >= 0, tam > 0, TA >= 0, TI > 0.")
            print(f"       Recibido: id={id_}, tam={tam}, TA={ta}, TI={ti}")
            _mostrarFormatoEsperado()
            return

        procesosArchivo.append({"id": id_, "tam": tam, "TA": ta, "TI": ti})

    if len(procesosArchivo) > 10:
        print(f"ERROR: el archivo tiene {len(procesosArchivo)} procesos; "
              f"el máximo permitido es 10. No se ejecuta la simulación.")
        return
    if len(procesosArchivo) == 0:
        print("ERROR: el archivo no contiene procesos válidos.")
        _mostrarFormatoEsperado()
        return

    print(f"\nPROCESOS ({len(procesosArchivo)} de 10 máximo):")
    for proceso in procesosArchivo:
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
                # CPU ociosa: en lugar de avanzar tick a tick (desperdiciando
                # tiempo), saltamos directamente al próximo arribo. No se
                # descuenta tiempo de ejecución de ningún proceso porque la
                # CPU está libre.
                proximoTA = min(p["TA"] for p in colaNuevos)
                tiempo = max(tiempo + 1, proximoTA)
                continue

            p = procesoEnEjecucion
            print(fila(f"t = {tiempo}", p["id"], p["tam"], p["TA"], p["restante"]))

            procesoEnEjecucion["restante"] -= 1
            tiempo += 1

        generarInformeFinal()

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
