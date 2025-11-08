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

