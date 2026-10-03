from leerArchivo import leerArchivo 

def crearArchivo():
    import random
    import html

    ta = 0
    ti = 0
    procesos = []

    for i in range(10):
        procesos.append(i)                        # id
        procesos.append(random.randint(10, 450))  # tamaño del proceso
        ta = ta + ti
        procesos.append(ta)                       # tiempo de arribo
        ti = random.randint(1, 20)
        procesos.append(ti)                       # tiempo de inserción

    def crear_svg(nombre, ancho, alto):

        # Anchos de columnas
        w_id, w_tam, w_ta, w_ti = 5, 25, 7, 7

        texto_svg = ""

        # ENCABEZADO
        informacion = (
            f"|{'ID':^{w_id}}"
            f"|{'Tamaño del proceso (KB)':^{w_tam}}"
            f"|{'TA':^{w_ta}}"
            f"|{'TI':^{w_ti}}|"
        )

        texto_svg += f'<tspan x="30" dy = "15">{html.escape("-"*50)}</tspan>\n'
        texto_svg += f'<tspan x="30" dy="15">{html.escape(informacion)}</tspan>\n'
        texto_svg += f'<tspan x="30" dy = "15">{html.escape("-"*50)}</tspan>\n'

        # FILAS
        for i in range(0, len(procesos), 4):
            proceso = (
                f"|{procesos[i]:^{w_id}}"
                f"|{procesos[i+1]:^{w_tam}}"
                f"|{procesos[i+2]:^{w_ta}}"
                f"|{procesos[i+3]:^{w_ti}} |"
            )

            texto_svg += f'<tspan x="30" dy="25">{html.escape(proceso)}</tspan>\n'

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
                        width="{ancho}" height="{alto}">

            <rect width="{ancho}" height="{alto}" fill="white"/>

            <text x="30" y="40"
                font-family="monospace"
                font-size="16"
                xml:space="preserve"
                fill="black">
                    {texto_svg}
            </text>

        </svg>'''

        with open(nombre, "w", encoding="utf-8") as archivo:
            archivo.write(svg)


    crear_svg("procesos.svg", 800, 500)

    leerArchivo()
    