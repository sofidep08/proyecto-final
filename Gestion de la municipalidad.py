import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
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


def inicializar_credenciales():
    with DatabaseManager.connect() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM credenciales")
        count = cursor.fetchone()['count']

        if count == 0:
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
    def __init__(self, ventana, login_app):
        self.ventana = ventana
        self.login_app = login_app
        self.ventana.title("Panel del Lector de Agua")
        try:
            self.ventana.state('zoomed')
        except:
            self.ventana.geometry("1000x700")

        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True)

        self.tab_lectura = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_lectura, text="Hacer Lectura")

        tk.Label(self.tab_lectura, text="Registrar Lectura (usuarios con contador)",
                 font=("Arial", 13, "bold")).pack(pady=10)

        frm = tk.Frame(self.tab_lectura)
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

        ttk.Button(self.tab_lectura, text="Cargar usuarios", command=self.cargar_usuarios).pack(pady=6)
        ttk.Button(self.tab_lectura, text="Guardar Lectura", command=self.guardar_lectura).pack(pady=6)

        self.cargar_usuarios()

        self.tab_ayuda = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_ayuda, text="Ayuda")
        ttk.Label(self.tab_ayuda, text="Centro de ayuda del lector de agua", font=("Segoe UI", 16, "bold")).pack(pady=20)
        ayuda_texto = (
            "Aquí puedes registrar las lecturas de los medidores.\n\n"
            "1. Selecciona el usuario del menú desplegable.\n"
            "2. Ingresa el consumo en galones.\n"
            "3. Verifica la fecha (se establece automáticamente).\n"
            "4. Pulsa 'Guardar Lectura' para almacenar el dato.\n\n"
            "Si tienes problemas, contacta al administrador del sistema."
        )
        ttk.Label(self.tab_ayuda, text=ayuda_texto, justify="left", font=("Segoe UI", 11)).pack(padx=20, pady=10)

        self.tab_salir = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_salir, text="Salir")
        ttk.Label(self.tab_salir, text="¿Deseas cerrar el panel del lector?", font=("Segoe UI", 14)).pack(pady=40)
        ttk.Button(self.tab_salir, text="Cerrar Sesión", command=self.cerrar_sesion, width=20).pack(pady=20)

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

        cliente_id = seleccionado.split("-")[0].strip()
        precio_unitario = 1.00
        total = consumo_float * precio_unitario

        with DatabaseManager.connect() as conn:
            conn.execute("""
                INSERT INTO lecturas(cliente_id, consumo, total_pagar, fecha, pagado)
                VALUES(?, ?, ?, ?, 0)
            """, (cliente_id, consumo_float, total, fecha))
            conn.commit()

        messagebox.showinfo("Guardado", f"Lectura registrada correctamente\nTotal Q{total:.2f}")
        self.e_consumo.delete(0, tk.END)

    def cerrar_sesion(self):
        confirm = messagebox.askyesno("Confirmar", "¿Seguro que deseas cerrar sesión?")
        if confirm:
            for widget in self.ventana.winfo_children():
                widget.destroy()
            self.login_app.crear_login()

class LoginApp:
    def __init__(self, ventana):
        self.ventana = ventana
        DatabaseManager.init_tables()
        DatabaseManager.setup()
        inicializar_credenciales()
        self.crear_login()

    def crear_login(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()

        self.ventana.title("SAN FRANCISCO LA UNIÓN")
        self.ventana.geometry("1100x650")
        self.ventana.resizable(False, False)

        self.main_frame = tk.Frame(self.ventana, bg="#F6F6F8")
        self.main_frame.pack(fill="both", expand=True)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_imagen = os.path.join(script_dir, "atardecer_montanas.jpg")

        if os.path.exists(ruta_imagen):
            try:
                if PIL_AVAILABLE:
                    img = Image.open(ruta_imagen)
                    img = img.resize((1100, 650), Image.Resampling.LANCZOS)
                    self.bg_photo = ImageTk.PhotoImage(img)
                    bg_label = tk.Label(main_frame, image=self.bg_photo)
                    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print("Error cargando imagen:", e)

        tk.Label(main_frame, text="Iniciar Sesión", font=("Segoe UI", 22, "bold"), bg="#F6F6F8").pack(pady=50)
        tk.Label(main_frame, text="Usuario:").pack()
        self.tipo = ttk.Combobox(main_frame, values=["Administrador", "LectorAgua", "Cocodes"], state="readonly",
                                 width=40)
        self.tipo.set("Selecciona un usuario")
        self.tipo.pack(pady=10)

        tk.Label(main_frame, text="Contraseña:").pack()
        self.pass_entry = ttk.Entry(main_frame, show="*", width=42)
        self.pass_entry.pack(pady=10)

        ttk.Button(main_frame, text="Iniciar", command=self.verificar_login).pack(pady=10)
        ttk.Button(main_frame, text="Salir", command=self.ventana.quit).pack(pady=5)


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
            self.mostrar_interfaz_usuario(tipo)
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

    def mostrar_interfaz_usuario(self, tipo):
        if tipo == "Administrador":
            for widget in self.ventana.winfo_children():
                widget.destroy()
            AdminPanel(self.ventana, self)
        elif tipo == "LectorAgua":
            for widget in self.ventana.winfo_children():
                widget.destroy()
            LectorApp(self.ventana, self)
        else:
            for widget in self.ventana.winfo_children():
                widget.destroy()
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
            self.ventana.geometry("1200x800")

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
        tk.Label(self.content, text="Use el menú para acceder a las opciones de administrador",
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

        labels = ["Nombre", "Dirección", "Número de casa", "DPI", "NIT"]
        self._reg_entries = {}

        for i, lbl in enumerate(labels):
            tk.Label(form, text=lbl, font=("Segoe UI", 10), bg="#FFFFFF").grid(row=i, column=0, sticky="w", **pad)
            e = ttk.Entry(form, width=50)
            e.grid(row=i, column=1, **pad)
            self._reg_entries[lbl] = e

        tk.Label(form, text="Tipo de servicio", font=("Segoe UI", 10), bg="#FFFFFF").grid(row=len(labels), column=0, sticky="w", **pad)
        tipo_cb = ttk.Combobox(form, values=["Contador", "Fijo"], width=47)
        tipo_cb.set("Contador")
        tipo_cb.grid(row=len(labels), column=1, **pad)
        self._reg_entries["Tipo"] = tipo_cb

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

        tipo_servicio = "contador" if datos["Tipo"] == "Contador" else "fijo"

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
                    tipo_servicio
                ))
                conn.commit()

            messagebox.showinfo("Éxito", "Usuario registrado correctamente")
            self._clear_register()

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El DPI ya está registrado.")
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))

    def _build_search_tab(self, parent):
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        search_frame = tk.LabelFrame(container, text="Buscar cliente", bg="#FFFFFF", padx=12, pady=12, font=("Segoe UI", 10))
        search_frame.pack(fill="x", pady=6)

        tk.Label(search_frame, text="Nombre:", bg="#FFFFFF").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.search_name = ttk.Entry(search_frame, width=40)
        self.search_name.grid(row=0, column=1, padx=6, pady=6)

        tk.Label(search_frame, text="Número de casa:", bg="#FFFFFF").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.search_house = ttk.Entry(search_frame, width=40)
        self.search_house.grid(row=1, column=1, padx=6, pady=6)

        btns = tk.Frame(search_frame, bg="#FFFFFF")
        btns.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Buscar", command=self._perform_search).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Limpiar", command=self._clear_search).grid(row=0, column=1, padx=6)

        self.search_tree = ttk.Treeview(container, columns=("id","nombre","direccion","numero","tipo"), show="headings", height=15)
        for col, heading in [("id","ID"),("nombre","Nombre"),("direccion","Dirección"),("numero","Número de casa"),("tipo","Tipo")]:
            self.search_tree.heading(col, text=heading)
            self.search_tree.column(col, width=120 if col!="nombre" else 250, anchor="w")
        self.search_tree.pack(fill="both", expand=True, padx=12, pady=12)

    def _clear_search(self):
        self.search_name.delete(0, tk.END)
        self.search_house.delete(0, tk.END)
        for i in self.search_tree.get_children():
            self.search_tree.delete(i)

    def _perform_search(self):
        name = self.search_name.get().strip()
        house = self.search_house.get().strip()

        query = "SELECT * FROM clientes WHERE 1=1"
        params = []

        if name:
            query += " AND nombre LIKE ?"
            params.append(f"%{name}%")
        if house:
            query += " AND numero_casa LIKE ?"
            params.append(f"%{house}%")

        for i in self.search_tree.get_children():
            self.search_tree.delete(i)

        with DatabaseManager.connect() as conn:
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                self.search_tree.insert("", "end", values=(
                    row['id'], row['nombre'], row['direccion'], row['numero_casa'], row['tipo']
                ))

    def _build_all_tab(self, parent):
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(container, text="Todos los clientes registrados", font=("Segoe UI", 12, "bold"), bg="#FFFFFF").pack(pady=10)

        self.all_tree = ttk.Treeview(container, columns=("id","nombre","direccion","numero","dpi","tipo"), show="headings", height=20)
        for col, heading in [("id","ID"),("nombre","Nombre"),("direccion","Dirección"),("numero","Número"),("dpi","DPI"),("tipo","Tipo")]:
            self.all_tree.heading(col, text=heading)
            self.all_tree.column(col, width=100 if col!="nombre" else 200, anchor="w")
        self.all_tree.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Button(container, text="Actualizar lista", command=self._load_all_clients).pack(pady=10)

        self._load_all_clients()

    def _load_all_clients(self):
        for i in self.all_tree.get_children():
            self.all_tree.delete(i)

        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
            for row in rows:
                self.all_tree.insert("", "end", values=(
                    row['id'], row['nombre'], row['direccion'], row['numero_casa'], row['dpi'], row['tipo']
                ))

    def _abrir_panel_agua(self):
        for w in self.content.winfo_children():
            w.destroy()

        tk.Label(self.content, text="Servicio de Agua", font=("Segoe UI", 20, "bold"), bg="#F2F5F9").pack(pady=20)
        tk.Label(self.content, text="Panel de gestión de servicio de agua", font=("Segoe UI", 12), bg="#F2F5F9").pack(pady=10)

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        tab_lecturas = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(tab_lecturas, text="Ver Lecturas")

        container = tk.Frame(tab_lecturas, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        self.lecturas_tree = ttk.Treeview(container, columns=("id","cliente","consumo","total","fecha","pagado"), show="headings", height=20)
        for col, heading in [("id","ID"),("cliente","Cliente ID"),("consumo","Consumo"),("total","Total"),("fecha","Fecha"),("pagado","Pagado")]:
            self.lecturas_tree.heading(col, text=heading)
            self.lecturas_tree.column(col, width=100, anchor="w")
        self.lecturas_tree.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Button(container, text="Actualizar lecturas", command=self._load_lecturas).pack(pady=10)

        self._load_lecturas()

    def _load_lecturas(self):
        for i in self.lecturas_tree.get_children():
            self.lecturas_tree.delete(i)

        with DatabaseManager.connect() as conn:
            rows = conn.execute("""
                SELECT l.*, c.nombre
                FROM lecturas l
                JOIN clientes c ON l.cliente_id = c.id
                ORDER BY l.fecha DESC
            """).fetchall()
            for row in rows:
                pagado_texto = "Sí" if row['pagado'] else "No"
                self.lecturas_tree.insert("", "end", values=(
                    row['id'], f"{row['cliente_id']} - {row['nombre']}",
                    row['consumo'], f"Q{row['total_pagar']:.2f}", row['fecha'], pagado_texto
                ))

    def cerrar_sesion(self):
        confirm = messagebox.askyesno("Confirmar", "¿Seguro que deseas cerrar sesión?")
        if confirm:
            self.app.crear_login()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()