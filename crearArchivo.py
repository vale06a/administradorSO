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
        procesos.append([i, tam, ta, ti])

    with open("procesos.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["id", "tam", "TA", "TI"])
        escritor.writerows(procesos)

    leerArchivo()
