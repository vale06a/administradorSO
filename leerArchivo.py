from administradorCPU import *
import csv
from pathlib import Path


def _mostrarFormatoEsperado():
    print()
    print("Formato esperado del archivo .csv (igual al enunciado de la cátedra):")
    print("  - Archivo de texto plano con extensión .csv y separador coma.")
    print("  - (Opcional) una primera línea con los nombres de las columnas.")
    print("  - Cada línea restante representa UN proceso con 4 columnas,")
    print("    en el siguiente orden:")
    print("        Proceso, TA, TI, Tamaño")
    print("    donde:")
    print("        Proceso = identificador del proceso. Se aceptan ambos")
    print("                  formatos: con prefijo P (P1, P2, ..., Px)")
    print("                  o directamente el número (1, 2, ..., x).")
    print("        TA      = tiempo de arribo        (entero mayor o igual a 0)")
    print("        TI      = tiempo de irrupción    (entero mayor a 0)")
    print("        Tamaño  = tamaño del proceso en KB (entero mayor a 0)")
    print("  - Máximo 10 procesos en total.")
    print()
    print("Ejemplo valido:")
    print("        Proceso,TA,TI,Tamaño")
    print("        P1,3,2,120")
    print("        P2,10,4,130")
    print("        P3,10,1,40")
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
    # Orden de columnas esperado (como en el PDF de la cátedra):
    #     Proceso, TA, TI, Tamaño
    # El campo Proceso acepta "P1", "p2", "P10" o simplemente "1", "2"...
    procesosArchivo = []
    for nroLinea, fila in enumerate(filas, start=1):
        if not fila or all(not c.strip() for c in fila):
            continue  # línea vacía: se ignora

        primera = fila[0].strip()
        # Si la primera celda no empieza con un número ni con P+número,
        # asumimos cabecera (solo si estamos antes del primer proceso).
        esIdPrefijado = (len(primera) > 1 and primera[0] in "Pp"
                         and primera[1:].isnumeric())
        esIdNumero = primera.isnumeric()
        if not (esIdPrefijado or esIdNumero):
            if not procesosArchivo:
                continue  # cabecera inicial, OK
            print(f"ERROR en la línea {nroLinea}: se esperaba un proceso "
                  f"cuya primera columna sea un identificador (P1, P2, ... "
                  f"o directamente un número).")
            print(f"       Línea leída: {fila}")
            _mostrarFormatoEsperado()
            return

        if len(fila) < 4:
            print(f"ERROR en la línea {nroLinea}: se esperan 4 columnas "
                  f"(Proceso, TA, TI, Tamaño) pero se encontraron {len(fila)}.")
            print(f"       Línea leída: {fila}")
            _mostrarFormatoEsperado()
            return

        try:
            # Primera columna (Proceso): puede venir como "P1" o como "1".
            # Nos quedamos con el número interno.
            idRaw = primera.lstrip("Pp")
            id_ = int(idRaw)
            # Las otras tres columnas en el orden del PDF: TA, TI, Tamaño.
            ta  = int(fila[1].strip())
            ti  = int(fila[2].strip())
            tam = int(fila[3].strip())
        except ValueError:
            print(f"ERROR en la línea {nroLinea}: las columnas TA, TI y "
                  f"Tamaño deben ser números enteros, y Proceso debe ser "
                  f"'P' seguido de un número o un número directamente.")
            print(f"       Línea leída: {fila[:4]}")
            _mostrarFormatoEsperado()
            return

        if tam <= 0 or ti <= 0 or ta < 0 or id_ < 0:
            print(f"ERROR en la línea {nroLinea}: valores fuera de rango. "
                  f"Se requiere Proceso >= 0, TA >= 0, TI > 0, Tamaño > 0.")
            print(f"       Recibido: Proceso=P{id_}, TA={ta}, TI={ti}, Tamaño={tam}")
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
        print(f"  P{proceso['id']}: TA={proceso['TA']}  TI={proceso['TI']}  "
              f"Tamaño={proceso['tam']}K")

    # Guardamos una copia de los procesos cargados para poder reusarlos
    # desde la opción "Ejecutar simulación paso a paso". Si el usuario
    # elige esa opción, el simulador se reinicia y se recarga con esta
    # lista (porque colaNuevos puede haberse consumido por otras opciones).
    procesosCargados = [dict(p) for p in procesosArchivo]

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
            print("Presione 3 si quiere ver la simulación tick a tick (sin pausas)")
            print("Presione 4 para ejecutar la simulación paso a paso con avance manual")
            print("Presione 5 para volver al menu principal")
            op = int(input())

            if op == 1:
                mostrarParticiones()
            elif op == 2:
                mostrarMemoria()
            elif op == 3:
                mostrarCPU()
            elif op == 4:
                # Simulación por eventos con los procesos cargados del CSV
                from simulacionPrueba import simulacionEventos
                simulacionEventos(procesos=procesosCargados)
                interactuar()
            elif op == 5:
                inicio()
            else:
                bandera = True
                print("Ingrese una opcion valida\n")

    interactuar()
