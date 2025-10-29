import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_NAME = "municipalidad.db"

class DatabaseManager:
    @staticmethod
    def connect():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_tables():
        with DatabaseManager.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios_registrados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    direccion TEXT,
                    numero_casa TEXT,
                    dpi TEXT,
                    nit TEXT,
                    servicio_agua TEXT,
                    contador TEXT
                );
            """)
            conn.commit()

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

#usuarios predeterminados
def inicializar_usuarios():
    usuarios = [
        (Administrador, "123"),
        (LectorAgua, "456"),
        (Cocodes, "789")
    ]
    for clase, contrasena in usuarios:
        if not clase.verificar_usuario(contrasena):
            clase(clase.__name__, contrasena).guardar()

class Administrador(Usuario):
    pass

class LectorAgua(Usuario):
    pass


class Cocodes(Usuario):
    pass

class Graficos:
    def __init__(self, ventana):
        self.ventana = ventana
        DatabaseManager.init_tables()
        self.crear_login()


    def crear_login(self):

        self.ventana.title("Panel de Administrador - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        for widget in self.ventana.winfo_children():
            widget.destroy()
            try:
                self.ventana.state('zoomed')
            except:
                pass

        self.ventana.title("SAN FRANCISCO LA UNIÓN")
        self.ventana.geometry("1100x650")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg="#F6F6F8")

        self.bg_photo = tk.PhotoImage(file="fondosss.png")
        bg_label = tk.Label(self.ventana, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        style = ttk.Style()
        style.theme_use("calm")
        style.configure("TNotebook", background="#F6F6F8", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=[12, 8])
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TEntry", padding=6)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=24)


        header = tk.Frame(self.ventana, bg="#E9EEF6", height=110)
        header.pack(fill="x")
        tk.Label(header, text="SAN FRANCISCO LA UNIÓN", font=("Segoe UI", 28, "bold"),
                 bg="#E9EEF6", fg="#2D3A4A").place(relx=0.5, rely=0.45, anchor="center")

        card = tk.Frame(self.ventana, bg="white", bd=0)
        card.place(relx=0.5, rely=0.58, anchor="center")

        tk.Label(card, text="Iniciar sesión", font=("Segoe UI", 16, "bold"),
                 bg="white", fg="#2D3A4A").pack(pady=(12, 6))

        inner = tk.Frame(card, bg="white")
        inner.pack(padx=24, pady=12)

        tk.Label(inner, text="Usuario", font=("Segoe UI", 11),
                 bg="white", fg="#505050").grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.tipo_usuario = tk.StringVar()
        opciones = ["Administrador", "LectorAgua", "Cocodes"]
        combo = ttk.Combobox(inner, textvariable=self.tipo_usuario, values=opciones,
                             state="readonly", width=34, font=("Segoe UI", 10))
        combo.set("Selecciona un usuario")
        combo.grid(row=1, column=0, pady=(0, 8))

        tk.Label(inner, text="Contraseña", font=("Segoe UI", 11),
                 bg="white", fg="#505050").grid(row=2, column=0, sticky="w", pady=(6, 4))

        self.entry_pass = ttk.Entry(inner, show="*", width=36)
        self.entry_pass.grid(row=3, column=0)

        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=14)

        iniciar_btn = ttk.Button(btn_frame, text="Iniciar Sesión", command=self.verificar_login)
        iniciar_btn.grid(row=0, column=1, padx=6)

        salir_btn = ttk.Button(btn_frame, text="Salir del programa", command=self._confirm_quit)
        salir_btn.grid(row=0, column=0, padx=6)

        footer = tk.Frame(self.ventana, bg="#E9EEF6", height=10)
        footer.pack(fill="x", side="bottom")

    def _confirm_quit(self):
        if messagebox.askyesno("Salir", "¿Deseas salir del programa?"):
            self.ventana.quit()

    def verificar_login(self):
        tipo = self.tipo_usuario.get()
        contra = self.entry_pass.get()

        if tipo == "Selecciona un usuario" or not tipo:
            messagebox.showwarning("Atención", "Debes seleccionar un tipo de usuario.")
            return
        if not contra:
            messagebox.showwarning("Atención", "Debes ingresar una contraseña.")
            return

        clases = {"Administrador": Administrador, "LectorAgua": LectorAgua, "Cocodes": Cocodes}
        clase_usuario = clases.get(tipo)

        if clase_usuario and clase_usuario.verificar_usuario(contra):
            self.mostrar_interfaz_usuario(tipo)
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

    def mostrar_interfaz_usuario(self, tipo):
        for widget in self.ventana.winfo_children():
            widget.destroy()

        if tipo == "Administrador":
            AdminPanel(self.ventana, self)
        else:
            # mantener estilo no-admin
            frame = tk.Frame(self.ventana, bg="#F6F6F8")
            frame.pack(fill="both", expand=True)
            tk.Label(frame, text=f"Panel de {tipo}", font=("Segoe UI", 20, "bold"), bg="#F6F6F8").pack(pady=40)
            ttk.Button(frame, text="Cerrar sesión", command=self.crear_login).pack(pady=12)

class AdminPanel:
    def __init__(self, ventana, app):
        self.ventana = ventana
        self.app = app
        self.selected_user_id = None
        self.crear_panel_admin()

    def crear_panel_admin(self):
        self.ventana.title("Panel de Administrador - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass







    def crear_panel_admin(self):

        self.menu = tk.Frame(self.ventana, bg="#D3C7A1", width=200, height=500)
        self.menu.pack(side="left", fill="y")

        tk.Label(self.menu, text="Administrador", bg="#D3C7A1",
                 font=("Arial", 12, "bold")).pack(pady=10)

        botones = [
            ("Registrar usuarios", self.mostrar_registro_usuario),
            ("Cobro de boleto de ornato", self.mostrar_opcion_placeholder),
            ("Cobro de agua", self.mostrar_opcion_placeholder),
            ("Cobro de multas", self.mostrar_opcion_placeholder)
        ]

        for texto, comando in botones:
            tk.Button(self.menu, text=texto, bg="#C1B68F", width=25,
                      command=comando).pack(pady=5)

        tk.Button(self.menu, text="Cerrar sesión", bg="#B09E7E",
                  command=self.cerrar_sesion).pack(side="bottom", pady=20)


        self.contenido = tk.Frame(self.ventana, bg="#D3C7A1")
        self.contenido.pack(side="right", fill="both", expand=True)

        self.mostrar_registro_usuario()

    def mostrar_opcion_placeholder(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()
        tk.Label(self.contenido, text="Funcionalidad en construcción...",
                 font=("Arial", 14), bg="#D3C7A1").pack(pady=50)

    def mostrar_registro_usuario(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

        tk.Label(self.contenido, text="Registro de usuario",
                 font=("Arial", 16, "bold"), bg="#D3C7A1").pack(pady=10)

        frame = tk.Frame(self.contenido, bg="#D3C7A1")
        frame.pack(pady=10)

        campos = ["Nombre", "Dirección", "Número de casa", "DPI", "NIT", "Solicitar servicio de agua"]
        self.entries = {}

        for campo in campos:
            tk.Entry(frame, width=30)
            label = tk.Label(frame, text=campo, bg="#D3C7A1", anchor="w")
            label.pack(pady=2)
            entry = tk.Entry(frame, width=40)
            entry.pack(pady=2)
            self.entries[campo] = entry

        tk.Label(frame, text="Contador", bg="#D3C7A1", anchor="w").pack(pady=2)
        contador_cb = ttk.Combobox(frame, values=["Sí", "No"], width=37)
        contador_cb.pack(pady=2)
        self.entries["Contador"] = contador_cb

        botones_frame = tk.Frame(frame, bg="#D3C7A1")
        botones_frame.pack(pady=15)

        tk.Button(botones_frame, text="Limpiar", bg="#4a4a4a", fg="white",
                  command=self.limpiar_campos).pack(side="left", padx=10)
        tk.Button(botones_frame, text="Guardar", bg="#2e2e2e", fg="white",
                  command=self.guardar_registro).pack(side="left", padx=10)

    def limpiar_campos(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Combobox):
                entry.set('')
            else:
                entry.delete(0, tk.END)

    def guardar_registro(self):
        datos = {campo: entry.get() for campo, entry in self.entries.items()}

        with DatabaseManager.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios_registrados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    direccion TEXT,
                    numero_casa TEXT,
                    dpi TEXT,
                    nit TEXT,
                    servicio_agua TEXT,
                    contador TEXT
                );
            """)
            conn.execute("""
                INSERT INTO usuarios_registrados 
                (nombre, direccion, numero_casa, dpi, nit, servicio_agua, contador)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datos["Nombre"], datos["Dirección"], datos["Número de casa"],
                datos["DPI"], datos["NIT"], datos["Solicitar servicio de agua"],
                datos["Contador"]
            ))
            conn.commit()

        messagebox.showinfo("Registro guardado", "El usuario ha sido registrado correctamente.")
        self.limpiar_campos()

    def cerrar_sesion(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        self.app.crear_login()

#programa principal
if __name__ == "__main__":
    inicializar_usuarios()
    ventana = tk.Tk()
    grafico = Graficos(ventana)
    ventana.mainloop()