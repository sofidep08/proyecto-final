import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_NAME = "municipalidad.db"

class Usuario:
    def __init__(self, tipo_usuario, contrasena):
        self.tipo_usuario = tipo_usuario
        self.contrasena = contrasena

    @staticmethod
    def _conn():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                clave INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_usuario TEXT NOT NULL,
                contrasena TEXT NOT NULL
            );
        """)
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO usuarios (tipo_usuario, contrasena) VALUES (?, ?)",
                (self.tipo_usuario, self.contrasena)
            )
            conn.commit()

    @staticmethod
    def verificar_usuario(tipo_usuario, contrasena):
        with Usuario._conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM usuarios WHERE tipo_usuario = ? AND contrasena = ?",
                (tipo_usuario, contrasena)
            )
            return cursor.fetchone() is not None

#usuarios predeterminados
def inicializar_usuarios():
    usuarios_base = [
        ("Administrador", "123"),
        ("Lector de contador de agua", "456"),
        ("Cocodes", "789")
    ]
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                clave INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_usuario TEXT NOT NULL,
                contrasena TEXT NOT NULL
            );
        """)
        for tipo, contrasena in usuarios_base:
            cursor = conn.execute("SELECT * FROM usuarios WHERE tipo_usuario = ?", (tipo,))
            if cursor.fetchone() is None:
                conn.execute(
                    "INSERT INTO usuarios (tipo_usuario, contrasena) VALUES (?, ?)",
                    (tipo, contrasena)
                )
        conn.commit()


class Graficos:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("SAN FRANCISCO LA UNIÓN")
        self.ventana.geometry("800x500")
        self.ventana.resizable(False, False)

        #fondo
        self.bg_photo = tk.PhotoImage(file="fondoss.png")
        bg_label = tk.Label(ventana, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # titulo
        title_label = tk.Label(ventana, text="SAN FRANCISCO LA UNIÓN",
                               font=("Arial", 20, "bold"),
                               bg="#000000", fg="white")
        title_label.place(relx=0.5, rely=0.1, anchor="center")

        #marco
        frame = tk.Frame(ventana, bg="#000000", bd=0)
        frame.place(relx=0.5, rely=0.55, anchor="center")

        # menu de opcioenes de usuario
        tk.Label(frame, text="Usuario", font=("Arial", 10),
                 bg="#000000", fg="white").pack(pady=(0, 5))

        self.tipo_usuario = tk.StringVar()
        opciones = ["Administrador", "Lector de contador de agua", "Cocodes"]

        combo = ttk.Combobox(frame, textvariable=self.tipo_usuario,
                             values=opciones, state="readonly", width=25)
        combo.set("Selecciona un usuario")
        combo.pack(pady=5)

        #contraseña
        tk.Label(frame, text="Contraseña", font=("Arial", 10),
                 bg="#000000", fg="white").pack(pady=(10, 5))

        self.entry_pass = ttk.Entry(frame, show="*", width=25)
        self.entry_pass.pack(pady=5)

    # boton de inicio de sesion
        login_btn = tk.Button(frame, text="Iniciar Sesión",
                              font=("Arial", 10, "bold"),
                              bg="#2e2e2e", fg="white", width=20,
                              command=self.verificar_login)
        login_btn.pack(pady=15)

    # linea decorativa
        tk.Frame(ventana, bg="#00aaff", height=3).pack(side="bottom", fill="x")


    def verificar_login(self):
        tipo = self.tipo_usuario.get()
        contra = self.entry_pass.get()

        if tipo == "Selecciona un usuario":
            messagebox.showwarning("Atención", "Debes seleccionar un tipo de usuario.")
            return
        if not contra:
            messagebox.showwarning("Atención", "Debes ingresar una contraseña.")
            return

        if Usuario.verificar_usuario(tipo, contra):
            pass
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

#programa principal
if __name__ == "__main__":
    inicializar_usuarios()
    ventana = tk.Tk()
    grafico = Graficos(ventana)
    ventana.mainloop()