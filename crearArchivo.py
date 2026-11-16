from leerArchivo import leerArchivo
import random
import csv


def crearArchivo():
    procesos = []
    ta = 0
    ti = 0

    for i in range(10):
        tam = random.randint(10, 450)
        ta = ta + ti                 # el próximo arribo depende de la irrupción anterior
        ti = random.randint(1, 20)
        procesos.append([f"P{i + 1}", ta, ti, tam])   # formato de la cátedra: Proceso, TA, TI, Tamaño

    with open("procesos.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["Proceso", "TA", "TI", "Tamaño"])
        escritor.writerows(procesos)

    leerArchivo()
