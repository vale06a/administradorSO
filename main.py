from crearArchivo import crearArchivo 
from leerArchivo import leerArchivo 
from getInformacion import getInformacion
from simulacionPrueba import simulacionEventos

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
        print("Presione 4 para iniciar una simulación de prueba (10 procesos fijos) \n")
        opcion = int(input())
        if opcion == 1:
            leerArchivo()
        elif opcion == 2:
            crearArchivo()
        elif opcion == 3:
            getInformacion()
        elif opcion == 4:
            simulacionEventos()
            inicio()
        else:
            bandera = True
            print("Ingrese una opcion válida")


if __name__ == "__main__":
    inicio()
