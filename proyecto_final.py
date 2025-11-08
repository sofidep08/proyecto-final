import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import os

PIL_AVAILABLE = False
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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

    @staticmethod
    def setup():
        with DatabaseManager.connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo_usuario TEXT NOT NULL,
                        contrasena TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        dpi TEXT NOT NULL UNIQUE,
                        direccion TEXT,
                        numero_casa TEXT,
                        tipo TEXT NOT NULL CHECK(tipo IN ('fijo','contador')),
                        total_mes REAL DEFAULT 12.0,
                        ultimo_pago TEXT,
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
                conn.execute("""
                        CREATE TABLE IF NOT EXISTS credenciales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo_usuario TEXT NOT NULL,
                        contrasena TEXT NOT NULL
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
            conn.execute(
                f"INSERT INTO {self.tabla} (tipo_usuario, contrasena) VALUES (?, ?)",
                (self.tipo_usuario, self.contrasena)
            )
            conn.commit()

    @classmethod
    def verificar_usuario(cls, contrasena):
        with DatabaseManager.connect() as conn:
            cursor = conn.execute(
            f"SELECT * FROM {cls.__name__.lower()} WHERE contrasena = ?",
    (contrasena,)
            )
            return cursor.fetchone() is not None

class Administrador(Usuario): pass
class LectorAgua(Usuario): pass
class Cocodes(Usuario): pass

def inicializar_credenciales():
    with DatabaseManager.connect() as conn:
        conn.execute("DELETE FROM credenciales")
        conn.executemany("""
            INSERT INTO credenciales (tipo_usuario, contrasena) VALUES (?, ?)
        """, [
            ("Administrador", "123"),
            ("LectorAgua", "456"),
            ("Cocodes", "789")
        ])
        conn.commit()

def verificar_credencial(tipo, contrasena):
    with DatabaseManager.connect() as conn:
        cur = conn.execute("SELECT * FROM credenciales WHERE tipo_usuario=? AND contrasena=?", (tipo, contrasena))
        return cur.fetchone() is not None

class LectorApp:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Panel del Lector de Agua")
        self.ventana.state('zoomed')

        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True)

        self.tab_lectura = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_lectura, text="Hacer Lectura")

        frm = ttk.Frame(self.tab_lectura, padding=20)
        frm.pack(pady=20)

        tk.Label(frm, text="Usuario (seleccione):").grid(row=0, column=0, sticky="e", padx=5, pady=6)
        self.cb_usuarios = ttk.Combobox(frm, width=45, state="readonly")
        self.cb_usuarios.grid(row=0, column=1, padx=5, pady=6)

        tk.Label(frm, text="Consumo (galones):").grid(row=1, column=0, sticky="e", padx=5, pady=6)
        self.e_consumo = ttk.Entry(frm, width=30)
        self.e_consumo.grid(row=1, column=1, padx=5, pady=6)

        tk.Label(frm, text="Fecha (YYYY-MM-DD):").grid(row=2, column=0, sticky="e", padx=5, pady=6)
        self.e_fecha = ttk.Entry(frm, width=30)
        self.e_fecha.grid(row=2, column=1, padx=5, pady=6)
        self.e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Button(root, text="Cargar usuarios", command=self.cargar_usuarios).pack(pady=6)
        ttk.Button(root, text="Guardar Lectura", command=self.guardar_lectura).pack(pady=6)
        ttk.Button(root, text="Cerrar sesión", command=self.root.destroy).pack(pady=10)

        self.cargar_usuarios()

        self.tab_ayuda = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ayuda, text="Ayuda")

        ttk.Label(self.tab_ayuda, text="Centro de ayuda del lector de agua", font=("Segoe UI", 16, "bold")).pack(pady=20)
        ayuda_texto = (
            "Aquí puedes registar las lecturas de los medidores.\n"
            "1. Ingresa el código del medidor.\n"
            "2. Escribe la lectura actual en galones.\n"
            "3. Pulsa 'Guardar Lectura' para almacenar el dato.\n"
            "Si tienes problemas, contacta al administrador del sistema."
        )
        ttk.Label(self.tab_ayuda, text=ayuda_texto, justify="left", font=("Segoe UI", 11)).pack(padx=20, pady=10)

        self.tab_salir = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_salir, text="Salir")
        ttk.Label(self.tab_salir, text="¿Deseas cerrar el panel del lector?", font=("Segoe UI", 14)).pack(pady=40)
        ttk.Button(self.tab_salir, text="Cerrar Sesión", command=self.cerrar_sesion).pack(pady=20)

    def cargar_usuarios(self):
        with DatabaseManager.connect() as conn:
            filas = conn.execute("SELECT id, nombre, numero_casa FROM clientes WHERE tipo='contador' ORDER BY nombre").fetchall()
            lista = [f"{f['id']} - {f['nombre']} (Casa {f['numero_casa']})" for f in filas]
        self.cb_usuarios['values'] = lista
        if lista:
            self.cb_usuarios.current(0)

    def guardar_lectura(self):
        seleccionado = slef.cb_usuarios.get()
        consumo = self.e_consumo.get().strip()
        fecha = self.e_fecha.get().strip()

        if not seleccionado or not consumo or not fecha:
            messagebox.showwarning("Atención", "Complete todos los campos.")
            return

        try:
            consumo_float = float(consumo)
            if consumo_float <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Consumo debe ser un número positivo.")
            return



    def cerrar_sesion(self):
        confirm = messagebox.askyesno("Confirmar", "¿Seguro que deseas cerrar sesión?")
        if confirm:
            self.ventana.destroy()
            import main
            main.Graficos(tk.Tk())

class Graficos:
    def __init__(self, ventana):
        self.ventana = ventana
        DatabaseManager.init_tables()
        DatabaseManager.setup()
        inicializar_credenciales()
        self.crear_login()

    def crear_login(self):
        self.ventana.title("Panel de Administrador - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        for widget in self.ventana.winfo_children():
            widget.destroy()

        self.ventana.title("SAN FRANCISCO LA UNIÓN")
        self.ventana.geometry("1100x650")
        self.ventana.resizable(False, False)

        self.main_frame = tk.Frame(self.ventana, bg="#F6F6F8")
        self.main_frame.pack(fill="both", expand=True)

        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        ruta_imagen = os.path.join(assets_dir, "images.jpg")

        loaded = False
        if os.path.exists(ruta_imagen):
            try:
                if PIL_AVAILABLE:
                    img = Image.open(ruta_imagen)
                    img = img.resize((1100, 650), Image.Resampling.LANCZOS)
                    self.bg_photo = ImageTk.PhotoImage(img)
                else:
                    self.bg_photo = tk.PhotoImage(file=ruta_imagen)

                bg_label = tk.Label(self.main_frame, image=self.bg_photo)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print(f"No se pudo cargar la imagen de fondo: {e}")
            else:
                print("No se encontró la imagen de fondo en:", ruta_imagen)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background="#F6F6F8", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=[12, 8])
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TEntry", padding=6)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=24)

        header = tk.Frame(self.main_frame, bg="#E9EEF6", height=110)
        header.pack(fill="x")
        tk.Label(header, text="SAN FRANCISCO LA UNIÓN", font=("Segoe UI", 28, "bold"),
                 bg="#E9EEF6", fg="#2D3A4A").place(relx=0.5, rely=0.45, anchor="center")

        card = tk.Frame(self.main_frame, bg="white", bd=0)
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

        if verificar_credencial(tipo, contra):
            messagebox.showinfo("Bienvenido", f"Inicio de sesión exitoso como {tipo}")
            self.mostrar_interfaz_usuario(tipo)  # 🔹 Aquí está la clave
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

    def mostrar_interfaz_usuario(self, tipo):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        if tipo == "Administrador":
            AdminPanel(self.ventana, self)
        elif tipo == "LectorAgua":
            lector_win = tk.Toplevel(self.ventana)
            LectorApp(lector_win)
        else:
            frame = tk.Frame(self.ventana, bg="#F6F6F8")
            frame.pack(fill="both", expand=True)
            tk.Label(frame, text=f"Panel de {tipo}", font=("Segoe UI", 20, "bold"), bg="#F6F6F8").pack(pady=40)
            ttk.Button(frame, text="Cerrar sesión", command=self.crear_login).pack(pady=12)

class AdminPanel:
    def __init__(self, ventana, app):
        self.ventana = ventana
        self.app = app
        self.selected_user_id = None
        self.cliente_seleccionado = None
        self.crear_panel_admin()

    def crear_panel_admin(self):
        self.ventana.title("Panel de Administrador - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        menu_bar = tk.Menu(self.ventana)
        self.ventana.config(menu=menu_bar)

        menu_usuarios = tk.Menu(menu_bar, tearoff=0)
        menu_usuarios.add_command(label="Administrar usuarios", command=self._abrir_panel_usuarios)
        menu_usuarios.add_command(label="Buscar", command=self._abrir_panel_usuarios)
        menu_bar.add_cascade(label="Usuarios", menu=menu_usuarios)

        menu_ornato = tk.Menu(menu_bar, tearoff=0)
        menu_ornato.add_command(label="Nuevo",
                                command=lambda: messagebox.showinfo("Boleta", "Funcionalidad en construcción"))
        menu_bar.add_cascade(label="Boleta de Ornato", menu=menu_ornato)

        menu_agua = tk.Menu(menu_bar, tearoff=0)
        menu_agua.add_command(label="Servicio de Agua", command=self._abrir_panel_agua)
        menu_bar.add_cascade(label="Servicio de Agua", menu=menu_agua)

        menu_multas = tk.Menu(menu_bar, tearoff=0)
        menu_multas.add_command(label="Multas",
                                command=lambda: messagebox.showinfo("Multas", "Funcionalidad en construcción"))
        menu_bar.add_cascade(label="Multas", menu=menu_multas)

        menu_ayuda = tk.Menu(menu_bar, tearoff=0)
        menu_ayuda.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Acerca de", "Sistema Municipal"))
        menu_bar.add_cascade(label="Ayuda", menu=menu_ayuda)

        menu_salir = tk.Menu(menu_bar, tearoff=0)
        menu_salir.add_command(label="Cerrar sesión", command=self.cerrar_sesion)
        menu_salir.add_command(label="Salir", command=self.ventana.quit)
        menu_bar.add_cascade(label="Salir", menu=menu_salir)

        self.content = tk.Frame(self.ventana, bg="#F2F5F9")
        self.content.pack(fill="both", expand=True)

        self._show_welcome()

    def _show_welcome(self):
        for w in self.content.winfo_children():
            w.destroy()
        tk.Label(self.content, text="Bienvenido al Panel de Administración",
                 font=("Segoe UI", 24, "bold"), bg="#F2F5F9", fg="#2D3A4A").pack(pady=60)
        tk.Label(self.content, text="Use el submenú para acceder a las opciones de administrador",
                 font=("Segoe UI", 12), bg="#F2F5F9", fg="#58606A").pack()

    def _abrir_panel_usuarios(self, agua=False):
        for w in self.content.winfo_children():
            w.destroy()

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        register_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(register_tab, text="Registrar")
        self._build_register_tab(register_tab)

        search_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(search_tab, text="Buscar")
        self._build_search_tab(search_tab)

        all_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(all_tab, text="Ver todos")
        self._build_all_tab(all_tab)

    def _build_register_tab(self, parent):
        pad = {"padx": 12, "pady": 6}
        form = tk.Frame(parent, bg="#FFFFFF")
        form.pack(padx=20, pady=20, anchor="n")

        labels = ["Nombre", "Dirección", "Número de casa", "DPI", "NIT", "Solicitar servicio de agua"]
        self._reg_entries = {}

        for i, lbl in enumerate(labels):
            tk.Label(form, text=lbl, font=("Segoe UI", 10), bg="#FFFFFF").grid(row=i, column=0, sticky="w", **pad)
            e = ttk.Entry(form, width=50)
            e.grid(row=i, column=1, **pad)
            self._reg_entries[lbl] = e

        tk.Label(form, text="Contador", font=("Segoe UI", 10), bg="#FFFFFF").grid(row=len(labels), column=0, sticky="w", **pad)
        contador_cb = ttk.Combobox(form, values=["Sí", "No"], width=47)
        contador_cb.grid(row=len(labels), column=1, **pad)
        self._reg_entries["Contador"] = contador_cb

        btn_frame = tk.Frame(form, bg="#FFFFFF")
        btn_frame.grid(row=len(labels)+1, column=0, columnspan=2, pady=14)
        ttk.Button(btn_frame, text="Limpiar", command=self._clear_register).grid(row=0, column=0, padx=8)
        ttk.Button(btn_frame, text="Guardar", command=self._save_register).grid(row=0, column=1, padx=8)

    def _clear_register(self):
        for e in self._reg_entries.values():
            try:
                e.delete(0, tk.END)
            except Exception:
                try:
                    e.set("")
                except Exception:
                    pass

    def _save_register(self):
        datos = {campo: widget.get() for campo, widget in self._reg_entries.items()}

        if not datos["Nombre"] or not datos["Número de casa"] or not datos["DPI"]:
            messagebox.showwarning("Validación", "Los campos Nombre, Número de casa y DPI son obligatorios.")
            return

        tipo_contador = "contador" if datos["Contador"] == "Sí" else "fijo"

        try:
            with DatabaseManager.connect() as conn:
                conn.execute("""
                    INSERT INTO clientes
                    (nombre, dpi, direccion, numero_casa, tipo, total_mes, ultimo_pago, mora)
                    VALUES (?, ?, ?, ?, ?, 12.0, NULL, 0.0)
                """, (
                    datos["Nombre"],
                    datos["DPI"],
                    datos["Dirección"],
                    datos["Número de casa"],
                    tipo_contador
                ))
                conn.commit()

            messagebox.showinfo("Éxito", "Usuario registrado correctamente ✅")
            self._clear_register()

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El DPI ya está registrado.")
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))

    def _build_search_tab(self, parent):
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        search_frame = tk.LabelFrame(container, text="Buscar usuario", bg="#FFFFFF", padx=12, pady=12, font=("Segoe UI", 10))
        search_frame.pack(fill="x", pady=6)

        tk.Label(search_frame, text="Nombre (parcial):", bg="#FFFFFF").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.search_name = ttk.Entry(search_frame, width=40)
        self.search_name.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(search_frame, text="Número de casa:", bg="#FFFFFF").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.search_house = ttk.Entry(search_frame, width=40)
        self.search_house.grid(row=1, column=1, padx=6, pady=6)

        tk.Label(search_frame, text="DPI:", bg="#FFFFFF").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.search_dpi = ttk.Entry(search_frame, width=40)
        self.search_dpi.grid(row=2, column=1, padx=6, pady=6)

        btns = tk.Frame(search_frame, bg="#FFFFFF")
        btns.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Buscar", command=self._perform_search).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Limpiar", command=self._clear_search).grid(row=0, column=1, padx=6)

        self.search_tree = ttk.Treeview(container, columns=("id","nombre","direccion","numero","dpi","nit","servicio","contador"), show="headings")
        for col, heading in [("id","ID"),("nombre","Nombre"),("direccion","Dirección"),("numero","Número de casa"),
                             ("dpi","DPI"),("nit","NIT"),("servicio","Servicio agua"),("contador","Contador")]:
            self.search_tree.heading(col, text=heading)
            self.search_tree.column(col, width=120 if col!="nombre" else 220, anchor="w")
        self.search_tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _clear_search(self):
        self.search_name.delete(0, tk.END)
        self.search_house.delete(0, tk.END)
        self.search_dpi.delete(0, tk.END)
        for i in self.search_tree.get_children():
            self.search_tree.delete(i)

    def _perform_search(self):
        name = self.search_name.get().strip()
        house = self.search_house.get().strip()
        dpi = self.search_dpi.get().strip()

        query = "SELECT * FROM usuarios_registrados WHERE 1=1"
        params = []

        if name:
            query += " AND nombre LIKE ?"
            params.append(f"%{name}%")
        if house:
            query += " AND numero_casa = ?"
            params.append(house)
        if dpi:
            query += " AND dpi = ?"
            params.append(dpi)

        with DatabaseManager.connect() as conn:
            cur = conn.execute(query, tuple(params))
            rows = cur.fetchall()

        for i in self.search_tree.get_children():
            self.search_tree.delete(i)

        for r in rows:
            self.search_tree.insert("", "end", values=(r["id"], r["nombre"], r["direccion"],
                                                       r["numero_casa"], r["dpi"], r["nit"],
                                                       r["servicio_agua"], r["contador"]))

    def _build_all_tab(self, parent):
        top = tk.Frame(parent, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=12)

        ttk.Button(top, text="Refrescar lista", command=self._load_all_users).pack(side="left", padx=6)
        ttk.Button(top, text="Editar seleccionado", command=self._edit_selected).pack(side="left", padx=6)
        ttk.Button(top, text="Eliminar seleccionado", command=self._delete_selected).pack(side="left", padx=6)

        cols = ("id","nombre","direccion","numero","dpi","nit","servicio","contador")
        self.all_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col, heading in [("id","ID"),("nombre","Nombre"),("direccion","Dirección"),("numero","Número de casa"),
                             ("dpi","DPI"),("nit","NIT"),("servicio","Servicio agua"),("contador","Contador")]:
            self.all_tree.heading(col, text=heading)
            self.all_tree.column(col, width=120 if col!="nombre" else 220, anchor="w")

        self.all_tree.pack(fill="both", expand=True, padx=12, pady=12)
        self._load_all_users()

    def _load_all_users(self):
        for i in self.all_tree.get_children():
            self.all_tree.delete(i)
        with DatabaseManager.connect() as conn:
            cur = conn.execute("SELECT * FROM usuarios_registrados ORDER BY nombre COLLATE NOCASE")
            rows = cur.fetchall()
        for r in rows:
            self.all_tree.insert("", "end", values=(r["id"], r["nombre"], r["direccion"],
                                                    r["numero_casa"], r["dpi"], r["nit"],
                                                    r["servicio_agua"], r["contador"]))

    def _get_selected_from_tree(self, tree):
        sel = tree.selection()
        if not sel:
            return None
        item = tree.item(sel[0])
        vals = item["values"]

        return {
            "id": vals[0],
            "nombre": vals[1],
            "direccion": vals[2],
            "numero_casa": vals[3],
            "dpi": vals[4],
            "nit": vals[5],
            "servicio_agua": vals[6],
            "contador": vals[7]
        }

    def _edit_selected(self):
        sel = self._get_selected_from_tree(self.all_tree)
        if not sel:
            messagebox.showinfo("Editar", "Selecciona un usuario para editar.")
            return
        self._open_edit_window(sel)

    def _open_edit_window(self, data):
        edit_win = tk.Toplevel(self.ventana)
        edit_win.title("Editar usuario")
        edit_win.grab_set()
        pad = {"padx": 10, "pady": 6}
        tk.Label(edit_win, text="Editar usuario", font=("Segoe UI", 14, "bold")).pack(pady=8)

        frame = tk.Frame(edit_win)
        frame.pack(padx=12, pady=8)

        fields = ["Nombre","Dirección","Número de casa","DPI","NIT","Solicitar servicio de agua","Contador"]
        entries = {}
        values_map = {
            "Nombre": data["nombre"],
            "Dirección": data["direccion"],
            "Número de casa": data["numero_casa"],
            "DPI": data["dpi"],
            "NIT": data["nit"],
            "Solicitar servicio de agua": data["servicio_agua"],
            "Contador": data["contador"]
        }

        for i, f in enumerate(fields):
            tk.Label(frame, text=f).grid(row=i, column=0, sticky="w", **pad)
            if f == "Contador":
                cb = ttk.Combobox(frame, values=["Sí","No"], width=40)
                cb.grid(row=i, column=1, **pad)
                cb.set(values_map[f] if values_map[f] else "")
                entries[f] = cb
            else:
                e = ttk.Entry(frame, width=42)
                e.grid(row=i, column=1, **pad)
                e.insert(0, values_map[f] if values_map[f] else "")
                entries[f] = e

        def guardar_edicion():
            nuevo = {f: entries[f].get().strip() for f in fields}
            if not nuevo["Nombre"] or not nuevo["Número de casa"] or not nuevo["DPI"]:
                messagebox.showwarning("Validación", "Nombre, Número de casa y DPI son obligatorios.")
                return
            with DatabaseManager.connect() as conn:
                conn.execute("""
                    UPDATE usuarios_registrados
                    SET nombre=?, direccion=?, numero_casa=?, dpi=?, nit=?, servicio_agua=?, contador=?
                    WHERE id=?
                """, (
                    nuevo["Nombre"], nuevo["Dirección"], nuevo["Número de casa"],
                    nuevo["DPI"], nuevo["NIT"], nuevo["Solicitar servicio de agua"],
                    nuevo["Contador"], data["id"]
                ))
                conn.commit()
            messagebox.showinfo("Editar", "Registro actualizado correctamente.")
            edit_win.destroy()
            self._load_all_users()

        btns = tk.Frame(edit_win)
        btns.pack(pady=8)
        ttk.Button(btns, text="Guardar cambios", command=guardar_edicion).pack(side="left", padx=8)
        ttk.Button(btns, text="Cancelar", command=edit_win.destroy).pack(side="left", padx=8)

    def _delete_selected(self):
        sel = self._get_selected_from_tree(self.all_tree)
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona un usuario para eliminar.")
            return
        if messagebox.askyesno("Eliminar", f"¿Eliminar al usuario '{sel['nombre']}' (ID {sel['id']})?"):
            with DatabaseManager.connect() as conn:
                conn.execute("DELETE FROM usuarios_registrados WHERE id = ?", (sel["id"],))
                conn.commit()
            messagebox.showinfo("Eliminar", "Registro eliminado.")
            self._load_all_users()

    def cerrar_sesion(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        self.app.crear_login()

    def _abrir_panel_agua(self):
        for w in self.content.winfo_children():
            w.destroy()

        titulo = tk.Label(self.content, text="Servicio de Agua",
                          font=("Segoe UI", 20, "bold"), bg="#F2F5F9", fg="#2D3A4A")
        titulo.pack(pady=20)

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        cobro_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(cobro_tab, text="Cobro")
        self._build_cobro_agua_tab(cobro_tab)

        ver_todos_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(ver_todos_tab, text="Ver Todos")
        self._build_ver_todos_agua_tab(ver_todos_tab)

    def _build_cobro_agua_tab(self, parent):

        main_frame = tk.Frame(parent, bg="#FFFFFF", relief="raised", bd=2)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        search_frame = tk.LabelFrame(main_frame, text="Buscar Cliente", font=("Segoe UI", 12, "bold"),
                                     bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        search_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(search_frame, text="Nombre:", font=("Segoe UI", 10), bg="#FFFFFF").grid(row=0, column=0, sticky="w",
                                                                                         padx=5, pady=5)
        self.agua_nombre = ttk.Entry(search_frame, width=30, font=("Segoe UI", 10))
        self.agua_nombre.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(search_frame, text="DPI:", font=("Segoe UI", 10), bg="#FFFFFF").grid(row=0, column=2, sticky="w",
                                                                                      padx=5, pady=5)
        self.agua_dpi = ttk.Entry(search_frame, width=20, font=("Segoe UI", 10))
        self.agua_dpi.grid(row=0, column=3, padx=10, pady=5)

        btn_frame = tk.Frame(search_frame, bg="#FFFFFF")
        btn_frame.grid(row=1, column=0, columnspan=4, pady=15)

        ttk.Button(btn_frame, text="🔍 Buscar Cliente", command=self._buscar_cliente_agua).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="🔄 Limpiar", command=self._limpiar_busqueda_agua).pack(side="left", padx=10)

        info_frame = tk.LabelFrame(main_frame, text="Información del Cliente", font=("Segoe UI", 12, "bold"),
                                   bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        info_frame.pack(fill="x", padx=20, pady=10)

        self.info_cliente_label = tk.Label(info_frame, text="Seleccione un cliente para ver su información",
                                           font=("Segoe UI", 11), bg="#FFFFFF", fg="#666666")
        self.info_cliente_label.pack(pady=10)

        cobro_frame = tk.LabelFrame(main_frame, text="Detalles de Cobro", font=("Segoe UI", 12, "bold"),
                                    bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        cobro_frame.pack(fill="x", padx=20, pady=10)

        self.deuda_label = tk.Label(cobro_frame, text="", font=("Segoe UI", 12, "bold"), bg="#FFFFFF")
        self.deuda_label.pack(pady=10)

        self.btn_cobro = ttk.Button(cobro_frame, text="💰 REALIZAR COBRO",
                                    command=self._realizar_cobro_agua, state="disabled")
        self.btn_cobro.pack(pady=15)

        historial_frame = tk.LabelFrame(main_frame, text="Historial de Pagos", font=("Segoe UI", 12, "bold"),
                                        bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        historial_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Fecha", "Tipo", "Consumo", "Monto", "Estado")
        self.historial_tree = ttk.Treeview(historial_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.historial_tree.heading(col, text=col)
            self.historial_tree.column(col, width=120, anchor="center")

        scrollbar = ttk.Scrollbar(historial_frame, orient="vertical", command=self.historial_tree.yview)
        self.historial_tree.configure(yscrollcommand=scrollbar.set)

        self.historial_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _build_ver_todos_agua_tab(self, parent):
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        top = tk.Frame(container, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=12)

        ttk.Button(top, text="🔄 Refrescar lista", command=self._load_all_clientes_agua).pack(side="left", padx=6)
        ttk.Button(top, text="📊 Ver detalles", command=self._ver_detalles_cliente_agua).pack(side="left", padx=6)

        cols = ("id", "nombre", "dpi", "direccion", "numero_casa", "tipo", "deuda")
        self.agua_all_tree = ttk.Treeview(container, columns=cols, show="headings")

        headers = [("id", "ID", 60), ("nombre", "Nombre", 200), ("dpi", "DPI", 120),
                   ("direccion", "Dirección", 180), ("numero_casa", "Casa #", 80),
                   ("tipo", "Tipo Servicio", 120), ("deuda", "Deuda", 100)]

        for col, heading, width in headers:
            self.agua_all_tree.heading(col, text=heading)
            self.agua_all_tree.column(col, width=width, anchor="w" if col in ["nombre", "direccion"] else "center")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.agua_all_tree.yview)
        self.agua_all_tree.configure(yscrollcommand=scrollbar.set)

        self.agua_all_tree.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        scrollbar.pack(side="right", fill="y")

        self._load_all_clientes_agua()

    def _load_all_clientes_agua(self):
        for i in self.agua_all_tree.get_children():
            self.agua_all_tree.delete(i)

        with DatabaseManager.connect() as conn:
            clientes = conn.execute("SELECT * FROM clientes ORDER BY nombre COLLATE NOCASE").fetchall()

        for cliente in clientes:
            deuda = self._calcular_deuda_simple(cliente)
            tipo_texto = "Con contador" if cliente["tipo"] == "contador" else "Tarifa fija"

            self.agua_all_tree.insert("", "end", values=(
                cliente["id"],
                cliente["nombre"],
                cliente["dpi"],
                cliente["direccion"] or "N/A",
                cliente["numero_casa"],
                tipo_texto,
                f"Q{deuda:.2f}"
            ))

    def _calcular_deuda_simple(self, cliente):
        with DatabaseManager.connect() as conn:
            if cliente["tipo"] == "contador":
                lecturas = conn.execute("""
                    SELECT SUM(total_pagar) as total FROM lecturas 
                    WHERE cliente_id = ? AND pagado = 0
                """, (cliente["id"],)).fetchone()
                return float(lecturas["total"] or 0.0)
            else:
                ultimo_pago = cliente["ultimo_pago"]
                meses_sin_pagar = self._calcular_meses_transcurridos(ultimo_pago) if ultimo_pago else 1
                if meses_sin_pagar <= 0:
                    meses_sin_pagar = 0
                tarifa_mensual = float(cliente["total_mes"] or 12.0)
                return meses_sin_pagar * tarifa_mensual

    def _ver_detalles_cliente_agua(self):
        sel = self.agua_all_tree.selection()
        if not sel:
            messagebox.showinfo("Atención", "Seleccione un cliente de la lista")
            return

        item = self.agua_all_tree.item(sel[0])
        cliente_id = item["values"][0]

        with DatabaseManager.connect() as conn:
            cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()

        if cliente:
            info = f"""
Información del Cliente:
━━━━━━━━━━━━━━━━━━━━━━
👤 Nombre: {cliente['nombre']}
🆔 DPI: {cliente['dpi']}
🏠 Dirección: {cliente['direccion'] or 'No especificada'}
🏘️ Casa #: {cliente['numero_casa']}
📊 Tipo: {'Con contador' if cliente['tipo'] == 'contador' else 'Tarifa fija'}
💰 Tarifa mensual: Q{cliente['total_mes']:.2f}
📅 Último pago: {cliente['ultimo_pago'] or 'Sin registros'}
💸 Deuda: Q{self._calcular_deuda_simple(cliente):.2f}
            """
            messagebox.showinfo("Detalles del Cliente", info)

    def _buscar_cliente_agua(self):
        nombre = self.agua_nombre.get().strip()
        dpi = self.agua_dpi.get().strip()

        if not nombre and not dpi:
            messagebox.showwarning("Atención", "Ingrese al menos el nombre o DPI del cliente")
            return

        with DatabaseManager.connect() as conn:
            query = "SELECT * FROM clientes WHERE 1=1"
            params = []

            if nombre:
                query += " AND nombre LIKE ?"
                params.append(f"%{nombre}%")
            if dpi:
                query += " AND dpi = ?"
                params.append(dpi)

            cliente = conn.execute(query, params).fetchone()

        if not cliente:
            messagebox.showwarning("No encontrado", "No se encontró ningún cliente con esos datos")
            self._limpiar_info_cliente()
            return

        self.cliente_seleccionado = cliente
        self._mostrar_info_cliente(cliente)
        self._calcular_deuda_cliente(cliente)
        self._cargar_historial_pagos(cliente["id"])

    def _mostrar_info_cliente(self, cliente):
        info_text = f"""
                👤 Nombre: {cliente['nombre']}
                🆔 DPI: {cliente['dpi']}
                🏠 Dirección: {cliente['direccion'] or 'No especificada'}
                🏘️ Casa #: {cliente['numero_casa']}
                📊 Tipo de servicio: {'Con contador' if cliente['tipo'] == 'contador' else 'Tarifa fija'}
                """

        self.info_cliente_label.config(text=info_text, fg="#2D3A4A", justify="left")

    def _calcular_deuda_cliente(self, cliente):
        with DatabaseManager.connect() as conn:
            if cliente["tipo"] == "contador":
                lecturas = conn.execute("""
                            SELECT * FROM lecturas 
                            WHERE cliente_id = ? AND pagado = 0
                            ORDER BY fecha DESC
                        """, (cliente["id"],)).fetchall()

                total_deuda = 0
                detalles = []

                for lectura in lecturas:
                    meses_mora = self._calcular_meses_transcurridos(lectura["fecha"])
                    mora = meses_mora * 25.0  # Q25 por mes de mora
                    total_lectura = float(lectura["total_pagar"]) + mora
                    total_deuda += total_lectura

                    detalles.append(f"• Lectura {lectura['fecha']}: Q{lectura['total_pagar']:.2f} + Mora Q{mora:.2f}")

            else:
                ultimo_pago = cliente["ultimo_pago"]
                meses_sin_pagar = self._calcular_meses_transcurridos(ultimo_pago) if ultimo_pago else 1
                if meses_sin_pagar <= 0:
                    meses_sin_pagar = 1

                tarifa_mensual = float(cliente["total_mes"] or 12.0)
                mora_total = meses_sin_pagar * 25.0
                total_deuda = (meses_sin_pagar * tarifa_mensual) + mora_total

                detalles = [
                    f"• Tarifa mensual: Q{tarifa_mensual:.2f}",
                    f"• Meses sin pagar: {meses_sin_pagar}",
                    f"• Subtotal: Q{meses_sin_pagar * tarifa_mensual:.2f}",
                    f"• Mora total: Q{mora_total:.2f}"
                ]

        if total_deuda > 0:
            deuda_text = f"💸 DEUDA TOTAL: Q{total_deuda:.2f}\n\nDetalles:\n" + "\n".join(detalles)
            self.deuda_label.config(text=deuda_text, fg="#D32F2F", justify="left")
            self.btn_cobro.config(state="normal")
        else:
            self.deuda_label.config(text="✅ Cliente al día - Sin deuda pendiente", fg="#388E3C")
            self.btn_cobro.config(state="disabled")

    def _calcular_meses_transcurridos(self, fecha_str):
        if not fecha_str:
            return 0

        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hoy = date.today()
            return (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month)
        except:
            return 0

    def _cargar_historial_pagos(self, cliente_id):
        for item in self.historial_tree.get_children():
            self.historial_tree.delete(item)

        with DatabaseManager.connect() as conn:
            lecturas = conn.execute("""
                SELECT fecha, consumo, total_pagar, pagado, fecha_pago
                FROM lecturas 
                WHERE cliente_id = ?
                ORDER BY fecha DESC
                LIMIT 10
            """, (cliente_id,)).fetchall()

            for lectura in lecturas:
                estado = "✅ Pagado" if lectura["pagado"] else "❌ Pendiente"
                consumo = f"{lectura['consumo']:.1f} gal" if lectura["consumo"] else "N/A"

                self.historial_tree.insert("", "end", values=(
                    lectura["fecha"],
                    "Contador",
                    consumo,
                    f"Q{lectura['total_pagar']:.2f}",
                    estado
                ))


    def _realizar_cobro_agua(self):
        if not self.cliente_seleccionado:
            messagebox.showwarning("Error", "No hay cliente seleccionado")
            return
        respuesta = messagebox.askyesno(
            "Confirmar Cobro",
            f"¿Confirma el cobro para {self.cliente_seleccionado['nombre']}?\n\n"
            "Esta acción marcará todas las deudas pendientes como pagadas."
        )

        if not respuesta:
            return

        try:
            with DatabaseManager.connect() as conn:
                fecha_pago = datetime.now().strftime("%Y-%m-%d")

                if self.cliente_seleccionado["tipo"] == "contador":
                    conn.execute("""
                        UPDATE lecturas 
                        SET pagado = 1, fecha_pago = ?
                        WHERE cliente_id = ? AND pagado = 0
                    """, (fecha_pago, self.cliente_seleccionado["id"]))
                else:
                    conn.execute("""
                        UPDATE clientes 
                        SET ultimo_pago = ?, mora = 0.0
                        WHERE id = ?
                    """, (fecha_pago, self.cliente_seleccionado["id"]))

                conn.commit()

            messagebox.showinfo("Cobro Realizado",
                              f"✅ Cobro realizado exitosamente\n\n"
                              f"Cliente: {self.cliente_seleccionado['nombre']}\n"
                              f"Fecha: {fecha_pago}")
            self._calcular_deuda_cliente(self.cliente_seleccionado)
            self._cargar_historial_pagos(self.cliente_seleccionado["id"])

        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el cobro: {str(e)}")

    def _limpiar_busqueda_agua(self):
        self.agua_nombre.delete(0, tk.END)
        self.agua_dpi.delete(0, tk.END)
        self._limpiar_info_cliente()

    def _limpiar_info_cliente(self):
        self.cliente_seleccionado =None
        self.info_cliente_label.config(text="Seleccione un cliente para ver su información", fg="#666666")
        self.deuda_label.config(text="")
        self.btn_cobro.config(state="disabled")

        for item in self.historial_tree.get_children():
            self.historial_tree.delete(item)

if __name__ == "__main__":
    DatabaseManager.init_tables()
    DatabaseManager.setup()
    inicializar_credenciales()

    root = tk.Tk()
    app = Graficos(root)
    root.mainloop()