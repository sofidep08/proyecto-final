import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date

DB_NAME = "municipalidad.db"

class DatabaseManager:
    @staticmethod
    def connect():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def setup():
        with DatabaseManager.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credenciales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_usuario TEXT NOT NULL,
                contrasena TEXT NOT NULL
            );
        """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                dpi TEXT,
                direccion TEXT,
                numero_casa TEXT,
                tipo TEXT NOT NULL CHECK(tipo IN ('fijo','contador')),
                total_mes REAL DEFAULT 12.0,      -- valor mensual para agua fija
                ultimo_pago TEXT,                -- fecha del último pago (YYYY-MM-DD)
                mora REAL DEFAULT 0.0
            );
        """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lecturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    consumo REAL NOT NULL,
                    total_pagar REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    pagado INTEGER DEFAULT 0,
                    fecha_pago TEXT,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
                );
            """)
            conn.commit()

def inicializar_credenciales():
    with DatabaseManager.connect() as conn:
        cur = conn.execute("SELECT COUNT(*) AS c FROM credenciales").fetchone()
        if cur ["c"] == 0:
            conn.execute("INSERT INTO credenciales (tipo_usuario, ocntrasena) VALUES (?, ?)", ("Administrador", "admin123"))
            conn.execute("INSERT INTO credenciales (tipo_usuario, ocntrasena) VALUES (?, ?)", ("LectorAgua", "lector456"))
            conn.execute("INSERT INTO credenciales (tipo_usuario, ocntrasena) VALUES (?, ?)", ("Cocodes","cocode789"))
            conn.commit()

def verificar_credencial(tipo, contrasena):
    with DatabaseManager.connect() as conn:
        cur = conn.execute("SELECT * FROM credenciales WHERE tipo_usuario=? AND contrasena=?", (tipo, contrasena))
        return cur.fetchone() is not None

def meses_transcurridos(fecha_str):
    if not fecha_str:
        return 0
    try:
        f = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        return 0
    hoy = datetime.today()
    return (hoy.year - f.year) * 12 + (hoy.month - f.month)

def calcular_mora_fijo(cliente_row):
    total_mes =cient_total_mes = float(cliente_row["total_mes"] or 12.0)
    ultimo = cliente_row["ultimo_pago"]
    meses = meses_transcurridos(ultimo)
    if meses <= 0:
        meses = 1
    mora = meses * 25.0
    total_deuda = meses * total_mes + mora
    return {
        "meses": meses,
        "mora": mora,
        "total_deuda": total_deuda
    }

def calcular_mora_lectura(lectura_row):
    fecha_lectura = lectura_row["fecha"]
    meses = meses_transcurridos(fecha_lectura)
    mora = max(0, meses) * 25.0
    total = float(lectura_row["total_pago"]) + mora
    return {"meses": meses, "mora": mora, "total": total}

class LoginApp:
    def __init__(self, root):
        self.root = root
        root.title("Municipalidad - Sistema de Agua")
        root.geometry("420x260")
        root.resizable(False, False)

        tk.Label(root, text="Sistema Municipal - Agua", font=("Arial", 14, "bold")).pack(pady=10)
        frame = tk.Frame(root)
        frame.pack(pady=5)

        tk.Label(frame, text="Tipo de usuario").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cb_tipo = ttk.Combobox(frame, values=["Administrador", "LectorAgua", "Cocodes"], state="readonly", width=25)
        self.cb_tipo.current(0)
        self.cb_tipo.grid(row=0, column=1, sticky="e", padx=5, pady=5)

        tk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_pass = ttk.Entry(frame, show="*", width=27)
        self.entry_pass.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(root, text="Iniciar Sesión", width=20, command=self.login).pack(pady=10)

    def login(self):
        tipo= self.cb_tipo.get()
        contra = self. entry_pass.get()
        if not tipo or not contra:
            messagebox.showwarning("Atención", "Ingrese tipo de usuario y contraseña.")
            return
        if verificar_credencial(tipo, contra):
            self.root.destroy()
            if tipo == "Administrador":
                root = tk.Tk()
                adminApp(root)
                root.mainloop()
            elif tipo == "LectorAgua":
                root = tk.Tk()
                LectorApp(root)
                root.mainloop()
            else:
                root = tk.Tk()
                tk.Label(root, text="Panel Cocodes (sin funionalidades)", padx=20, pady=20).pack()
                tk.Button(root, text="Cerrar", command=root.destroy).pack(pady=10)
                root.mainloop()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas.")

class AdminApp:
    def __init__(self, root):
        self.root = root
        root.title("Administrador - Municipalidad")
        root.geometry("900x600")
        root.resizable(True, True)

        # Left menu
        menu = tk.Frame(root, width=220, bg="#D3C7A1")
        menu.pack(side="left", fill="y")
        tk.Label(menu, text="Administrador", bg="#D3C7A1", font=("Arial", 12, "bold")).pack(pady=12)

        tk.Button(menu, text="Registrar Cliente", width=22, command=self.pantalla_registrar).pack(pady=8)
        tk.Button(menu, text="Cobro de Agua", width=22, command=self.pantalla_cobro).pack(pady=8)
        tk.Button(menu, text="Ver Clientes", width=22, command=self.pantalla_listar_clientes).pack(pady=8)
        tk.Button(menu, text="Cerrar sesión", width=22, command=self.cerrar).pack(side="bottom", pady=20)

        # Main content
        self.content = tk.Frame(root, bg="#EFEFEF")
        self.content.pack(side="right", expand=True, fill="both")

        self.pantalla_registrar()

    def limpiar_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def pantalla_registrar(self):
        self.limpiar_content()
        tk.Label(self.content, text="Registrar Cliente", font=("Arial", 12, "bold"), bg="#EFEFEF").pack(pady=10)

        frm = tk.Frame(self.content, bg="#EFEFEF")
        frm.pack(pady=5)
        tk.Label(frm, text="Nombre: ", bg="#EFEFEF").grid(row=0, column=0, sticky="e")
        e_nombre = ttk.Entry(frm, width=40);
        e_nombre.grid(row=0, column=1, pady=4)

        tk.Label(frm, text="DPI: ", bg="#EFEFEF").grid(row=1, column=0, sticky="e")
        e_dpi = ttk.Entry(frm, width=40);
        e_dpi.grid(row=1, column=1, pady=4)

        tk.Label(frm, text="Dirección: ", bg="#EFEFEF").grid(row=2, column=0, sticky="e")
        e_direccion = ttk.Entry(frm, width=40);
        e_direccion.grid(row=2, column=1, pady=4)

        tk.Label(frm, text="Número de casa: ", bg="#EFEFEF").grid(row=3, column=0, sticky="e")
        e_casa = ttk.Entry(frm, width=40);
        e_casa.grid(row=3, column=1, pady=4)

        tk.Label(frm, text="Tipo de servicio: ", bg="#EFEFEF").grid(row=4, column=0, sticky="e")
        cb_tipo = ttk.Combobox(frm, values=["fijo", "contador"], width=37, state="readonly");
        cb_tipo.grid(row=4, column=1, pady=4)
        cb_tipo.current(0)


def menu_principal():
    while True:
        print("\n---PANTALLA DE INICIO---")
        print("1. Iniciar sesión")
        print("2. Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            seleccionar_usuario()
        elif opcion == "2":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción no válida. Intente de nuevo.")

def seleccionar_usuario():
    print("\n---USUARIOS---")
    print("1. Administrador")
    print("2. Lector de contador de agua")
    print("3. Cocodes")

    opcion = input("Seleccione el tipo de usuario:")

    if opcion == "1":
        iniciar_sesion("Administrar", "admin", "1234")
    elif opcion == "2":
        iniciar_sesion("Lector de contador de agua","lector","5678")
    elif opcion == "3":
        iniciar_sesion("Cocodes","cocode","0000")
    elif opcion == "4":
        return
    else:
        print("Opcion no válida. Intente de nuevo.")

def iniciar_sesion(rol, usuario_correcto, contraseña_correcta):
    print(f"\n---Inicio de sesión ({rol})---")
    usuario = input("Ingrese su nombre de usuario: ")
    contraseña = input("Ingrese su contraseña: ")

    if usuario  == usuario_correcto and contraseña == contraseña_correcta:
        print(f"\n Bienvenido, {rol} ({usuario})")
        menu_rol(rol)
    else:
        print("\n Usario o contraseña incorrectos.")

def menu_rol(rol):
    print(f"\n---MENÚ DE {rol.upper()}---")
    if rol == "Administrar":
        print("1. Gestionar pagos")
    elif rol == "Lector de contador de agua":
        print("1. Ingresar lectura del contador")
    elif rol == "Cocodes":
        print("1. Registrar multa")
    input("\nPresione ENTER para regresar al inicio...")

def menu_lector_contador():
    empleados = Empleados()

    print("\n---INICIO DE SESIÓN DEL LECTOR DE CONTADOR---")
    usuario = input("Usuario: ")
    contrasenia = input("Contraseña: ")

    if empleados.validar_login(usuario, contrasenia):
        print(f"\n Bienvenido, {empleados.empleados[usuario]['Nombre']}")
    else:
        print("Usuario o contraseña incorrectos. Intente de nuevo.")
        return

    while True:
        print("\n---LECTOR DE CONTADOR DE AGUA---")
        print("1. Registrar lectura")
        print("2. Ver historial")
        print("3. Regresar")

        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            registrar_lectura()
        elif opcion == "2":
            ver_historial()
        elif opcion == "3":
            break
        else:
            print("Opción no válida.Intente de nuevo.")

def registrar_lectura():
    print("\n---REGISTRO DE LECTURA ---")
    print("Direcciones disponibles:")
    direcciones = [
        "Cantón Tzanjuyup",
        "Cantón Chuistancia",
        "Cantón Palá",
        "Cantón Paxán",
        "Aldea Xeaj"
    ]
    for i,d in enumerate(direcciones, start=1):
        print(f"{i}. {d}")

    try:
        opcion = int(input("Seleccione la dirección (1-5): "))
        direccion = direcciones[opcion-1]
    except ValueError:
        print("Opción inválida.")
        return

