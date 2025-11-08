import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
            # Usuarios
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo_usuario TEXT NOT NULL,
                        contrasena TEXT NOT NULL
                    );
                """)
            # Clientes
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
            # Lecturas
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
                    contrasena TEXT NOT NULL,
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


#usuarios predeterminados
def inicializar_credenciales():
    with DatabaseManager.connect() as conn:
        cur = conn.execute("SELECT COUNT(*) AS c FROM credenciales").fetchone()
        if cur["c"] == 0:
            conn.execute("INSERT INTO credenciales (tipo_usuario, contrasena) VALUES (?, ?)", ("Administrador", "123"))
            conn.execute("INSERT INTO credenciales (tipo_usuario, contrasena) VALUES (?, ?)", ("LectorAgua", "456"))
            conn.execute("INSERT INTO credenciales (tipo_usuario, contrasena) VALUES (?, ?)", ("Cocodes", "789"))
            conn.commit()

def verificar_credencial(tipo, contrasena):
    with DatabaseManager.connect() as conn:
        cur = conn.execute("SELECT * FROM credenciales WHERE tipo_usuario=? AND contrasena=?", (tipo, contrasena))
        return cur.fetchone() is not None

class LectorApp:
    def __init__(self, root):
        self.root = root
        root.title("Lector de Agua - Registrar Lecturas")
        root.geometry("600x420")
        root.resizable(False, False)

        tk.Label(root, text="Registrar Lectura (usuarios con contador)", font=("Arial", 13, "bold")).pack(pady=10)

        frm = tk.Frame(root)
        frm.pack(pady=8)

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

    def cargar_usuarios(self):
        with DatabaseManager.connect() as conn:
            filas = conn.execute("SELECT id, nombre, numero_casa FROM clientes WHERE tipo='contador' ORDER BY nombre").fetchall()
            lista = [f"{f['id']} - {f['nombre']} (Casa {f['numero_casa']})" for f in filas]
        self.cb_usuarios['values'] = lista
        if lista:
            self.cb_usuarios.current(0)

    def guardar_lectura(self):
        seleccionado = self.cb_usuarios.get()
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

        cliente_id = seleccionado.split(" - ")[0]
        precio_unitario = 0.10  # Q0.10 por galón (configurable)
        total = consumo_float * precio_unitario

        with DatabaseManager.connect() as conn:
            conn.execute("""
                INSERT INTO lecturas(cliente_id, consumo, total_pagar, fecha, pagado)
                VALUES(?, ?, ?, ?, 0)
            """, (cliente_id, consumo_float, total, fecha))
            conn.commit()

        messagebox.showinfo("Guardado", f"Lectura registrada ✅\nTotal Q{total:.2f}")
        self.e_consumo.delete(0, tk.END)

class Graficos:
    def __init__(self, ventana):
        self.ventana = ventana
        # ensure DB tables exist
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

        # frame principal
        self.main_frame = tk.Frame(self.ventana, bg="#F6F6F8")
        self.main_frame.pack(fill="both", expand=True)

        # try to load background image safely
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        ruta_png = os.path.join(assets_dir, "fondo_login.png")
        ruta_jpg = os.path.join(assets_dir, "fondo_login.jpg")

        loaded = False
        if os.path.exists(ruta_png):
            try:
                self.bg_photo = tk.PhotoImage(file=ruta_png)
                bg_label = tk.Label(self.main_frame, image=self.bg_photo)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                loaded = True
            except Exception:
                loaded = False

        if (not loaded) and os.path.exists(ruta_jpg) and PIL_AVAILABLE:
            try:
                img = Image.open(ruta_jpg)
                # optional: resize to window if desired
                # img = img.resize((1100,650), Image.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(img)
                bg_label = tk.Label(self.main_frame, image=self.bg_photo)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                loaded = True
            except Exception:
                loaded = False

        if not loaded:
            # fallback to solid background color (safe)
            self.main_frame.configure(bg="#F6F6F8")

        # style
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
        elif tipo == "LectorAgua":
            # abrir ventana del lector
            lector_win = tk.Toplevel(self.ventana)
            LectorApp(lector_win)
            # volver al login cuando lector cierre ventana
            # opcional: keep main login open or close - here we'll leave main closed
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

            #bienvenido
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

        if agua:
            panel_agua = self.ServicioAgua(self.content)
            panel_agua.pack(fill="both", expand=True)
            return

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        # Registrar
        register_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(register_tab, text="Registrar")
        self._build_register_tab(register_tab)

        # Buscar
        search_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(search_tab, text="Buscar")
        self._build_search_tab(search_tab)

        # Ver todos
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

    def _calcular_mora_fijo(self, cliente_row):
        def meses_transcurridos(fecha_str):
            if not fecha_str:
                return 0
            try:
                f = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except Exception:
                return 0
            hoy = date.today()
            return (hoy.year - f.year) * 12 + (hoy.month - f.month)

        total_mes = float(cliente_row["total_mes"] or 12.0)
        ultimo = cliente_row["ultimo_pago"]
        meses = meses_transcurridos(ultimo)
        if meses <= 0:
            meses = 1
        mora = meses * 25.0
        total_deuda = meses * total_mes + mora
        return {"meses": meses, "mora": mora, "total_deuda": total_deuda}

    def _calcular_mora_lectura(self, lectura_row):
        fecha_lectura = lectura_row["fecha"]

        def meses_transcurridos(fecha_str):
            if not fecha_str:
                return 0
            try:
                f = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except Exception:
                return 0
            hoy = date.today()
            return (hoy.year - f.year) * 12 + (hoy.month - f.month)

        meses = meses_transcurridos(fecha_lectura)
        mora = max(0, meses) * 25.0
        total = float(lectura_row["total_pagar"]) + mora
        return {"meses": meses, "mora": mora, "total": total}

    def _abrir_panel_agua(self):
        # Limpia contenido actual
        for w in self.content.winfo_children():
            w.destroy()

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        # Subpestaña: Buscar cliente
        search_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(search_tab, text="Buscar cliente")
        self._build_agua_search_tab(search_tab)

        # Subpestaña: Ver todos
        all_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(all_tab, text="Ver todos")
        self._build_agua_all_tab(all_tab)

    def _build_agua_search_tab(self, parent):
        frame = tk.Frame(parent, bg="#FFFFFF")
        frame.pack(padx=12, pady=12, fill="x")

        # Entradas
        tk.Label(frame, text="Nombre:", bg="#FFFFFF").grid(row=0, column=0, padx=6, pady=6)
        self.agua_search_nombre = ttk.Entry(frame, width=40)
        self.agua_search_nombre.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(frame, text="DPI:", bg="#FFFFFF").grid(row=1, column=0, padx=6, pady=6)
        self.agua_search_dpi = ttk.Entry(frame, width=40)
        self.agua_search_dpi.grid(row=1, column=1, padx=6, pady=6)

        # Botón buscar
        ttk.Button(frame, text="Buscar", command=self._buscar_cliente_agua).grid(row=2, column=0, columnspan=2, pady=10)

        # Resultado
        self.agua_result_lbl = tk.Label(frame, text="", bg="#FFFFFF", fg="blue", font=("Arial", 12))
        self.agua_result_lbl.grid(row=3, column=0, columnspan=2, pady=6)

        # Botón generar boleta
        ttk.Button(frame, text="Generar Boleta", command=self._generar_boleta_agua).grid(row=4, column=0, columnspan=2,
                                                                                         pady=10)

    def _build_agua_all_tab(self, parent):
        # Tabla de todos los clientes con deuda
        self.agua_all_tree = ttk.Treeview(parent, columns=("ID", "Nombre", "DPI", "Mora"), show="headings")
        for col in self.agua_all_tree["columns"]:
            self.agua_all_tree.heading(col, text=col)
            self.agua_all_tree.column(col, width=120 if col != "Nombre" else 220, anchor="w")
        self.agua_all_tree.pack(fill="both", expand=True, padx=12, pady=12)

        # Cargar datos
        self._cargar_todos_clientes_agua()

    # Métodos auxiliares
    def _buscar_cliente_agua(self):
        nombre = self.agua_search_nombre.get().strip()
        dpi = self.agua_search_dpi.get().strip()

        if not nombre or not dpi:
            messagebox.showwarning("Aviso", "Ingrese nombre y DPI")
            return

        with DatabaseManager.connect() as conn:
            user = conn.execute("SELECT * FROM clientes WHERE nombre LIKE ? AND dpi=?", (f"%{nombre}%", dpi)).fetchone()

        if not user:
            self.agua_result_lbl.config(text="Usuario NO encontrado ❌")
            self.agua_cliente = None
            return

        self.agua_cliente = user

        # Calcular mora simple: 25 por mes por ejemplo
        with DatabaseManager.connect() as conn:
            lecturas = conn.execute("SELECT * FROM lecturas WHERE cliente_id=? AND pagado=0", (user["id"],)).fetchall()
        deuda = sum(l["total_pagar"] for l in lecturas)

        if deuda > 0:
            self.agua_result_lbl.config(text=f"MORA: Q{deuda:.2f} ❌")
        else:
            self.agua_result_lbl.config(text="Usuario SIN deuda ✅")

    def _generar_boleta_agua(self):
        if not hasattr(self, "agua_cliente") or not self.agua_cliente:
            messagebox.showwarning("Error", "Primero busque un cliente")
            return

        nombre = self.agua_cliente["nombre"]
        dpi = self.agua_cliente["dpi"]

        messagebox.showinfo("Boleta lista ✅",
                            f"Se generó la boleta del servicio de agua:\n\nNombre: {nombre}\nDPI: {dpi}")

    def _cargar_todos_clientes_agua(self):
        for i in self.agua_all_tree.get_children():
            self.agua_all_tree.delete(i)
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT id, nombre, dpi FROM clientes").fetchall()
        for r in rows:
            # Calcular mora simple
            lecturas = conn.execute("SELECT total_pagar FROM lecturas WHERE cliente_id=? AND pagado=0",
                                    (r["id"],)).fetchall()
            deuda = sum(l["total_pagar"] for l in lecturas)
            self.agua_all_tree.insert("", "end", values=(r["id"], r["nombre"], r["dpi"], f"Q{deuda:.2f}"))


class ServicioAguaAdmin(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.usuario = None

        # Formulario de búsqueda
        tk.Label(self, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_nombre = tk.Entry(self)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="DPI:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_dpi = tk.Entry(self)
        self.entry_dpi.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(self, text="Buscar", command=self.buscar_cliente).grid(row=0, column=4, padx=5, pady=5)

        # Tabla de resultados
        self.tree = ttk.Treeview(self, columns=("ID", "Nombre", "DPI", "Mora", "Total Deuda"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.grid(row=1, column=0, columnspan=5, padx=5, pady=5)

        # Botón para generar boleta
        tk.Button(self, text="Generar Boleta", command=self.generar_boleta).grid(row=2, column=0, padx=5, pady=5)

    def buscar_cliente(self):
        nombre = self.entry_nombre.get()
        dpi = self.entry_dpi.get()
        self.tree.delete(*self.tree.get_children())

        with DatabaseManager.connect() as conn:
            query = "SELECT * FROM clientes WHERE nombre LIKE ? AND dpi LIKE ?"
            rows = conn.execute(query, (f"%{nombre}%", f"%{dpi}%")).fetchall()

        for row in rows:
            mora = self.calcular_mora(row)
            total_deuda = (row["total_mes"] or 12.0) + mora
            self.tree.insert("", "end", values=(row["id"], row["nombre"], row["dpi"], mora, total_deuda))

    def calcular_mora(self, cliente_row):
        # Calcula la mora según la fecha del último pago
        ultimo_pago = cliente_row["ultimo_pago"]
        if not ultimo_pago:
            return 0
        fecha = datetime.strptime(ultimo_pago, "%Y-%m-%d").date()
        hoy = date.today()
        meses = (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month)
        mora = max(0, meses) * 25.0
        return mora

    def generar_boleta(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Aviso", "Seleccione un cliente")
            return
        cliente = self.tree.item(item)["values"]
        messagebox.showinfo("Boleta",
                            f"Boleta generada ✅\n\n"
                            f"Nombre: {cliente[1]}\n"
                            f"DPI: {cliente[2]}\n"
                            f"Mora: Q{cliente[3]:.2f}\n"
                            f"Total a pagar: Q{cliente[4]:.2f}")

class AdminAgua:
    def __init__(self, frame):
        self.frame = frame
        self.frame.configure(bg="white")

        tk.Label(frame, text="Servicio de Agua - Administrador",
                 font=("Arial", 16, "bold"), bg="white").pack(pady=15)

        form = tk.Frame(frame, bg="white")
        form.pack(pady=10)

        tk.Label(form, text="Nombre:", bg="white").grid(row=0, column=0, padx=6)
        self.e_nombre = ttk.Entry(form, width=35)
        self.e_nombre.grid(row=0, column=1, padx=6)

        tk.Label(form, text="DPI:", bg="white").grid(row=1, column=0, padx=6)
        self.e_dpi = ttk.Entry(form, width=35)
        self.e_dpi.grid(row=1, column=1, padx=6)

        ttk.Button(form, text="Buscar",
                   command=self.buscar_deuda).grid(row=2, column=0, columnspan=2, pady=10)

        self.lbl_resultado = tk.Label(frame, text="", font=("Arial", 12),
                                      bg="white", fg="blue")
        self.lbl_resultado.pack(pady=10)

        ttk.Button(frame, text="Generar Boleta",
                   command=self.generar_boleta).pack(pady=8)

    def buscar_deuda(self):
        nombre = self.e_nombre.get().strip()
        dpi = self.e_dpi.get().strip()

        if not nombre or not dpi:
            messagebox.showwarning("Ups", "Ingrese nombre y DPI.")
            return

        with DatabaseManager.connect() as conn:
            user = conn.execute("""
                SELECT * FROM clientes
                WHERE nombre LIKE ? AND dpi=?
            """, (f"%{nombre}%", dpi)).fetchone()

            if not user:
                self.lbl_resultado.config(text="Usuario NO encontrado ❌")
                self.usuario = None
                return

            self.usuario = user
            lecturas = conn.execute("""
                SELECT * FROM lecturas WHERE cliente_id=? AND pagado=0
            """, (user["id"],)).fetchall()

        deuda = sum(l["total_pagar"] for l in lecturas)

        if deuda > 0:
            self.lbl_resultado.config(text=f"MORA: Q{deuda:.2f} ❌")
        else:
            self.lbl_resultado.config(text="Usuario SIN deuda ✅")

    def generar_boleta(self):
        if not self.usuario:
            messagebox.showwarning("Error", "Primero debe buscar un usuario.")
            return

        nombre = self.usuario["nombre"]
        dpi = self.usuario["dpi"]

        messagebox.showinfo("Boleta lista ✅",
                            f"Se generó la boleta del servicio de agua:\n\n"
                            f"Nombre: {nombre}\nDPI: {dpi}")

#programa principal
if __name__ == "__main__":
    DatabaseManager.init_tables()
    DatabaseManager.setup()
    inicializar_credenciales()

    root = tk.Tk()
    app = Graficos(root)
    root.mainloop()