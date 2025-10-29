import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = "municipalidad.db"

# ==============================
# MANEJO DE BASE DE DATOS
# ==============================
class DatabaseManager:
    @staticmethod
    def connect():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

# ==============================
# CLASES DE USUARIOS
# ==============================
class Usuario:
    def __init__(self, tipo_usuario, contrasena):
        self.tipo_usuario = tipo_usuario
        self.contrasena = contrasena
        self.tabla = self.__class__.__name__.lower()

    def guardar(self):
        with DatabaseManager.connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.tabla} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_usuario TEXT NOT NULL,
                    contrasena TEXT NOT NULL
                );
            """)
            conn.execute(
                f"INSERT INTO {self.tabla} (tipo_usuario, contrasena) VALUES (?, ?)",
                (self.tipo_usuario, self.contrasena)
            )
            conn.commit()

    @classmethod
    def verificar_usuario(cls, contrasena):
        with DatabaseManager.connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.__name__.lower()} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_usuario TEXT NOT NULL,
                    contrasena TEXT NOT NULL
                );
            """)
            cursor = conn.execute(
                f"SELECT * FROM {cls.__name__.lower()} WHERE contrasena = ?",
                (contrasena,)
            )
            return cursor.fetchone() is not None

# ==============================
# SUBCLASES DE USUARIOS
# ==============================
class Administrador(Usuario):
    pass

class LectorAgua(Usuario):
    @staticmethod
    def crear_tabla():
        with DatabaseManager.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agua_registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    direccion TEXT,
                    numero_casa TEXT,
                    consumo_galones REAL,
                    total_pagar REAL,
                    fecha TEXT
                );
            """)
            conn.commit()

    @staticmethod
    def insertar_registro(direccion, numero_casa, consumo_galones, fecha):
        if consumo_galones == "":
            consumo_galones = 0
        consumo = float(consumo_galones)
        total = consumo * 1  # Q1 por galón
        with DatabaseManager.connect() as conn:
            conn.execute("""
                INSERT INTO agua_registros (direccion, numero_casa, consumo_galones, total_pagar, fecha)
                VALUES (?, ?, ?, ?, ?)
            """, (direccion, numero_casa, consumo, total, fecha))
            conn.commit()

class Cocodes(Usuario):
    pass

# ==============================
# AGUA FIJA
# ==============================
class AguaFija:
    @staticmethod
    def crear_tabla():
        with DatabaseManager.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agua_fija (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    direccion TEXT,
                    numero_casa TEXT,
                    ultimo_pago TEXT,
                    total_mes REAL,
                    mora REAL,
                    pago_pendiente INTEGER
                );
            """)
            conn.commit()

    @staticmethod
    def agregar_usuario(direccion, numero_casa):
        with DatabaseManager.connect() as conn:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            conn.execute("""
                INSERT INTO agua_fija (direccion, numero_casa, ultimo_pago, total_mes, mora, pago_pendiente)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (direccion, numero_casa, fecha_actual, 12, 0, 0))
            conn.commit()

    @staticmethod
    def calcular_mora_y_pago():
        dias_cobro = [1, 3, 6]  # martes=1, jueves=3, domingo=6
        hoy = datetime.now()
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM agua_fija").fetchall()
            for r in rows:
                ultimo = datetime.strptime(r["ultimo_pago"], "%Y-%m-%d")
                meses_atraso = (hoy.year - ultimo.year) * 12 + (hoy.month - ultimo.month)
                mora = max(0, meses_atraso * 25)
                pago_pendiente = 1 if hoy.weekday() in dias_cobro else 0
                conn.execute("UPDATE agua_fija SET mora=?, pago_pendiente=? WHERE id=?", (mora, pago_pendiente, r["id"]))
            conn.commit()

# ==============================
# USUARIOS PREDETERMINADOS
# ==============================
def inicializar_usuarios():
    usuarios = [
        (Administrador, "123"),
        (LectorAgua, "456"),
        (Cocodes, "789")
    ]
    for clase, contrasena in usuarios:
        if not clase.verificar_usuario(contrasena):
            clase(clase.__name__, contrasena).guardar()
    AguaFija.crear_tabla()

# ==============================
# INTERFAZ GRÁFICA PRINCIPAL
# ==============================
class Graficos:
    def __init__(self, ventana):
        self.ventana = ventana
        self.crear_login()

    def crear_login(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()

        self.ventana.title("SAN FRANCISCO LA UNIÓN")
        self.ventana.geometry("800x500")
        self.ventana.resizable(False, False)
        self.ventana.config(bg="#000000")  # Fondo negro temporal

        title_label = tk.Label(self.ventana, text="SAN FRANCISCO LA UNIÓN",
                               font=("Arial", 20, "bold"),
                               bg="#000000", fg="white")
        title_label.place(relx=0.5, rely=0.1, anchor="center")

        frame = tk.Frame(self.ventana, bg="#000000", bd=0)
        frame.place(relx=0.5, rely=0.55, anchor="center")

        tk.Label(frame, text="Usuario", font=("Arial", 10),
                 bg="#000000", fg="white").pack(pady=(0, 5))

        self.tipo_usuario = tk.StringVar()
        opciones = ["Administrador", "LectorAgua", "Cocodes"]
        combo = ttk.Combobox(frame, textvariable=self.tipo_usuario,
                             values=opciones, state="readonly", width=25)
        combo.set("Selecciona un usuario")
        combo.pack(pady=5)

        tk.Label(frame, text="Contraseña", font=("Arial", 10),
                 bg="#000000", fg="white").pack(pady=(10, 5))

        self.entry_pass = ttk.Entry(frame, show="*", width=25)
        self.entry_pass.pack(pady=5)

        login_btn = tk.Button(frame, text="Iniciar Sesión",
                              font=("Arial", 10, "bold"),
                              bg="#2e2e2e", fg="white", width=20,
                              command=self.verificar_login)
        login_btn.pack(pady=15)

    def verificar_login(self):
        tipo = self.tipo_usuario.get()
        contra = self.entry_pass.get()

        if tipo == "Selecciona un usuario":
            messagebox.showwarning("Atención", "Debes seleccionar un tipo de usuario.")
            return
        if not contra:
            messagebox.showwarning("Atención", "Debes ingresar una contraseña.")
            return

        clases = {"Administrador": Administrador, "LectorAgua": LectorAgua, "Cocodes": Cocodes}
        clase_usuario = clases.get(tipo)

        if clase_usuario.verificar_usuario(contra):
            self.mostrar_interfaz_usuario(tipo)
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

    def mostrar_interfaz_usuario(self, tipo):
        for widget in self.ventana.winfo_children():
            widget.destroy()

        if tipo == "Administrador":
            AdminPanel(self.ventana, self)
        elif tipo == "LectorAgua":
            LectorPanel(self.ventana, self)
        elif tipo == "Cocodes":
            tk.Label(self.ventana, text="Panel de Cocodes", font=("Arial", 16)).pack()
            tk.Button(self.ventana, text="Cerrar sesión",
                      command=self.crear_login).pack(pady=20)

# ==============================
# PANEL DE ADMINISTRADOR
# ==============================
class AdminPanel:
    def __init__(self, ventana, app):
        self.ventana = ventana
        self.app = app
        self.crear_panel_admin()

    def crear_panel_admin(self):
        self.menu = tk.Frame(self.ventana, bg="#D3C7A1", width=200, height=500)
        self.menu.pack(side="left", fill="y")

        tk.Label(self.menu, text="Administrador", bg="#D3C7A1",
                 font=("Arial", 12, "bold")).pack(pady=10)

        botones = [
            ("Registrar usuarios", self.mostrar_registro_usuario),
            ("Cobro de agua con contador", self.mostrar_registro_agua),
            ("Cobro de agua fija", self.mostrar_agua_fija)
        ]

        for texto, comando in botones:
            tk.Button(self.menu, text=texto, bg="#C1B68F", width=25,
                      command=comando).pack(pady=5)

        tk.Button(self.menu, text="Cerrar sesión", bg="#B09E7E",
                  command=self.cerrar_sesion).pack(side="bottom", pady=20)

        self.contenido = tk.Frame(self.ventana, bg="#D3C7A1")
        self.contenido.pack(side="right", fill="both", expand=True)

        self.mostrar_registro_usuario()

    def mostrar_registro_usuario(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()
        tk.Label(self.contenido, text="Registro de usuario", font=("Arial", 14, "bold"), bg="#D3C7A1").pack(pady=10)

    def mostrar_registro_agua(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()
        tk.Label(self.contenido, text="Historial de agua", font=("Arial", 14, "bold"), bg="#D3C7A1").pack(pady=10)

        tree = ttk.Treeview(self.contenido, columns=("id", "direccion", "numero_casa", "consumo", "total", "fecha"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col.capitalize())
        tree.pack(expand=True, fill="both")

        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM agua_registros ORDER BY fecha DESC").fetchall()
            for r in rows:
                tree.insert("", "end", values=(r["id"], r["direccion"], r["numero_casa"], r["consumo_galones"], r["total_pagar"], r["fecha"]))

    def mostrar_agua_fija(self):
        AguaFija.calcular_mora_y_pago()
        for widget in self.contenido.winfo_children():
            widget.destroy()
        tk.Label(self.contenido, text="Agua fija", font=("Arial", 14, "bold"), bg="#D3C7A1").pack(pady=10)

        tree = ttk.Treeview(self.contenido, columns=("id", "direccion", "numero_casa", "ultimo_pago", "total_mes", "mora", "pago_pendiente"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col.capitalize())
        tree.pack(expand=True, fill="both")

        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM agua_fija ORDER BY ultimo_pago DESC").fetchall()
            for r in rows:
                iid = tree.insert("", "end", values=(r["id"], r["direccion"], r["numero_casa"], r["ultimo_pago"], r["total_mes"], r["mora"], r["pago_pendiente"]))
                if r["pago_pendiente"]:
                    tree.item(iid, tags=("pendiente",))
        tree.tag_configure("pendiente", background="#ffcccc")  # Resalta pagos pendientes

    def cerrar_sesion(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        self.app.crear_login()

# ==============================
# PANEL DEL LECTOR DE AGUA
# ==============================
class LectorPanel:
    def __init__(self, ventana, app):
        self.ventana = ventana
        self.app = app
        LectorAgua.crear_tabla()
        self.crear_panel_lector()

    def crear_panel_lector(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()

        self.ventana.title("Panel del Lector de Agua")
        self.ventana.config(bg="#D3C7A1")

        tk.Label(self.ventana, text="REGISTRO DE LECTURA DE AGUA", font=("Arial", 16, "bold"), bg="#D3C7A1").pack(pady=10)

        frame = tk.Frame(self.ventana, bg="#D3C7A1")
        frame.pack(pady=10)

        tk.Label(frame, text="Dirección:", bg="#D3C7A1").grid(row=0, column=0, sticky="e")
        self.direccion = ttk.Combobox(frame, values=["Cantón Tzanjuyup", "Cantón Chuistancia", "Cantón Pala", "Cantón Paxán", "Aldea Xeaj"], width=40, state="readonly")
        self.direccion.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Número de Casa:", bg="#D3C7A1").grid(row=1, column=0, sticky="e")
        self.numero_casa = tk.Entry(frame, width=43)
        self.numero_casa.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Consumo (galones):", bg="#D3C7A1").grid(row=2, column=0, sticky="e")
        self.consumo = tk.Entry(frame, width=43)
        self.consumo.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Fecha:", bg="#D3C7A1").grid(row=3, column=0, sticky="e")
        self.fecha = tk.Entry(frame, width=43)
        self.fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.fecha.grid(row=3, column=1, pady=5)

        tk.Button(self.ventana, text="Guardar registro", bg="#4a4a4a", fg="white",
                  command=self.guardar_registro).pack(pady=10)
        tk.Button(self.ventana, text="Regresar", bg="#B09E7E",
                  command=self.app.crear_login).pack(pady=5)

    def guardar_registro(self):
        direccion = self.direccion.get()
        casa = self.numero_casa.get()
        consumo = self.consumo.get()
        fecha = self.fecha.get()

        if not direccion or not casa or not fecha:
            messagebox.showwarning("Atención", "Todos los campos son obligatorios.")
            return

        LectorAgua.insertar_registro(direccion, casa, consumo, fecha)
        messagebox.showinfo("Éxito", "Registro de agua guardado correctamente.")
        self.consumo.delete(0, tk.END)

# ==============================
# PROGRAMA PRINCIPAL
# ==============================
if __name__ == "__main__":
    inicializar_usuarios()
    ventana = tk.Tk()
    grafico = Graficos(ventana)
    ventana.mainloop()
