from crearArchivo import crearArchivo 
from leerArchivo import leerArchivo 
from getInformacion import getInformacion

def inicio():
    print("".center(120, "="))
    print("SIMULADOR DE MEMORIA 2026".center(120))
    print("".center(120, "="))


    bandera = True

    while bandera:
        bandera = False
        print("Presione 1 si usted ya cargo un archivo y solamente lo quiere leer \n")
        print("Presione 2 para crear un archivo con procesos cargados \n")
        print("Presione 3 para obtener informacion del equipo \n")
        opcion = int(input())
        if opcion == 1:
            leerArchivo()
        elif opcion == 2:
            crearArchivo()
        elif opcion == 3:
            getInformacion()
        else:
            bandera = True
            print("Ingrese una opcion válida")

inicio()