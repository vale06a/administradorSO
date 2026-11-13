# simuladorGUI.py — Interfaz gráfica Tkinter para el simulador.
# Convive con la CLI (main.py) sin modificarla.
#
# Menú principal:
#   1 - Simulación precargada (los 10 procesos fijos de la demo)
#   2 - Cargar procesos desde .csv
#   3 - Cargar procesos manualmente (grilla editable, hasta 10)
#   4 - Información del grupo
#
# En 1, 2 y 3, se abre la Ventana de Simulación con navegación libre
# entre instantes (slider, botones ◀ ▶ ⏮ ⏭, campo "ir a t=X"). El
# último instante es el informe final.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from pathlib import Path

from motorSnapshot import correrSimulacion


# ======================================================================
# 10 procesos fijos para la simulación precargada (idénticos a la demo)
# ======================================================================
PROCESOS_DEMO = [
    {"id": 1,  "tam": 100, "TA": 0,  "TI": 5},
    {"id": 2,  "tam": 150, "TA": 1,  "TI": 8},
    {"id": 3,  "tam": 80,  "TA": 2,  "TI": 3},
    {"id": 4,  "tam": 200, "TA": 3,  "TI": 10},
    {"id": 5,  "tam": 60,  "TA": 4,  "TI": 4},
    {"id": 6,  "tam": 120, "TA": 6,  "TI": 6},
    {"id": 7,  "tam": 90,  "TA": 8,  "TI": 7},
    {"id": 8,  "tam": 150, "TA": 10, "TI": 5},
    {"id": 9,  "tam": 70,  "TA": 12, "TI": 9},
    {"id": 10, "tam": 110, "TA": 14, "TI": 4},
]


# ======================================================================
# Parser de CSV reusable (no reutilizo leerArchivo porque ese es CLI)
# ======================================================================
FORMATO_ESPERADO = (
    "Formato esperado del archivo .csv (igual al enunciado de la cátedra):\n"
    "  - Archivo de texto plano con extensión .csv, separador coma.\n"
    "  - (Opcional) una primera línea con los nombres de las columnas.\n"
    "  - Cada línea restante es UN proceso con 4 columnas, en este orden:\n"
    "        Proceso, TA, TI, Tamaño\n"
    "  - Proceso acepta 'P1', 'p2', ..., o directamente 1, 2, ...\n"
    "  - TA ≥ 0, TI > 0, Tamaño > 0 (todos enteros).\n"
    "  - Máximo 10 procesos.\n\n"
    "Ejemplo valido:\n"
    "    Proceso,TA,TI,Tamaño\n"
    "    P1,3,2,120\n"
    "    P2,10,4,130\n"
    "    P3,10,1,40\n"
)


def parsearCSV(ruta):
    """Devuelve (procesos, None) si el CSV es válido,
    o (None, mensaje_error) si no."""
    archivo = Path(ruta)
    if not archivo.exists():
        return None, f"No se encontró el archivo:\n{ruta}"
    if not archivo.is_file():
        return None, f"La ruta indicada no apunta a un archivo:\n{ruta}"
    if archivo.suffix.lower() != ".csv":
        return None, (f"El archivo debe tener extensión .csv "
                      f"(se recibió '{archivo.suffix}').\n\n{FORMATO_ESPERADO}")

    try:
        with open(archivo, newline="", encoding="utf-8") as f:
            filas = list(csv.reader(f))
    except (OSError, UnicodeDecodeError) as e:
        return None, f"Error al abrir/leer el archivo: {e}\n\n{FORMATO_ESPERADO}"

    procesos = []
    for nro, fila in enumerate(filas, start=1):
        if not fila or all(not c.strip() for c in fila):
            continue

        primera = fila[0].strip()
        esIdPrefijado = (len(primera) > 1 and primera[0] in "Pp"
                         and primera[1:].isnumeric())
        esIdNumero = primera.isnumeric()
        if not (esIdPrefijado or esIdNumero):
            if not procesos:
                continue  # cabecera
            return None, (f"Línea {nro}: la primera columna debería ser un "
                          f"identificador (P1, P2 … o un número).\n"
                          f"Línea leída: {fila}\n\n{FORMATO_ESPERADO}")

        if len(fila) < 4:
            return None, (f"Línea {nro}: se esperan 4 columnas y hay "
                          f"{len(fila)}.\nLínea leída: {fila}\n\n"
                          f"{FORMATO_ESPERADO}")

        try:
            id_ = int(primera.lstrip("Pp"))
            ta  = int(fila[1].strip())
            ti  = int(fila[2].strip())
            tam = int(fila[3].strip())
        except ValueError:
            return None, (f"Línea {nro}: valores no numéricos.\n"
                          f"Línea leída: {fila[:4]}\n\n{FORMATO_ESPERADO}")

        if tam <= 0 or ti <= 0 or ta < 0 or id_ < 0:
            return None, (f"Línea {nro}: valores fuera de rango.\n"
                          f"Se requiere Proceso≥0, TA≥0, TI>0, Tamaño>0.\n"
                          f"Recibido: P{id_}, TA={ta}, TI={ti}, Tamaño={tam}"
                          f"\n\n{FORMATO_ESPERADO}")

        procesos.append({"id": id_, "tam": tam, "TA": ta, "TI": ti})

    if len(procesos) == 0:
        return None, ("El archivo no contiene procesos válidos.\n\n"
                      f"{FORMATO_ESPERADO}")
    if len(procesos) > 10:
        return None, (f"El archivo tiene {len(procesos)} procesos; "
                      f"el máximo permitido es 10.")

    return procesos, None


# ======================================================================
# Ventana de simulación (navegable por instantes)
# ======================================================================
class VentanaSimulacion(tk.Toplevel):
    # Paleta de colores para los procesos en la barra de memoria
    COLORES_PROCESO = [
        "#e57373", "#64b5f6", "#81c784", "#ffb74d", "#ba68c8",
        "#4db6ac", "#f06292", "#9575cd", "#dce775", "#4fc3f7",
    ]
    COLOR_SO = "#455a64"
    COLOR_LIBRE = "#eceff1"

    def __init__(self, master, procesos, titulo="Simulación"):
        super().__init__(master)
        self.title(titulo)
        self.geometry("1100x720")

        # Corremos la simulación completa una sola vez
        self.snapshots, self.informe = correrSimulacion(procesos)
        # El informe final es el instante extra (índice == N)
        self.idxMax = len(self.snapshots)  # N = len(snaps) corresponde al informe
        self.idxActual = 0

        self._construirUI()
        self._actualizarVista()

    # ------------------------------------------------------------------
    def _construirUI(self):
        # ---- Barra de navegación superior ----
        nav = ttk.Frame(self, padding=8)
        nav.pack(side="top", fill="x")

        ttk.Button(nav, text="⏮ Inicio", command=self._alInicio).pack(side="left")
        ttk.Button(nav, text="◀ Retroceder", command=self._retroceder).pack(side="left", padx=4)
        ttk.Button(nav, text="▶ Avanzar", command=self._avanzar).pack(side="left")
        ttk.Button(nav, text="⏭ Fin (informe)", command=self._alFin).pack(side="left", padx=4)

        ttk.Button(nav, text="✕ Volver al menú",
                   command=self._volverAlMenu).pack(side="right")
        self.lblInstante = ttk.Label(nav, text="", font=("Segoe UI", 11, "bold"))
        self.lblInstante.pack(side="right", padx=12)

        # ---- Slider ----
        sliderFrame = ttk.Frame(self, padding=(8, 0, 8, 4))
        sliderFrame.pack(side="top", fill="x")
        self.slider = ttk.Scale(
            sliderFrame, from_=0, to=self.idxMax,
            orient="horizontal", command=self._alSlider,
        )
        self.slider.pack(fill="x")

        # ---- Evento del instante ----
        eventoFrame = ttk.Frame(self, padding=(8, 2, 8, 4))
        eventoFrame.pack(side="top", fill="x")
        self.lblEvento = ttk.Label(eventoFrame, text="", font=("Segoe UI", 10, "italic"),
                                    wraplength=1050, justify="left")
        self.lblEvento.pack(anchor="w")

        # ---- Cuerpo: 3 columnas ----
        cuerpo = ttk.Frame(self, padding=8)
        cuerpo.pack(fill="both", expand=True)

        # Columna izquierda: barra de memoria
        colIzq = ttk.LabelFrame(cuerpo, text="Memoria (barra)", padding=6)
        colIzq.pack(side="left", fill="y", padx=(0, 6))
        self.canvasMem = tk.Canvas(colIzq, width=230, height=600,
                                    bg="white", highlightthickness=1,
                                    highlightbackground="#bbbbbb")
        self.canvasMem.pack()

        # Columna central: procesador + colas
        colCentro = ttk.Frame(cuerpo)
        colCentro.pack(side="left", fill="both", expand=True, padx=6)

        procFrame = ttk.LabelFrame(colCentro, text="Procesador", padding=6)
        procFrame.pack(fill="x")
        self.lblProc = ttk.Label(procFrame, text="", font=("Segoe UI", 11))
        self.lblProc.pack(anchor="w")

        colasFrame = ttk.LabelFrame(colCentro, text="Colas", padding=6)
        colasFrame.pack(fill="both", expand=True, pady=(6, 0))
        self.lblNuevos  = ttk.Label(colasFrame, text="", font=("Consolas", 10))
        self.lblListos  = ttk.Label(colasFrame, text="", font=("Consolas", 10))
        self.lblSusp    = ttk.Label(colasFrame, text="", font=("Consolas", 10))
        self.lblTerm    = ttk.Label(colasFrame, text="", font=("Consolas", 10))
        for lbl in (self.lblNuevos, self.lblListos, self.lblSusp, self.lblTerm):
            lbl.pack(anchor="w", pady=2)

        # Columna derecha: tabla de procesos
        colDer = ttk.LabelFrame(cuerpo, text="Procesos", padding=6)
        colDer.pack(side="left", fill="both", expand=True, padx=(6, 0))
        cols = ("ID", "Tam", "TA", "TI", "Estado", "Rest", "TR", "TE")
        self.tablaProc = ttk.Treeview(colDer, columns=cols, show="headings",
                                        height=15)
        anchos = {"ID": 45, "Tam": 55, "TA": 45, "TI": 45,
                  "Estado": 100, "Rest": 50, "TR": 50, "TE": 50}
        for c in cols:
            self.tablaProc.heading(c, text=c)
            self.tablaProc.column(c, width=anchos[c], anchor="center")
        self.tablaProc.pack(fill="both", expand=True)

        # Enlace teclado
        self.bind("<Left>",  lambda e: self._retroceder())
        self.bind("<Right>", lambda e: self._avanzar())
        self.bind("<Home>",  lambda e: self._alInicio())
        self.bind("<End>",   lambda e: self._alFin())

    # ------------------------------------------------------------------
    def _colorDeProceso(self, pid):
        return self.COLORES_PROCESO[(pid - 1) % len(self.COLORES_PROCESO)]

    def _actualizarVista(self):
        self.slider.set(self.idxActual)
        if self.idxActual == self.idxMax:
            # Pantalla de informe final
            self._dibujarInforme()
        else:
            snap = self.snapshots[self.idxActual]
            self.lblInstante.config(
                text=f"Snapshot {self.idxActual + 1}/{self.idxMax + 1}   |   t = {snap['t']}")
            self.lblEvento.config(text=f"Evento: {snap['evento']}")
            self._dibujarBarraMemoria(snap)
            self._dibujarProcesador(snap)
            self._dibujarColas(snap)
            self._dibujarTablaProcesos(snap)

    def _dibujarBarraMemoria(self, snap):
        c = self.canvasMem
        c.delete("all")
        ancho = 210
        xOff = 10
        altoTotal = 580
        yOff = 10
        totalKB = sum(p["tam"] for p in snap["memoria"])

        y = yOff
        for part in snap["memoria"]:
            h = max(16, int(altoTotal * part["tam"] / totalKB))
            ocupante = part["proceso"]
            if ocupante == "SO":
                color = self.COLOR_SO
                etiqueta = "SO"
                textColor = "white"
            elif ocupante == "LIBRE":
                color = self.COLOR_LIBRE
                etiqueta = "LIBRE"
                textColor = "#555555"
            else:
                color = self._colorDeProceso(int(ocupante))
                etiqueta = f"P{ocupante}"
                textColor = "black"
            c.create_rectangle(xOff, y, xOff + ancho, y + h,
                                fill=color, outline="#333333")
            c.create_text(xOff + ancho/2, y + h/2 - 7,
                          text=etiqueta, font=("Segoe UI", 10, "bold"),
                          fill=textColor)
            c.create_text(xOff + ancho/2, y + h/2 + 8,
                          text=f"{part['tam']}K (base {part['base']})",
                          font=("Segoe UI", 8), fill=textColor)
            y += h

    def _dibujarProcesador(self, snap):
        pid = snap["procesoEnEjecucion"]
        if pid is None:
            self.lblProc.config(text="CPU OCIOSA", foreground="#888888")
        else:
            proc = next(p for p in snap["procesos"] if p["id"] == pid)
            rest = proc.get("restante", "?")
            self.lblProc.config(
                text=f"Ejecutando P{pid}  (restante={rest}, TI={proc['TI']})",
                foreground="#1565c0")

    def _dibujarColas(self, snap):
        def fmt(lst):
            return "[" + ", ".join(f"P{i}" for i in lst) + "]" if lst else "(vacía)"
        self.lblNuevos.config(text=f"Nuevos            : {fmt(snap['colaNuevos'])}")
        self.lblListos.config(text=f"Listos            : {fmt(snap['colaListos'])}")
        self.lblSusp  .config(text=f"Listos/Suspendidos: {fmt(snap['colaListosYSusp'])}")
        self.lblTerm  .config(text=f"Terminados        : {fmt(snap['colaTerminados'])}")

    def _estadoDeProceso(self, proceso, snap):
        pid = proceso["id"]
        if pid == snap["procesoEnEjecucion"]:
            return "EJECUCION"
        if pid in snap["colaListos"]:
            return "LISTO"
        if pid in snap["colaListosYSusp"]:
            return "LISTO/SUSP"
        if pid in snap["colaTerminados"]:
            return "TERMINADO"
        return "NUEVO"

    def _dibujarTablaProcesos(self, snap):
        for item in self.tablaProc.get_children():
            self.tablaProc.delete(item)
        for p in snap["procesos"]:
            estado = self._estadoDeProceso(p, snap)
            rest = p.get("restante", "-") if estado != "NUEVO" else "-"
            tr = p.get("TR", "-")
            te = p.get("TE", "-")
            self.tablaProc.insert("", "end", values=(
                f"P{p['id']}", p["tam"], p["TA"], p["TI"],
                estado, rest, tr, te
            ))

    def _dibujarInforme(self):
        self.lblInstante.config(text=f"INFORME FINAL (último instante navegable)")
        self.lblEvento.config(
            text=f"Simulación finalizada en t = {self.informe['tiempoTotal']}")

        # Barra de memoria final
        if self.snapshots:
            self._dibujarBarraMemoria(self.snapshots[-1])

        # Procesador / colas: lo final
        self.lblProc.config(text="— (fin de simulación) —", foreground="#444444")
        self.lblNuevos.config(text="Procesos terminados:")
        self.lblListos.config(
            text=f"  TR promedio = {self.informe['promedioTR']:.2f}")
        self.lblSusp.config(
            text=f"  TE promedio = {self.informe['promedioTE']:.2f}")
        self.lblTerm.config(
            text=f"  Rendimiento = {self.informe['rendimiento']:.3f} proc/u.t.")

        # Tabla: TR/TE de todos los terminados
        for item in self.tablaProc.get_children():
            self.tablaProc.delete(item)
        for p in sorted(self.informe["terminados"], key=lambda x: x["id"]):
            self.tablaProc.insert("", "end", values=(
                f"P{p['id']}", p["tam"], p["TA"], p["TI"],
                "TERMINADO", "0", p.get("TR", "-"), p.get("TE", "-")
            ))
        for p in self.informe["noEjecutados"]:
            self.tablaProc.insert("", "end", values=(
                f"P{p['id']}", p["tam"], p["TA"], p["TI"],
                "NO EJECUTÓ", "-", "-", "-"
            ))

    # ------------------------------------------------------------------
    def _alInicio(self):
        self.idxActual = 0
        self._actualizarVista()

    def _alFin(self):
        self.idxActual = self.idxMax
        self._actualizarVista()

    def _avanzar(self):
        if self.idxActual < self.idxMax:
            self.idxActual += 1
            self._actualizarVista()

    def _retroceder(self):
        if self.idxActual > 0:
            self.idxActual -= 1
            self._actualizarVista()

    def _alSlider(self, valor):
        nuevo = int(float(valor))
        if nuevo != self.idxActual:
            self.idxActual = nuevo
            self._actualizarVista()

    def _volverAlMenu(self):
        """Cierra la ventana de simulación; el menú principal queda visible."""
        self.destroy()


# ======================================================================
# Ventana de carga manual (grilla editable)
# ======================================================================
class VentanaCargaManual(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Cargar procesos manualmente")
        self.geometry("520x480")
        self.entries = []  # lista de tuplas (eId, eTA, eTI, eTam)

        frameTop = ttk.Frame(self, padding=8)
        frameTop.pack(fill="x")
        ttk.Label(frameTop,
                  text="Cargá hasta 10 procesos. ID: número o 'P1'. "
                       "Dejá filas vacías si no las usás.",
                  wraplength=500, foreground="#444444").pack(anchor="w")

        # Encabezado
        header = ttk.Frame(self, padding=(8, 4))
        header.pack(fill="x")
        for i, texto in enumerate(("#", "Proceso", "TA", "TI", "Tamaño")):
            ttk.Label(header, text=texto,
                      font=("Segoe UI", 10, "bold"), width=10,
                      anchor="center").grid(row=0, column=i, padx=2)

        # Grilla de 10 filas
        gridFrame = ttk.Frame(self, padding=(8, 2))
        gridFrame.pack(fill="x")
        for n in range(10):
            ttk.Label(gridFrame, text=str(n + 1), width=10,
                      anchor="center").grid(row=n, column=0, padx=2, pady=1)
            eId  = ttk.Entry(gridFrame, width=10, justify="center")
            eTA  = ttk.Entry(gridFrame, width=10, justify="center")
            eTI  = ttk.Entry(gridFrame, width=10, justify="center")
            eTam = ttk.Entry(gridFrame, width=10, justify="center")
            eId .grid(row=n, column=1, padx=2, pady=1)
            eTA .grid(row=n, column=2, padx=2, pady=1)
            eTI .grid(row=n, column=3, padx=2, pady=1)
            eTam.grid(row=n, column=4, padx=2, pady=1)
            # Pre-rellenamos el ID con "P1", "P2"... para guiar
            eId.insert(0, f"P{n+1}")
            self.entries.append((eId, eTA, eTI, eTam))

        # Botones
        botones = ttk.Frame(self, padding=8)
        botones.pack(fill="x")
        ttk.Button(botones, text="Limpiar todo",
                   command=self._limpiar).pack(side="left")
        ttk.Button(botones, text="Validar y simular",
                   command=self._validarYSimular).pack(side="right")

    def _limpiar(self):
        for i, (eId, eTA, eTI, eTam) in enumerate(self.entries):
            eId.delete(0, "end")
            eId.insert(0, f"P{i+1}")
            eTA.delete(0, "end")
            eTI.delete(0, "end")
            eTam.delete(0, "end")

    def _validarYSimular(self):
        procesos = []
        for nro, (eId, eTA, eTI, eTam) in enumerate(self.entries, start=1):
            vId, vTA, vTI, vTam = (e.get().strip() for e in (eId, eTA, eTI, eTam))
            if not any((vTA, vTI, vTam)):
                continue  # fila vacía — se ignora
            if not all((vTA, vTI, vTam)):
                messagebox.showerror(
                    "Fila incompleta",
                    f"Fila {nro}: completá las 4 columnas o dejá la fila vacía.",
                    parent=self)
                return
            try:
                id_ = int(vId.lstrip("Pp")) if vId else nro
                ta  = int(vTA)
                ti  = int(vTI)
                tam = int(vTam)
            except ValueError:
                messagebox.showerror(
                    "Valores no numéricos",
                    f"Fila {nro}: los valores deben ser enteros. "
                    f"Proceso puede ser 'P1' o '1'.",
                    parent=self)
                return
            if tam <= 0 or ti <= 0 or ta < 0 or id_ < 0:
                messagebox.showerror(
                    "Valores fuera de rango",
                    f"Fila {nro}: se requiere Proceso ≥ 0, TA ≥ 0, "
                    f"TI > 0, Tamaño > 0.",
                    parent=self)
                return
            procesos.append({"id": id_, "tam": tam, "TA": ta, "TI": ti})

        if not procesos:
            messagebox.showwarning(
                "Sin procesos", "Cargá al menos un proceso.", parent=self)
            return
        if len(procesos) > 10:
            messagebox.showerror(
                "Demasiados procesos",
                f"Hay {len(procesos)} procesos; el máximo es 10.", parent=self)
            return

        # IDs duplicados?
        ids = [p["id"] for p in procesos]
        if len(set(ids)) != len(ids):
            messagebox.showerror(
                "IDs duplicados",
                "Hay procesos con el mismo ID. Deben ser únicos.", parent=self)
            return

        self.destroy()
        VentanaSimulacion(self.master, procesos,
                          titulo="Simulación (carga manual)")


# ======================================================================
# Ventana principal (menú de 4 opciones)
# ======================================================================
class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador SO 2026 — UTN Resistencia")
        self.geometry("460x380")
        self.resizable(False, False)

        ttk.Label(self, text="SIMULADOR DE MEMORIA 2026",
                  font=("Segoe UI", 14, "bold")).pack(pady=(20, 4))
        ttk.Label(self, text="MVT + Best-Fit + SRTF",
                  font=("Segoe UI", 10), foreground="#666666").pack(pady=(0, 20))

        botones = ttk.Frame(self, padding=20)
        botones.pack()

        ttk.Button(botones, text="1  —  Iniciar simulación precargada",
                   width=42, command=self._opcion1).pack(pady=4)
        ttk.Button(botones, text="2  —  Cargar procesos desde .csv",
                   width=42, command=self._opcion2).pack(pady=4)
        ttk.Button(botones, text="3  —  Cargar procesos manualmente",
                   width=42, command=self._opcion3).pack(pady=4)
        ttk.Button(botones, text="4  —  Información del grupo",
                   width=42, command=self._opcion4).pack(pady=4)

        ttk.Button(self, text="Salir",
                   command=self.destroy).pack(side="bottom", pady=14)

    def _opcion1(self):
        VentanaSimulacion(self, PROCESOS_DEMO,
                          titulo="Simulación precargada (10 procesos)")

    def _opcion2(self):
        ruta = filedialog.askopenfilename(
            parent=self, title="Seleccioná el archivo .csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not ruta:
            return
        procesos, error = parsearCSV(ruta)
        if error:
            messagebox.showerror("Error al leer el CSV", error, parent=self)
            return
        VentanaSimulacion(self, procesos,
                          titulo=f"Simulación — {Path(ruta).name}")

    def _opcion3(self):
        VentanaCargaManual(self)

    def _opcion4(self):
        info = (
            "COMISION 2.2 — EQUIPO 3\n\n"
            "Aranda Galissier Agustina Milagros\n"
            "Dali, Tania Yazmin\n"
            "Guillen Alexis de Jesus\n"
            "Lopez Yaccuzzi, Lourdes Anali\n"
            "Maciel, Julieta Andrea\n"
            "Robles Francisco\n"
            "Vargas Valentina"
        )
        messagebox.showinfo("Información del grupo", info, parent=self)


if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()
