import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import tkinter.font as tkfont
from datetime import datetime, date

DB_NAME = "municipalidad.db"
def _add_header_footer(ventana, title_text, usuario_text, header_bg):
    header = tk.Frame(ventana, bg=header_bg, height=90)
    header.pack(fill="x", side="top")

    lbl_title = tk.Label(header, text=title_text,
                         font=("Segoe UI", 20, "bold"),
                         bg=header_bg, fg="#1B3556")
    lbl_title.place(relx=0.02, rely=0.5, anchor="w")

    lbl_user = tk.Label(header, text=f"👤 {usuario_text}",
                        font=("Segoe UI", 11, "bold"),
                        bg=header_bg, fg="#1B3556")
    lbl_user.place(relx=0.98, rely=0.5, anchor="e")

    footer_bg = "#E9EEF6"
    footer = tk.Frame(ventana, bg=footer_bg, height=26)
    footer.pack(fill="x", side="bottom")
    lbl_footer = tk.Label(footer, text="Municipalidad de San Francisco La Unión",
                          font=("Segoe UI", 15 , "italic"),
                          bg=footer_bg, fg="#2D3A4A")
    lbl_footer.pack(pady=2)
    return header, footer

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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS multas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_completo TEXT NOT NULL,
                    dpi TEXT NOT NULL,
                    tipo_multa TEXT NOT NULL,
                    detalle_otro TEXT,
                    estado TEXT NOT NULL DEFAULT 'Vigente',
                    creado_por TEXT,
                    fecha_creacion TEXT
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lecturas_agua (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    consumo_m3 REAL,
                    total_pagar REAL,
                    fecha TEXT,
                    pagado INTEGER DEFAULT 0,
                    fecha_pago TEXT,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios_registrados(id)
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ciudadanos_ornato (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    dpi TEXT UNIQUE NOT NULL,
                    nit TEXT,
                    salario REAL NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS boletas_ornato (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ciudadano_id INTEGER NOT NULL,
                    monto REAL NOT NULL,
                    con_multa INTEGER DEFAULT 0,
                    fecha_pago TEXT,
                    anio INTEGER,
                    FOREIGN KEY (ciudadano_id) REFERENCES ciudadanos_ornato(id)
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

# usuarios predeterminados
def inicializar_usuarios():
    usuarios = [
        (Administrador, "123"),
        (LectorAgua, "456"),
        (Cocodes, "789"),
        (LectorMultas, "012")
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

class LectorMultas(Usuario):
    pass

class Graficos:
    def __init__(self, ventana):
        self.ventana = ventana
        DatabaseManager.init_tables()
        self.crear_login()

    def crear_login(self):

        for widget in self.ventana.winfo_children():
            widget.destroy()

        self.ventana.title("Municipalidad de San Francisco La Unión - Login")
        try:
            self.ventana.state('zoomed')
        except:
            pass
        self.ventana.geometry("1100x650")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg="#CCEFFF")

        header = tk.Frame(self.ventana, bg="#008ECC", height=150)
        header.pack(fill="x")
        tk.Label(header, text="🏛️ Municipalidad de San Francisco La Unión",
                 font=("Segoe UI", 26, "bold"),
                 bg="#008ECC", fg="white").place(relx=0.5, rely=0.35,
                                                 anchor="center")
        tk.Label(header, text="Sistema de Gestión Municipal",
                 font=("Segoe UI", 13),
                 bg="#008ECC", fg="white").place(relx=0.5, rely=0.72,
                                                 anchor="center")

        card = tk.Frame(self.ventana, bg="white", bd=0)
        card.place(relx=0.5, rely=0.58, anchor="center")

        tk.Label(card, text="Iniciar sesión", font=("Segoe UI", 18, "bold"),
                 bg="white", fg="#2D3A4A").pack(pady=(12, 6))

        inner = tk.Frame(card, bg="white")
        inner.pack(padx=30, pady=17)

        tk.Label(inner, text="Usuario", font=("Segoe UI", 13),
                 bg="white", fg="#505050").grid(row=0, column=0, sticky="w", pady=(0,
                                                                                   4))

        self.tipo_usuario = tk.StringVar()
        opciones = ["Administrador", "LectorAgua", "Cocodes", "LectorMultas"]
        combo = ttk.Combobox(inner, textvariable=self.tipo_usuario,
                             values=opciones,
                             state="readonly", width=25, font=("Segoe UI", 14))
        combo.set("Selecciona un usuario")
        combo.grid(row=1, column=0, pady=(0, 8))

        tk.Label(inner, text="Contraseña", font=("Segoe UI", 13),
                 bg="white", fg="#505050").grid(row=2, column=0, sticky="w", pady=(6,
                                                                                   4))

        self.entry_pass = ttk.Entry(inner, show="*", width=45)
        self.entry_pass.grid(row=5, column=0, ipady=5)

        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=20)

        style = ttk.Style()
        style.configure(
            "big.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=(10, 7)
        )

        salir_btn = ttk.Button(
            btn_frame,
            text="Salir del programa",
            style="big.TButton",
            command=self._confirm_quit
        )
        salir_btn.grid(row=0, column=0, padx=10)

        iniciar_btn = ttk.Button(
            btn_frame,
            text="Iniciar Sesión",
            style="big.TButton",
            command=self.verificar_login
        )
        iniciar_btn.grid(row=0, column=1, padx=10)

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

        clases = {"Administrador": Administrador, "LectorAgua": LectorAgua, "Cocodes": Cocodes,
                  "LectorMultas": LectorMultas}
        clase_usuario = clases.get(tipo)

        if clase_usuario and clase_usuario.verificar_usuario(contra):
            self.mostrar_interfaz_usuario(tipo)
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

    def mostrar_interfaz_usuario(self, tipo):

        for widget in self.ventana.winfo_children():
            widget.destroy()

        colores = {
            "Administrador": "#DCE9FF",
            "Cocodes": "#E6F7E6",
            "LectorAgua": "#E6F3FF",
            "LectorMultas": "#F3F3F4"
        }
        header_color = colores.get(tipo, "#F6F6F8")

        if tipo == "Administrador":
            AdminPanel(self.ventana, self, usuario=tipo, header_bg="#DCE9FF")
        elif tipo == "Cocodes":
            CocodesPanel(self.ventana, self, usuario_tipo=tipo, header_bg="#71C551")
        elif tipo == "LectorMultas":
            LectorMultasPanel(self.ventana, self, usuario=tipo, header_bg="#AF69CD")
        elif tipo == "LectorAgua":
            LectorAguaPanel(self.ventana, self, usuario=tipo, header_bg="#008081")

class AdminPanel:
    def __init__(self, ventana, app, usuario="Administrador", header_bg="#DCE9FF"):
        self.ventana = ventana
        self.app = app
        self.usuario = usuario
        self.header_bg = header_bg
        self.selected_user_id = None
        self.crear_panel_admin()
        self.search_name: ttk.Entry | None = None
        self.search_house: ttk.Entry | None = None
        self.search_dpi: ttk.Entry | None = None
        self.search_tree: ttk.Treeview | None = None

    def crear_panel_admin(self):
        self.ventana.title("🏛️ Panel de Administrador - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        # Header + Footer
        self.header, self.footer = _add_header_footer(self.ventana, "🏛️ Panel de Administrador", self.usuario,
                                                      self.header_bg)

        # Menu bar
        menu_bar = tk.Menu(self.ventana)
        self.ventana.config(menu=menu_bar)

        menu_usuarios = tk.Menu(menu_bar, tearoff=0)
        menu_usuarios.add_command(label="Administrar usuarios", command=self._abrir_panel_usuarios)
        menu_bar.add_cascade(label="Usuarios", menu=menu_usuarios)

        menu_ornato = tk.Menu(menu_bar, tearoff=0)
        menu_ornato.add_command(label="🧾 Nuevo", command=self._abrir_panel_ornato)
        menu_bar.add_cascade(label="Boleta de Ornato", menu=menu_ornato)

        menu_agua = tk.Menu(menu_bar, tearoff=0)
        menu_agua.add_command(label="💧 Servicio de Agua", command=self._abrir_panel_agua)
        menu_bar.add_cascade(label="Servicio de Agua", menu=menu_agua)

        menu_multas = tk.Menu(menu_bar, tearoff=0)
        menu_multas.add_command(label="⚖️ Multas", command=self._abrir_multas_admin)
        menu_bar.add_cascade(label="Multas", menu=menu_multas)

        menu_ayuda = tk.Menu(menu_bar, tearoff=0)
        menu_ayuda.add_command(label="ℹ️ Acerca de", command=lambda: messagebox.showinfo("Acerca de", "Sistema Municipal"))
        menu_bar.add_cascade(label="Ayuda", menu=menu_ayuda)

        menu_salir = tk.Menu(menu_bar, tearoff=0)
        menu_salir.add_command(label="Cerrar sesión", command=self.cerrar_sesion)
        menu_salir.add_command(label="Salir", command=self.ventana.quit)
        menu_bar.add_cascade(label="Salir", menu=menu_salir)

        self.content = tk.Frame(self.ventana, bg="#F2F5F9")
        self.content.pack(fill="both", expand=True)

        # Mostrar bienvenida
        self.bienvenida()

    def bienvenida(self):
        for w in self.content.winfo_children():
            w.destroy()
        tk.Label(self.content, text="Bienvenido al Panel de Administración",
                 font=("Segoe UI", 24, "bold"), bg="#F2F5F9", fg="#2D3A4A").pack(pady=60)
        tk.Label(self.content, text=f"Usuario activo: 👤 {self.usuario}",
                 font=("Segoe UI", 12), bg="#F2F5F9", fg="#58606A").pack(pady=(0,20))
        tk.Label(self.content, text="Use el submenú para acceder a las opciones de administrador",
                 font=("Segoe UI", 12), bg="#F2F5F9", fg="#58606A").pack()

    def _abrir_panel_ornato(self):
        for w in self.content.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.configure(
            "Big.TNotebook",
            background="#FFFFFF",
            padding=10
        )
        style.configure(
            "Big.TNotebook.Tab",
            font=("Segoe UI", 12, "bold"),
            padding=[10, 8]
        )

        notebook = ttk.Notebook(self.content, style="Big.TNotebook")
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        # --- Tab para registrar ciudadanos ---
        tab_registrar = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(tab_registrar, text="🧾 Registrar Ciudadano")
        self._build_registrar_ornato(tab_registrar)

        # --- Tab para cobro ---
        tab_cobro = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(tab_cobro, text="💰 Cobro de Boleta")
        self._build_cobro_ornato(tab_cobro)

        # --- Tab para ver todos ---
        tab_ver = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(tab_ver, text="📋 Ver Todos")
        self._build_ver_todos_ornato(tab_ver)

    def _build_registrar_ornato(self, parent):
        frame = tk.Frame(parent, bg="#FFFFFF")
        frame.pack(pady=20)

        tk.Label(frame, text="Nombre:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="e", pady=5)
        self.e_nombre_orn = ttk.Entry(frame, width=40)
        self.e_nombre_orn.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(frame, text="DPI:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", pady=5)
        self.e_dpi_orn = ttk.Entry(frame, width=40)
        self.e_dpi_orn.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(frame, text="NIT (opcional):", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="e", pady=5)
        self.e_nit_orn = ttk.Entry(frame, width=40)
        self.e_nit_orn.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(frame, text="Salario (Q):", font=("Segoe UI", 11)).grid(row=3, column=0, sticky="e", pady=5)
        self.e_salario_orn = ttk.Entry(frame, width=40)
        self.e_salario_orn.grid(row=3, column=1, pady=5, padx=5)

        btn_frame = tk.Frame(frame, bg="#FFFFFF")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Registrar", command=self._registrar_ciudadano_ornato).grid(row=0, column=0, padx=8)
        ttk.Button(btn_frame, text="Limpiar", command=self._limpiar_registro_ornato).grid(row=0, column=1, padx=8)

    def _limpiar_registro_ornato(self):
        self.e_nombre_orn.delete(0, tk.END)
        self.e_dpi_orn.delete(0, tk.END)
        self.e_nit_orn.delete(0, tk.END)
        self.e_salario_orn.delete(0, tk.END)

    def _registrar_ciudadano_ornato(self):
        nombre = self.e_nombre_orn.get().strip()
        dpi = self.e_dpi_orn.get().strip()
        nit = self.e_nit_orn.get().strip()
        salario = self.e_salario_orn.get().strip()

        if not nombre or not dpi or not salario:
            messagebox.showwarning("Atención", "Debe llenar los campos Nombre, DPI y Salario.")
            return

        try:
            salario = float(salario)
        except ValueError:
            messagebox.showerror("Error", "El salario debe ser un número válido.")
            return

        try:
            with DatabaseManager.connect() as conn:
                conn.execute("""
                    INSERT INTO ciudadanos_ornato (nombre, dpi, nit, salario)
                    VALUES (?, ?, ?, ?)
                """, (nombre, dpi, nit if nit else None, salario))
                conn.commit()

            messagebox.showinfo("Éxito", "Ciudadano registrado correctamente ✅")
            self._limpiar_registro_ornato()
            self._cargar_ciudadanos_ornato()

        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El DPI ya está registrado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar: {e}")

    def _build_cobro_ornato(self, parent):
        main_frame = tk.Frame(parent, bg="#FFFFFF", relief="raised", bd=2)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        search_frame = tk.LabelFrame(main_frame, text="Buscar Ciudadano", font=("Segoe UI", 12, "bold"),
                                     bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        search_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(search_frame, text="DPI:", font=("Segoe UI", 10), bg="#FFFFFF").grid(row=0, column=0, sticky="w",
                                                                                      padx=5, pady=5)
        self.e_buscar_dpi_orn = ttk.Entry(search_frame, width=30, font=("Segoe UI", 10))
        self.e_buscar_dpi_orn.grid(row=0, column=1, padx=10, pady=5)

        btn_frame = tk.Frame(search_frame, bg="#FFFFFF")
        btn_frame.grid(row=1, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="🔍 Buscar", command=self._buscar_ciudadano_ornato).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🔄 Limpiar", command=self._limpiar_busqueda_ornato).pack(side="left", padx=8)

        info_frame = tk.LabelFrame(main_frame, text="Información del Ciudadano", font=("Segoe UI", 12, "bold"),
                                   bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        info_frame.pack(fill="x", padx=20, pady=10)

        self.info_ciudadano_label = tk.Label(info_frame, text="Busque un ciudadano para ver su información",
                                             font=("Segoe UI", 11), bg="#FFFFFF", fg="#666666")
        self.info_ciudadano_label.pack(pady=10)

        cobro_frame = tk.LabelFrame(main_frame, text="Monto a Pagar", font=("Segoe UI", 12, "bold"),
                                    bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        cobro_frame.pack(fill="x", padx=20, pady=10)

        self.monto_label = tk.Label(cobro_frame, text="", font=("Segoe UI", 12, "bold"), bg="#FFFFFF")
        self.monto_label.pack(pady=10)

        self.btn_pagar_boleta = ttk.Button(main_frame, text="💰 PAGAR BOLETA DE ORNATO",
                                           command=self._pagar_boleta_ornato, state="disabled")
        self.btn_pagar_boleta.pack(pady=15)

    def _buscar_ciudadano_ornato(self):
        dpi = self.e_buscar_dpi_orn.get().strip()
        if not dpi:
            messagebox.showwarning("Atención", "Ingrese un DPI para buscar.")
            return

        with DatabaseManager.connect() as conn:
            ciud = conn.execute("SELECT * FROM ciudadanos_ornato WHERE dpi = ?", (dpi,)).fetchone()

        if not ciud:
            messagebox.showwarning("No encontrado", "No se encontró ningún ciudadano con ese DPI.")
            self._limpiar_info_ornato()
            return

        self.ciudadano_actual = ciud
        salario = float(ciud["salario"])
        con_multa = 1 if datetime.now().month > 2 else 0

        if salario <= 3000:
            monto = 15 if not con_multa else 30
        elif salario <= 6000:
            monto = 50 if not con_multa else 100
        elif salario <= 9000:
            monto = 75 if not con_multa else 150
        elif salario <= 12000:
            monto = 100 if not con_multa else 200
        else:
            monto = 150 if not con_multa else 300

        self.monto_label.config(
            text=f"💰 Monto a pagar: Q{monto:.2f}\n{'⚠️ Con multa' if con_multa else 'Sin multa'}",
            fg="#D32F2F" if con_multa else "#2E7D32"
        )
        self.info_ciudadano_label.config(
            text=f"👤 {ciud['nombre']}\n🆔 DPI: {ciud['dpi']}\n💼 Salario: Q{salario:.2f}",
            fg="#2D3A4A"
        )
        self.btn_pagar_boleta.config(state="normal")

    def _pagar_boleta_ornato(self):
        ciud = getattr(self, "ciudadano_actual", None)
        if not ciud:
            messagebox.showwarning("Atención", "Debe buscar un ciudadano antes de cobrar.")
            return

        salario = float(ciud["salario"])
        anio_actual = datetime.now().year
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        con_multa = 1 if datetime.now().month > 2 else 0

        # Calcular monto
        if salario <= 3000:
            monto = 15 if not con_multa else 30
        elif salario <= 6000:
            monto = 50 if not con_multa else 100
        elif salario <= 9000:
            monto = 75 if not con_multa else 150
        elif salario <= 12000:
            monto = 100 if not con_multa else 200
        else:
            monto = 150 if not con_multa else 300

        # Confirmar cobro
        confirmar = messagebox.askyesno(
            "Confirmar Cobro",
            f"¿Desea cobrar la boleta de {ciud['nombre']}?\nMonto: Q{monto:.2f}"
        )
        if not confirmar:
            return

        try:
            with DatabaseManager.connect() as conn:
                pago_existente = conn.execute("""
                    SELECT * FROM boletas_ornato WHERE ciudadano_id=? AND anio=?
                """, (ciud["id"], anio_actual)).fetchone()

                if pago_existente:
                    messagebox.showwarning("Aviso", f"El ciudadano ya pagó la boleta del año {anio_actual}.")
                    return

                conn.execute("""
                    INSERT INTO boletas_ornato (ciudadano_id, monto, con_multa, fecha_pago, anio)
                    VALUES (?, ?, ?, ?, ?)
                """, (ciud["id"], monto, con_multa, fecha_hoy, anio_actual))
                conn.commit()

            messagebox.showinfo("Pago registrado", f"✅ Boleta pagada correctamente.\nMonto: Q{monto:.2f}")
            self.btn_pagar_boleta.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el pago: {e}")

    def _limpiar_busqueda_ornato(self):
        self.e_buscar_dpi_orn.delete(0, tk.END)
        self._limpiar_info_ornato()

    def _limpiar_info_ornato(self):
        self.ciudadano_actual = None
        self.info_ciudadano_label.config(text="Busque un ciudadano para ver su información", fg="#666666")
        self.monto_label.config(text="")
        self.btn_pagar_boleta.config(state="disabled")

    def _build_ver_todos_ornato(self, parent):
        frame = tk.Frame(parent, bg="#FFFFFF")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Button(frame, text="🔄 Refrescar lista", command=self._cargar_ciudadanos_ornato).pack(pady=10)

        cols = ("id", "nombre", "dpi", "nit", "salario", "estado")
        self.tree_ciudadanos = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        self.tree_ciudadanos.pack(fill="both", expand=True)

        for c, t in zip(cols, ["ID", "Nombre", "DPI", "NIT", "Salario (Q)", "Estado"]):
            self.tree_ciudadanos.heading(c, text=t)
            self.tree_ciudadanos.column(c, width=140, anchor="center")

        self._cargar_ciudadanos_ornato()

    def _cargar_ciudadanos_ornato(self):
        if not hasattr(self, "tree_ciudadanos"):
            return

        for i in self.tree_ciudadanos.get_children():
            self.tree_ciudadanos.delete(i)

        anio_actual = datetime.now().year

        with DatabaseManager.connect() as conn:
            rows = conn.execute(f"""
                SELECT 
                    c.id,
                    c.nombre,
                    c.dpi,
                    c.nit,
                    c.salario,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM boletas_ornato b 
                            WHERE b.ciudadano_id = c.id AND b.anio = ?
                        ) THEN '✅ Pagó'
                        ELSE '❌ No ha pagado'
                    END AS estado
                FROM ciudadanos_ornato c
                ORDER BY c.id DESC
            """, (anio_actual,)).fetchall()

        for r in rows:
            self.tree_ciudadanos.insert("", "end", values=(
                r["id"],
                r["nombre"],
                r["dpi"],
                r["nit"] if r["nit"] else "—",
                f"Q{r['salario']:.2f}",
                r["estado"]
            ))

    def _abrir_panel_agua(self):
        try:
            self.header.pack_forget()
            self.footer.pack_forget()
        except:
            pass

        for w in self.content.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.configure("Big.TNotebook", background="#FFFFFF", padding=14)

        style.configure(
            "Big.TNotebook.Tab",
            font=("Segoe UI", 11, "bold"),
            padding=[12, 10]
        )

        notebook = ttk.Notebook(self.content, style="Big.TNotebook")
        notebook.pack(fill="both", expand=True, padx=22, pady=22)

        cobro_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(cobro_tab, text="💧 Cobro")
        self._build_cobro_agua_tab(cobro_tab)

        ver_todos_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(ver_todos_tab, text="📄 Ver Todos")
        self._build_ver_todos_agua_tab(ver_todos_tab)

    def _build_cobro_agua_tab(self, parent):
        main_frame = tk.Frame(parent, bg="#FFFFFF", relief="raised", bd=2)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        search_frame = tk.LabelFrame(main_frame, text="Buscar Cliente", font=("Segoe UI", 12, "bold"),
                                     bg="#FFFFFF", fg="#2D3A4A", padx=15, pady=15)
        search_frame.pack(fill="x", padx=20, pady=20)

        tk.Label(search_frame, text="Nombre:", font=("Segoe UI", 10), bg="#FFFFFF").grid(row=0, column=0,
                                                                                         sticky="w",
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

        self.btn_cobro = ttk.Button(btn_frame, text="💰 REALIZAR COBRO",
                                    command=self._realizar_cobro_agua, state="disabled")
        self.btn_cobro.pack(side="left", padx=10)

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
        historial_frame = tk.LabelFrame(main_frame, text="Historial de Lecturas", font=("Segoe UI", 12, "bold"),
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

        cols = ("id", "nombre", "dpi", "direccion", "numero_casa", "contador", "deuda")
        self.agua_all_tree = ttk.Treeview(container, columns=cols, show="headings")

        headers = [("id", "ID", 60), ("nombre", "Nombre", 200), ("dpi", "DPI", 120),
                   ("direccion", "Dirección", 180), ("numero_casa", "Casa #", 80),
                   ("contador", "Contador", 100), ("deuda", "Deuda", 100)]

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
            clientes = conn.execute("""
                SELECT * FROM usuarios_registrados
                WHERE servicio_agua = 'Sí' OR servicio_agua = 'si'
                ORDER BY nombre COLLATE NOCASE
            """).fetchall()

        for cliente in clientes:
            deuda = self._calcular_deuda_simple(cliente)
            contador_texto = "Con contador" if (cliente["contador"] or "").lower() == "sí" else "Tarifa fija"

            self.agua_all_tree.insert("", "end", values=(
                cliente["id"],
                cliente["nombre"],
                cliente["dpi"],
                cliente["direccion"] or "N/A",
                cliente["numero_casa"],
                contador_texto,
                f"Q{deuda:.2f}"
            ))

    def _calcular_deuda_simple(self, cliente):
        with DatabaseManager.connect() as conn:
            if (cliente["contador"] or "").lower() == "sí":
                lecturas = conn.execute("""
                    SELECT SUM(total_pagar) as total FROM lecturas_agua
                    WHERE usuario_id = ? AND pagado = 0
                """, (cliente["id"],)).fetchone()
                return float(lecturas["total"] or 0.0)
            else:
                tarifa_fija = 20.0
                ultimo_pago = None
                try:
                    ultimo_pago = cliente["ultimo_pago"]
                except:
                    pass
                meses_sin_pagar = self._calcular_meses_transcurridos(ultimo_pago) if ultimo_pago else 1
                if meses_sin_pagar < 0:
                    meses_sin_pagar = 0
                return meses_sin_pagar * tarifa_fija

    def _ver_detalles_cliente_agua(self):
        sel = self.agua_all_tree.selection()
        if not sel:
            messagebox.showinfo("Atención", "Seleccione un cliente de la lista")
            return

        item = self.agua_all_tree.item(sel[0])
        usuario_id = item["values"][0]

        with DatabaseManager.connect() as conn:
            cliente = conn.execute("SELECT * FROM usuarios_registrados WHERE id = ?", (usuario_id,)).fetchone()

        if cliente:
            info = f"""
Información del Cliente:
━━━━━━━━━━━━━━━━━━━━━━
👤 Nombre: {cliente['nombre']} 🆔 DPI: {cliente['dpi']}
🏠 Dirección: {cliente['direccion'] or 'No especificada'} 🏘️ Casa #: {cliente['numero_casa']}
📊 Contador: {cliente['contador'] or 'N/A'}
            """
            messagebox.showinfo("Detalles del Cliente", info)

    def _buscar_cliente_agua(self):
        nombre = self.agua_nombre.get().strip()
        dpi = self.agua_dpi.get().strip()

        if not nombre and not dpi:
            messagebox.showwarning("Atención", "Ingrese al menos el nombre o DPI del cliente")
            return

        with DatabaseManager.connect() as conn:
            query = "SELECT * FROM usuarios_registrados WHERE 1=1"
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

    def _realizar_cobro_agua(self):
        if not hasattr(self, "cliente_seleccionado") or not self.cliente_seleccionado:
            messagebox.showwarning("Error", "No hay cliente seleccionado")
            return

        respuesta = messagebox.askyesno(
            "Confirmar Cobro",
            f"¿Confirma el cobro para {self.cliente_seleccionado['nombre']}?\n\n"
            "Esta acción marcará todas las lecturas pendientes como pagadas."
        )

        if not respuesta:
            return

        try:
            with DatabaseManager.connect() as conn:
                fecha_pago = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn.execute("""
                    UPDATE lecturas_agua
                    SET pagado = 1, fecha_pago = ?
                    WHERE usuario_id = ? AND pagado = 0
                """, (fecha_pago, self.cliente_seleccionado["id"]))

                conn.commit()

            messagebox.showinfo(
                "Cobro Realizado",
                f"✅ Cobro realizado exitosamente\n\n"
                f"Cliente: {self.cliente_seleccionado['nombre']}\n"
                f"Fecha: {fecha_pago}"
            )

            self._calcular_deuda_cliente(self.cliente_seleccionado)
            self._cargar_historial_pagos(self.cliente_seleccionado["id"])

        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el cobro: {str(e)}")

    def _mostrar_info_cliente(self, cliente):
        info_text = f"""
                👤 Nombre: {cliente['nombre']} 🆔 DPI: {cliente['dpi']}
                🏠 Dirección: {cliente['direccion'] or 'No especificada'} 🏘️ Casa #: {cliente['numero_casa']}
                📊 Contador: {cliente['contador'] or 'N/A'}
                """

        self.info_cliente_label.config(text=info_text, fg="#2D3A4A", justify="left")

    def _calcular_deuda_cliente(self, cliente):
        with DatabaseManager.connect() as conn:
            lecturas = conn.execute("""
                        SELECT * FROM lecturas_agua
                        WHERE usuario_id = ? AND pagado = 0
                        ORDER BY fecha DESC
                    """, (cliente["id"],)).fetchall()

            total_deuda = 0
            detalles = []

            for lectura in lecturas:
                meses_mora = self._calcular_meses_transcurridos(lectura["fecha"])
                mora = meses_mora * 25.0
                total_lectura = float(lectura["total_pagar"]) + mora
                total_deuda += total_lectura

                detalles.append(
                    f"• Lectura {lectura['fecha']}: Q{lectura['total_pagar']:.2f} + Mora Q{mora:.2f}")

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
            fecha = datetime.strptime(fecha_str.split(" ")[0], "%Y-%m-%d").date()
            hoy = date.today()
            return (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month)
        except:
            return 0

    def _cargar_historial_pagos(self, usuario_id):
        for item in self.historial_tree.get_children():
            self.historial_tree.delete(item)

        with DatabaseManager.connect() as conn:
            lecturas = conn.execute("""
                SELECT fecha, consumo_m3 as consumo, total_pagar, pagado, fecha_pago
                FROM lecturas_agua
                WHERE usuario_id = ?
                ORDER BY fecha DESC
                LIMIT 10
            """, (usuario_id,)).fetchall()

            for lectura in lecturas:
                estado = "✅ Pagado" if lectura["pagado"] else "❌ Pendiente"
                consumo = f"{lectura['consumo']:.2f} m³" if lectura["consumo"] is not None else "N/A"

                self.historial_tree.insert("", "end", values=(
                    lectura["fecha"],
                    "Contador",
                    consumo,
                    f"Q{lectura['total_pagar']:.2f}",
                    estado
                ))

    def _limpiar_busqueda_agua(self):
        self.agua_nombre.delete(0, tk.END)
        self.agua_dpi.delete(0, tk.END)
        self._limpiar_info_cliente()

    def _limpiar_info_cliente(self):
        self.cliente_seleccionado = None
        self.info_cliente_label.config(text="Seleccione un cliente para ver su información", fg="#666666")
        self.deuda_label.config(text="")
        self.btn_cobro.config(state="disabled")

        for item in self.historial_tree.get_children():
            self.historial_tree.delete(item)

    def _abrir_panel_usuarios(self):
        for w in self.content.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.configure("Big.TNotebook", background="#FFFFFF", padding=10)
        style.configure("Big.TNotebook.Tab", font=("Segoe UI", 13, "bold"), padding=[10, 5])

        notebook = ttk.Notebook(self.content, style="Big.TNotebook")
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        registro_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(registro_tab, text="📝 Registrar")
        self.buscar_registro(registro_tab)

        buscando = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(buscando, text="🔍 Buscar")
        self.buscar_tab(buscando)

        all_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(all_tab, text="📋 Ver todos")
        self._build_all_tab(all_tab)

    def buscar_registro(self, parent):
        pad = {"padx": 15, "pady": 10}
        form = tk.Frame(parent, bg="#FFFFFF")
        form.pack(padx=20, pady=20, anchor="n")

        fuente_label = ("Segoe UI", 12)
        fuente_entry = ("Segoe UI", 10)
        fuente_boton = ("Segoe UI", 10, "bold")

        labels = ["Nombre", "Dirección", "Número de casa", "DPI", "NIT", "Solicitar servicio de agua"]
        self._reg_entries = {}

        for i, lbl in enumerate(labels):
            tk.Label(form, text=lbl, font=fuente_label, bg="#FFFFFF").grid(row=i, column=0, sticky="w", **pad)

            e = ttk.Entry(form, width=60)
            e.grid(row=i, column=1, **pad, ipady=6)  # ipady agranda verticalmente
            e.configure(font=fuente_entry)
            self._reg_entries[lbl] = e

        tk.Label(form, text="Contador", font=fuente_label, bg="#FFFFFF").grid(row=len(labels), column=0, sticky="w",
                                                                              **pad)
        contador_cb = ttk.Combobox(form, values=["Sí", "No"], width=57, font=fuente_entry)
        contador_cb.grid(row=len(labels), column=1, **pad, ipady=6)
        self._reg_entries["Contador"] = contador_cb

        btn_frame = tk.Frame(form, bg="#FFFFFF")
        btn_frame.grid(row=len(labels) + 1, column=0, columnspan=2, pady=20)

        style = ttk.Style()
        style.configure("Custom.TButton", font=fuente_boton, padding=10)

        ttk.Button(btn_frame, text="🧹 Limpiar", style="Custom.TButton", command=self.limpiar_registro).grid(row=0,
                                                                                                            column=0,
                                                                                                            padx=12)
        ttk.Button(btn_frame, text="💾 Guardar", style="Custom.TButton", command=self.guardar_registro).grid(row=0,
                                                                                                            column=1,
                                                                                                            padx=12)

    def limpiar_registro(self):
        for e in self._reg_entries.values():
            try:
                e.delete(0, tk.END)
            except:
                e.set("")

    def guardar_registro(self):
        datos = {campo: widget.get() for campo, widget in self._reg_entries.items()}

        if not datos["Nombre"] or not datos["Número de casa"] or not datos["DPI"]:
            messagebox.showwarning("Validación", "Los campos Nombre, Número de casa y DPI son obligatorios.")
            return

        with DatabaseManager.connect() as conn:
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

        messagebox.showinfo("Registro", "Usuario registrado correctamente. 💾")
        self.limpiar_registro()

    def buscar_tab(self, parent):
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        fuente_label = ("Segoe UI", 12)
        fuente_entry = ("Segoe UI", 10)
        fuente_group = ("Segoe UI", 14, "bold")

        search_frame = tk.LabelFrame(
            container,
            text="Buscar usuario",
            bg="#FFFFFF",
            padx=16,
            pady=16,
            font=fuente_group
        )
        search_frame.pack(fill="x", pady=10)

        labels = [
            ("Nombre (parcial):", "search_name"),
            ("Número de casa:", "search_house"),
            ("DPI:", "search_dpi")
        ]

        for i, (texto, atributo) in enumerate(labels):
            tk.Label(search_frame, text=texto, font=fuente_label, bg="#FFFFFF").grid(
                row=i, column=0, sticky="w", padx=8, pady=8
            )
            entry = ttk.Entry(search_frame, width=45, font=fuente_entry)
            entry.grid(row=i, column=1, padx=8, pady=8, ipady=5)
            setattr(self, atributo, entry)

        style = ttk.Style()
        style.configure(
            "Big.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=(10, 8)
        )

        btns = tk.Frame(search_frame, bg="#FFFFFF")
        btns.grid(row=3, column=0, columnspan=2, pady=14)

        ttk.Button(btns, text="🔍 Buscar", style="Big.TButton", command=self.buscar).grid(row=0, column=0, padx=10)
        ttk.Button(btns, text="🧹 Limpiar", style="Big.TButton", command=self.limpiar).grid(row=0, column=1, padx=10)

        self.search_tree = ttk.Treeview(
            container,
            columns=("id", "nombre", "direccion", "numero", "dpi", "nit", "servicio", "contador"),
            show="headings",
            height=6
        )

        style.configure(
            "Treeview",
            font=("Segoe UI", 12),
            rowheight=32
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 12, "bold")
        )

        headings = [
            ("id", "ID"),
            ("nombre", "Nombre"),
            ("direccion", "Dirección"),
            ("numero", "Número de casa"),
            ("dpi", "DPI"),
            ("nit", "NIT"),
            ("servicio", "Servicio agua"),
            ("contador", "Contador")
        ]

        for col, heading in headings:
            ancho = 150
            if col == "nombre":
                ancho = 220
            elif col == "id":
                ancho = 80

            self.search_tree.heading(col, text=heading)
            self.search_tree.column(col, width=ancho, anchor="w", stretch=True)

        self.search_tree.pack(fill="both", expand=True, padx=16, pady=16)

        self.search_tree.update_idletasks()

        font = tkfont.Font()
        for col in self.search_tree["columns"]:
            header_text = self.search_tree.heading(col, "text")
            width = font.measure(header_text) + 60
            self.search_tree.column(col, width=width, stretch=True)

    def limpiar(self):
        self.search_name.delete(0, tk.END)
        self.search_house.delete(0, tk.END)
        self.search_dpi.delete(0, tk.END)
        for i in self.search_tree.get_children():
            self.search_tree.delete(i)

    def buscar(self):
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
        top.pack(fill="x", padx=20, pady=16)

        style = ttk.Style()
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=(10, 6))

        ttk.Button(top, text="🔄 Refrescar lista", style="Big.TButton", command=self._load_all_users).pack(
            side="left",
            padx=10)
        ttk.Button(top, text="✏️ Editar seleccionado", style="Big.TButton", command=self._edit_selected).pack(
            side="left", padx=10)
        ttk.Button(top, text="🗑️ Eliminar seleccionado", style="Big.TButton", command=self._delete_selected).pack(
            side="left", padx=10)

        cols = ("id", "nombre", "direccion", "numero", "dpi", "nit", "servicio", "contador")
        self.all_tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)

        style.configure("Treeview", font=("Segoe UI", 12), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"))

        headings = [
            ("id", "ID"),
            ("nombre", "Nombre"),
            ("direccion", "Dirección"),
            ("numero", "Número de casa"),
            ("dpi", "DPI"),
            ("nit", "NIT"),
            ("servicio", "Servicio agua"),
            ("contador", "Contador")
        ]

        for col, heading in headings:
            ancho = 150
            if col == "nombre":
                ancho = 250
            elif col == "id":
                ancho = 80

            self.all_tree.heading(col, text=heading)
            self.all_tree.column(col, width=ancho, anchor="w",
                                 stretch=True)

        self.all_tree.pack(fill="both", expand=True, padx=20, pady=16)

        self.all_tree.update_idletasks()

        font = tkfont.Font()
        for col in self.all_tree["columns"]:
            header_text = self.all_tree.heading(col, "text")
            width = font.measure(header_text) + 50  # +50 px de margen para que no se corte
            self.all_tree.column(col, width=width, stretch=True)

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

        fields = ["Nombre", "Dirección", "Número de casa", "DPI", "NIT", "Solicitar servicio de agua", "Contador"]
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
                cb = ttk.Combobox(frame, values=["Sí", "No"], width=40)
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
        ttk.Button(btns, text="💾 Guardar cambios", command=guardar_edicion).pack(side="left", padx=8)
        ttk.Button(btns, text="❌ Cancelar", command=edit_win.destroy).pack(side="left", padx=8)

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

    def _abrir_multas_admin(self):

        for w in self.content.winfo_children():
            w.destroy()

        top = tk.Frame(self.content, bg="#FFFFFF")
        top.pack(fill="x", padx=20, pady=16)

        style = ttk.Style()
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=(10, 7))

        ttk.Button(top, text="🔄 Refrescar", style="Big.TButton", command=self._load_multas_admin).pack(side="left",
                                                                                                       padx=10)
        ttk.Button(top, text="🔎 Ver detalles", style="Big.TButton", command=self._ver_detalle_multa_admin).pack(
            side="left", padx=10)
        ttk.Button(top, text="🔁 Cambiar estado", style="Big.TButton",
                   command=self._cambiar_estado_seleccionado_admin).pack(side="left", padx=10)

        cols = ("id", "nombre", "dpi", "tipo", "detalle", "estado", "creado_por", "fecha")
        self.admin_multas_tree = ttk.Treeview(self.content, columns=cols, show="headings", height=4)

        style.configure("Treeview", font=("Segoe UI", 10), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        headings = [
            ("id", "ID"),
            ("nombre", "Nombre completo"),
            ("dpi", "DPI"),
            ("tipo", "Tipo multa"),
            ("detalle", "Detalle (otro)"),
            ("estado", "Estado"),
            ("creado_por", "Creado por"),
            ("fecha", "Fecha")
        ]

        for col, heading in headings:
            ancho = 180
            if col in ("nombre", "detalle"):
                ancho = 250
            elif col == "id":
                ancho = 80
            self.admin_multas_tree.heading(col, text=heading)

            self.admin_multas_tree.column(col, width=ancho, anchor="w", stretch=True)

        self.admin_multas_tree.pack(fill="both", expand=True, padx=20, pady=16)

        self.admin_multas_tree.update_idletasks()

        font = tkfont.Font()
        for col in self.admin_multas_tree["columns"]:
            header_text = self.admin_multas_tree.heading(col, "text")
            width = font.measure(header_text) + 30  # +50 px de margen visual
            self.admin_multas_tree.column(col, width=width, stretch=True)

        self._load_multas_admin()

    def _load_multas_admin(self):
        for i in self.admin_multas_tree.get_children():
            self.admin_multas_tree.delete(i)
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM multas ORDER BY fecha_creacion DESC").fetchall()
        for r in rows:
            self.admin_multas_tree.insert("", "end", values=(r["id"], r["nombre_completo"], r["dpi"],
                                                             r["tipo_multa"], r["detalle_otro"], r["estado"],
                                                             r["creado_por"], r["fecha_creacion"]))

    def _get_selected_multa(self, tree):
        sel = tree.selection()
        if not sel:
            return None
        item = tree.item(sel[0])
        vals = item["values"]
        return {
            "id": vals[0],
            "nombre_completo": vals[1],
            "dpi": vals[2],
            "tipo_multa": vals[3],
            "detalle_otro": vals[4],
            "estado": vals[5],
            "creado_por": vals[6],
            "fecha_creacion": vals[7]
        }

    def _ver_detalle_multa_admin(self):
        sel = self._get_selected_multa(self.admin_multas_tree)
        if not sel:
            messagebox.showinfo("Detalle", "Selecciona una multa para ver detalles.")
            return
        info = (f"ID: {sel['id']}\nNombre: {sel['nombre_completo']}\nDPI: {sel['dpi']}\n"
                f"Tipo: {sel['tipo_multa']}\nDetalle (otro): {sel['detalle_otro']}\nEstado: {sel['estado']}\n"
                f"Creada por: {sel['creado_por']}\nFecha: {sel['fecha_creacion']}")
        messagebox.showinfo("Detalle de la multa", info)

    def _cambiar_estado_seleccionado_admin(self):
        sel = self._get_selected_multa(self.admin_multas_tree)
        if not sel:
            messagebox.showinfo("Cambiar estado", "Selecciona una multa para cambiar su estado.")
            return

        win = tk.Toplevel(self.ventana)
        win.title("Cambiar estado de la multa")
        win.grab_set()
        tk.Label(win, text=f"Cambiar estado - ID {sel['id']} - {sel['nombre_completo']}").pack(padx=12, pady=8)
        estado_var = tk.StringVar(value=sel["estado"])
        cb = ttk.Combobox(win, values=["Vigente", "Pagada", "Anulada"], textvariable=estado_var, state="readonly", width=30)
        cb.pack(padx=12, pady=8)

        def guardar():
            nuevo = estado_var.get()
            with DatabaseManager.connect() as conn:
                conn.execute("UPDATE multas SET estado = ? WHERE id = ?", (nuevo, sel["id"]))
                conn.commit()
            messagebox.showinfo("Estado", "Estado actualizado.")
            win.destroy()
            self._load_multas_admin()

        ttk.Button(win, text="💾 Guardar", command=guardar).pack(padx=8, pady=8)
        ttk.Button(win, text="❌ Cancelar", command=win.destroy).pack(padx=8, pady=4)

# Panel Cocodes
class CocodesPanel:
    def __init__(self, ventana, app, usuario_tipo="Cocodes", header_bg="#E6F7E6"):
        self.ventana = ventana
        self.app = app
        self.usuario_tipo = usuario_tipo
        self.header_bg = header_bg
        self.crear_panel_cocodes()

    def crear_panel_cocodes(self):
        self.ventana.title("🌾 Panel de Cocodes - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        # Header + Footer con color verde
        _add_header_footer(self.ventana, "🌾 Panel de Cocodes", self.usuario_tipo, self.header_bg)

        menu_bar = tk.Menu(self.ventana)
        self.ventana.config(menu=menu_bar)

        menu_multas = tk.Menu(menu_bar, tearoff=0)
        menu_multas.add_command(label="➕ Crear multa", command=self._abrir_panel_multas)
        menu_bar.add_cascade(label="⚖️ Multas", menu=menu_multas)

        menu_salir = tk.Menu(menu_bar, tearoff=0)
        menu_salir.add_command(label="Cerrar sesión", command=self.cerrar_sesion)
        menu_salir.add_command(label="Salir", command=self.ventana.quit)
        menu_bar.add_cascade(label="Salir", menu=menu_salir)

        self.content = tk.Frame(self.ventana, bg="#F2F5F9")
        self.content.pack(fill="both", expand=True)

        self._abrir_panel_multas()

    def cerrar_sesion(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        self.app.crear_login()

    def _abrir_panel_multas(self):
        for w in self.content.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.configure("Big.TNotebook", background="#FFFFFF", padding=10)
        style.configure("Big.TNotebook.Tab", font=("Segoe UI", 12, "bold"), padding=[10, 8])

        style.configure("TLabel", font=("Segoe UI", 12))
        style.configure("TEntry", font=("Segoe UI", 12))
        style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=6)
        style.configure("TCombobox", font=("Segoe UI", 12))

        notebook = ttk.Notebook(self.content, style="Big.TNotebook")
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        crear_tab = tk.Frame(notebook, bg="#FFFFFF")
        ver_tab = tk.Frame(notebook, bg="#FFFFFF")
        modi_tab = tk.Frame(notebook, bg="#FFFFFF")

        notebook.add(crear_tab, text="➕ Crear multa")
        notebook.add(ver_tab, text="🔎 Ver registro de multas")
        notebook.add(modi_tab, text="✏️ Modificar multas")

        self._build_crear_multa(crear_tab)
        self._build_ver_multas(ver_tab)
        self._build_modificar_multas(modi_tab)

    def _build_crear_multa(self, parent):
        pad = {"padx": 12, "pady": 10}
        frame = tk.Frame(parent, bg="#FFFFFF")
        frame.pack(padx=20, pady=20, anchor="n")

        label_font = ("Segoe UI", 13)
        entry_font = ("Segoe UI", 12)

        # Nombre completo
        tk.Label(frame, text="Nombre completo:", bg="#FFFFFF", font=label_font).grid(row=0, column=0, sticky="w", **pad)
        self.cm_nombre = ttk.Entry(frame, width=55, font=entry_font)
        self.cm_nombre.grid(row=0, column=1, **pad)

        # DPI
        tk.Label(frame, text="DPI:", bg="#FFFFFF", font=label_font).grid(row=1, column=0, sticky="w", **pad)
        self.cm_dpi = ttk.Entry(frame, width=55, font=entry_font)
        self.cm_dpi.grid(row=1, column=1, **pad)

        # Tipo de multa
        tk.Label(frame, text="Tipo de multa:", bg="#FFFFFF", font=label_font).grid(row=2, column=0, sticky="w", **pad)
        tipos = [
            "Daño a la infraestructura pública.",
            "Daño al alumbrado público.",
            "Contaminación ambiental.",
            "Tala de árboles.",
            "Indocumentación",
            "Otro"
        ]
        self.cm_tipo = tk.StringVar()
        cb_tipo = ttk.Combobox(frame, textvariable=self.cm_tipo, values=tipos, state="readonly", width=52,
                               font=entry_font)
        cb_tipo.grid(row=2, column=1, **pad)
        cb_tipo.set(tipos[0])
        cb_tipo.bind("<<ComboboxSelected>>", self._tipo_seleccionado)

        # Otro tipo
        tk.Label(frame, text="Si eligió 'Otro', especifique:", bg="#FFFFFF", font=label_font).grid(row=3, column=0,
                                                                                                   sticky="w", **pad)
        self.cm_otro = ttk.Entry(frame, width=55, font=entry_font)
        self.cm_otro.grid(row=3, column=1, **pad)
        self.cm_otro.configure(state="disabled")

        # Botones
        btns = tk.Frame(frame, bg="#FFFFFF")
        btns.grid(row=4, column=0, columnspan=2, pady=16)
        ttk.Button(btns, text="🧹 Limpiar", command=self._limpiar_crear_multa).grid(row=0, column=0, padx=10, ipadx=10,
                                                                                   ipady=4)
        ttk.Button(btns, text="💾 Guardar", command=self._guardar_multa).grid(row=0, column=1, padx=10, ipadx=10,
                                                                             ipady=4)

    def _tipo_seleccionado(self, event=None):
        if self.cm_tipo.get() == "Otro":
            self.cm_otro.configure(state="normal")
        else:
            self.cm_otro.delete(0, tk.END)
            self.cm_otro.configure(state="disabled")

    def _limpiar_crear_multa(self):
        self.cm_nombre.delete(0, tk.END)
        self.cm_dpi.delete(0, tk.END)
        self.cm_tipo.set("")
        self.cm_otro.configure(state="disabled")
        self.cm_otro.delete(0, tk.END)

    def _guardar_multa(self):
        nombre = self.cm_nombre.get().strip()
        dpi = self.cm_dpi.get().strip()
        tipo = self.cm_tipo.get().strip()
        detalle = self.cm_otro.get().strip() if tipo == "Otro" else ""

        if not nombre or not dpi or not tipo:
            messagebox.showwarning("Validación", "Nombre completo, DPI y Tipo de multa son obligatorios.")
            return

        fecha = datetime.now().isoformat(sep=" ", timespec="seconds")

        with DatabaseManager.connect() as conn:
            conn.execute("""
                INSERT INTO multas (nombre_completo, dpi, tipo_multa, detalle_otro, estado, creado_por, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nombre, dpi, tipo, detalle, "Vigente", self.usuario_tipo, fecha))
            conn.commit()

        messagebox.showinfo("Multa", "Multa creada y guardada correctamente. ✅")
        self._limpiar_crear_multa()
        # refrescar vistas si existen
        try:
            self._cargar_multas_ver()
            self._cargar_multas_modificar()
        except Exception:
            pass

    def _build_ver_multas(self, parent):
        top = tk.Frame(parent, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=12)
        ttk.Button(top, text="🔄 Refrescar", command=self._cargar_multas_ver).pack(side="left", padx=6)
        ttk.Button(top, text="🔎 Ver detalle", command=self._ver_detalle_multa_ver).pack(side="left", padx=6)

        cols = ("id","nombre","dpi","tipo","detalle","estado","creado_por","fecha")
        self.ver_tree = ttk.Treeview(parent, columns=cols, show="headings")
        headings = [("id","ID"),("nombre","Nombre completo"),("dpi","DPI"),("tipo","Tipo multa"),
                    ("detalle","Detalle (otro)"),("estado","Estado"),("creado_por","Creado por"),("fecha","Fecha")]
        for col, heading in headings:
            self.ver_tree.heading(col, text=heading)
            self.ver_tree.column(col, width=120 if col not in ("nombre","detalle") else 220, anchor="w")
        self.ver_tree.pack(fill="both", expand=True, padx=12, pady=12)

        self._cargar_multas_ver()

    def _cargar_multas_ver(self):
        for i in self.ver_tree.get_children():
            self.ver_tree.delete(i)
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM multas ORDER BY fecha_creacion DESC").fetchall()
        for r in rows:
            self.ver_tree.insert("", "end", values=(r["id"], r["nombre_completo"], r["dpi"],
                                                    r["tipo_multa"], r["detalle_otro"],
                                                    r["estado"], r["creado_por"], r["fecha_creacion"]))

    def _ver_detalle_multa_ver(self):
        sel = self._get_selected_from_tree(self.ver_tree)
        if not sel:
            messagebox.showinfo("Detalle", "Selecciona una multa para ver detalle.")
            return
        info = (f"ID: {sel['id']}\nNombre: {sel['nombre_completo']}\nDPI: {sel['dpi']}\n"
                f"Tipo: {sel['tipo_multa']}\nDetalle (otro): {sel['detalle_otro']}\nEstado: {sel['estado']}\n"
                f"Creada por: {sel['creado_por']}\nFecha: {sel['fecha_creacion']}")
        messagebox.showinfo("Detalle de la multa", info)

    def _build_modificar_multas(self, parent):
        top = tk.Frame(parent, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=12)
        ttk.Button(top, text="🔄 Refrescar", command=self._cargar_multas_modificar).pack(side="left", padx=6)
        ttk.Button(top, text="✏️ Editar seleccionado", command=self._editar_seleccionado).pack(side="left", padx=6)
        ttk.Button(top, text="🗑️ Eliminar seleccionado", command=self._eliminar_seleccionado).pack(side="left", padx=6)

        cols = ("id","nombre","dpi","tipo","detalle","estado","creado_por","fecha")
        self.modi_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for col, heading in [("id","ID"),("nombre","Nombre completo"),("dpi","DPI"),("tipo","Tipo multa"),
                             ("detalle","Detalle (otro)"),("estado","Estado"),("creado_por","Creado por"),("fecha","Fecha")]:
            self.modi_tree.heading(col, text=heading)
            self.modi_tree.column(col, width=120 if col not in ("nombre","detalle") else 220, anchor="w")
        self.modi_tree.pack(fill="both", expand=True, padx=12, pady=12)

        self._cargar_multas_modificar()

    def _cargar_multas_modificar(self):
        for i in self.modi_tree.get_children():
            self.modi_tree.delete(i)
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM multas ORDER BY fecha_creacion DESC").fetchall()
        for r in rows:
            self.modi_tree.insert("", "end", values=(r["id"], r["nombre_completo"], r["dpi"],
                                                     r["tipo_multa"], r["detalle_otro"], r["estado"],
                                                     r["creado_por"], r["fecha_creacion"]))

    def _get_selected_from_tree(self, tree):
        sel = tree.selection()
        if not sel:
            return None
        item = tree.item(sel[0])
        vals = item["values"]
        return {
            "id": vals[0],
            "nombre_completo": vals[1],
            "dpi": vals[2],
            "tipo_multa": vals[3],
            "detalle_otro": vals[4],
            "estado": vals[5],
            "creado_por": vals[6],
            "fecha_creacion": vals[7]
        }

    def _editar_seleccionado(self):
        sel = self._get_selected_from_tree(self.modi_tree)
        if not sel:
            messagebox.showinfo("Editar", "Selecciona una multa para editar.")
            return

        win = tk.Toplevel(self.ventana)
        win.title("Editar multa")
        win.grab_set()
        pad = {"padx": 10, "pady": 6}

        tk.Label(win, text=f"Editar multa - ID {sel['id']}", font=("Segoe UI", 12, "bold")).pack(pady=8)
        frame = tk.Frame(win)
        frame.pack(padx=8, pady=8)

        tk.Label(frame, text="Nombre completo:").grid(row=0, column=0, sticky="w", **pad)
        e_nombre = ttk.Entry(frame, width=50)
        e_nombre.grid(row=0, column=1, **pad)
        e_nombre.insert(0, sel["nombre_completo"])

        tk.Label(frame, text="DPI:").grid(row=1, column=0, sticky="w", **pad)
        e_dpi = ttk.Entry(frame, width=50)
        e_dpi.grid(row=1, column=1, **pad)
        e_dpi.insert(0, sel["dpi"])

        tk.Label(frame, text="Tipo de multa:").grid(row=2, column=0, sticky="w", **pad)
        tipos = ["Daño a la infraestructura publica.", "Daño al alumbrado publico.", "Contaminación ambiental.",
                 "Tala de arboles.", "Indocumentación", "Otro"]
        tipo_var = tk.StringVar(value=sel["tipo_multa"])
        cb_tipo = ttk.Combobox(frame, values=tipos, textvariable=tipo_var, state="readonly", width=48)
        cb_tipo.grid(row=2, column=1, **pad)

        tk.Label(frame, text="Detalle (si eligió otro):").grid(row=3, column=0, sticky="w", **pad)
        e_otro = ttk.Entry(frame, width=50)
        e_otro.grid(row=3, column=1, **pad)
        e_otro.insert(0, sel["detalle_otro"] if sel["detalle_otro"] else "")

        def guardar_cambios():
            nuevo_nom = e_nombre.get().strip()
            nuevo_dpi = e_dpi.get().strip()
            nuevo_tipo = tipo_var.get().strip()
            nuevo_otro = e_otro.get().strip()

            if not nuevo_nom or not nuevo_dpi or not nuevo_tipo:
                messagebox.showwarning("Validación", "Nombre, DPI y Tipo son obligatorios.")
                return
            with DatabaseManager.connect() as conn:
                conn.execute("""
                    UPDATE multas SET nombre_completo=?, dpi=?, tipo_multa=?, detalle_otro=?
                    WHERE id = ?
                """, (nuevo_nom, nuevo_dpi, nuevo_tipo, nuevo_otro, sel["id"]))
                conn.commit()
            messagebox.showinfo("Editar", "Multa actualizada correctamente.")
            win.destroy()
            self._cargar_multas_modificar()
            self._cargar_multas_ver()

        btns = tk.Frame(win)
        btns.pack(pady=8)
        ttk.Button(btns, text="💾 Guardar cambios", command=guardar_cambios).pack(side="left", padx=6)
        ttk.Button(btns, text="❌ Cancelar", command=win.destroy).pack(side="left", padx=6)

    def _eliminar_seleccionado(self):
        sel = self._get_selected_from_tree(self.modi_tree)
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona una multa para eliminar.")
            return
        if messagebox.askyesno("Eliminar", f"¿Eliminar la multa ID {sel['id']}?"):
            with DatabaseManager.connect() as conn:
                conn.execute("DELETE FROM multas WHERE id = ?", (sel["id"],))
                conn.commit()
            messagebox.showinfo("Eliminar", "Multa eliminada.")
            self._cargar_multas_modificar()
            self._cargar_multas_ver()

# Panel LectorMultas
class LectorMultasPanel:
    def __init__(self, ventana, app, usuario="LectorMultas", header_bg="#F3F3F4"):
        self.ventana = ventana
        self.app = app
        self.usuario = usuario
        self.header_bg = header_bg
        self.crear_panel_lector()

    def crear_panel_lector(self):
        self.ventana.title("Lector de Multas - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        _add_header_footer(self.ventana, "⚖️ Lector de Multas", self.usuario, self.header_bg)

        menu_bar = tk.Menu(self.ventana)
        self.ventana.config(menu=menu_bar)
        menu_multas = tk.Menu(menu_bar, tearoff=0)
        menu_multas.add_command(label="🔎 Ver Multas", command=self._abrir_ver_multas)
        menu_bar.add_cascade(label="Multas", menu=menu_multas)

        menu_salir = tk.Menu(menu_bar, tearoff=0)
        menu_salir.add_command(label="Cerrar sesión", command=self.cerrar_sesion)
        menu_salir.add_command(label="Salir", command=self.ventana.quit)
        menu_bar.add_cascade(label="Salir", menu=menu_salir)

        self.content = tk.Frame(self.ventana, bg="#F2F5F9")
        self.content.pack(fill="both", expand=True)

        self._abrir_ver_multas()

    def cerrar_sesion(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        self.app.crear_login()

    def _abrir_ver_multas(self):
        for w in self.content.winfo_children():
            w.destroy()
        top = tk.Frame(self.content, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=12)
        ttk.Button(top, text="🔄 Refrescar", command=self._cargar_multas).pack(side="left", padx=6)
        ttk.Button(top, text="🔎 Ver detalle", command=self._ver_detalle).pack(side="left", padx=6)

        cols = ("id","nombre","dpi","tipo","detalle","estado","creado_por","fecha")
        self.tree = ttk.Treeview(self.content, columns=cols, show="headings")
        headings = [("id","ID"),("nombre","Nombre completo"),("dpi","DPI"),("tipo","Tipo multa"),
                    ("detalle","Detalle (otro)"),("estado","Estado"),("creado_por","Creado por"),("fecha","Fecha")]
        for col, heading in headings:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=120 if col not in ("nombre","detalle") else 220, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

        self._cargar_multas()

    def _cargar_multas(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT * FROM multas ORDER BY fecha_creacion DESC").fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["nombre_completo"], r["dpi"],
                                                r["tipo_multa"], r["detalle_otro"], r["estado"],
                                                r["creado_por"], r["fecha_creacion"]))

    def _ver_detalle(self):
        sel = self._get_selected(self.tree)
        if not sel:
            messagebox.showinfo("Detalle", "Selecciona una multa para ver detalle.")
            return
        info = (f"ID: {sel['id']}\nNombre: {sel['nombre_completo']}\nDPI: {sel['dpi']}\n"
                f"Tipo: {sel['tipo_multa']}\nDetalle (otro): {sel['detalle_otro']}\nEstado: {sel['estado']}\n"
                f"Creada por: {sel['creado_por']}\nFecha: {sel['fecha_creacion']}")
        messagebox.showinfo("Detalle de la multa", info)

    def _get_selected(self, tree):
        sel = tree.selection()
        if not sel:
            return None
        item = tree.item(sel[0])
        vals = item["values"]
        return {
            "id": vals[0],
            "nombre_completo": vals[1],
            "dpi": vals[2],
            "tipo_multa": vals[3],
            "detalle_otro": vals[4],
            "estado": vals[5],
            "creado_por": vals[6],
            "fecha_creacion": vals[7]
        }

class LectorAguaPanel:
    TARIFA_POR_M3 = 5.0
    def __init__(self, ventana, app, usuario="LectorAgua", header_bg="#E6F3FF"):
        self.ventana = ventana
        self.app = app
        self.usuario = usuario
        self.header_bg = header_bg
        self.content = None
        self._crear_panel_lector_agua()

    def _crear_panel_lector_agua(self):
        self.ventana.title("Lector de Agua - Municipalidad")
        try:
            self.ventana.state('zoomed')
        except:
            pass

        _add_header_footer(self.ventana, "💧 Lector de Agua", self.usuario, self.header_bg)

        menu_bar = tk.Menu(self.ventana)
        self.ventana.config(menu=menu_bar)

        menu_agua = tk.Menu(menu_bar, tearoff=0)
        menu_agua.add_command(label="Lectura de agua", command=self._abrir_panel_lectura)
        menu_bar.add_cascade(label="Agua", menu=menu_agua)

        menu_salir = tk.Menu(menu_bar, tearoff=0)
        menu_salir.add_command(label="Cerrar sesión", command=self.cerrar_sesion)
        menu_salir.add_command(label="Salir", command=self.ventana.quit)
        menu_bar.add_cascade(label="Salir", menu=menu_salir)

        self.content = tk.Frame(self.ventana, bg="#F2F5F9")
        self.content.pack(fill="both", expand=True)

        self.bienvenida4()

    def bienvenida4(self):
        for w in self.content.winfo_children():
            w.destroy()
        tk.Label(self.content, text="Bienvenido al Panel del lector de agua",
                 font=("Segoe UI", 24, "bold"), bg="#F2F5F9", fg="#2D3A4A").pack(pady=60)
        tk.Label(self.content, text=f"Usuario activo: 👤 {self.usuario}",
                 font=("Segoe UI", 12), bg="#F2F5F9", fg="#58606A").pack(pady=(0, 20))

        tk.Label(self.content, text="Use el submenú para acceder a las opciones del lector de agua",
                 font=("Segoe UI", 12), bg="#F2F5F9", fg="#58606A").pack()


    def cerrar_sesion(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
        self.app.crear_login()

    def _abrir_panel_lectura(self):
        for w in self.content.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.configure(
            "Big.TNotebook",
            background="#FFFFFF",
            padding=10
        )
        style.configure(
            "Big.TNotebook.Tab",
            font=("Segoe UI", 12, "bold"),
            padding=[10, 8]
        )
        style.map(
            "Big.TNotebook.Tab",
            background=[("selected", "#DCE9FF")],
            foreground=[("selected", "#1B3556")]
        )

        notebook = ttk.Notebook(self.content, style="Big.TNotebook")
        notebook.pack(fill="both", expand=True, padx=18, pady=18)

        generar_tab = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(generar_tab, text="📊 Generar lectura")
        self._build_generar_lectura_tab(generar_tab)

    def _build_generar_lectura_tab(self, parent):
        pad = {"padx": 12, "pady": 8}
        frame = tk.Frame(parent, bg="#FFFFFF")
        frame.pack(padx=20, pady=20, anchor="n")

        titulo = tk.Label(frame, text="📊 Generar Lectura de Agua",
                          font=("Segoe UI", 16, "bold"), bg="#FFFFFF", fg="#2D3A4A")
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        tk.Label(frame, text="Elegir usuario (con contador):", bg="#FFFFFF",
                 font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", **pad)
        self.lista_usuarios_cb = ttk.Combobox(
            frame,
            values=self._obtener_usuarios_con_contador(),
            state="readonly",
            width=50,
            font=("Segoe UI", 10)
        )
        self.lista_usuarios_cb.grid(row=1, column=1, **pad)
        if self.lista_usuarios_cb['values']:
            self.lista_usuarios_cb.current(0)

        tk.Label(frame, text="Consumo (m³):", bg="#FFFFFF", font=("Segoe UI", 11)).grid(
            row=2, column=0, sticky="w", **pad)
        self.consumo_entry = ttk.Entry(frame, width=50, font=("Segoe UI", 10))
        self.consumo_entry.grid(row=2, column=1, sticky="w", **pad)

        tk.Label(frame, text="Fecha (auto):", bg="#FFFFFF", font=("Segoe UI", 11)).grid(
            row=3, column=0, sticky="w", **pad)
        self.fecha_label = tk.Label(frame,width=60,
                                    text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    bg="#FFFFFF",
                                    font=("Segoe UI", 10))
        self.fecha_label.grid(row=3, column=1, sticky="w", **pad)

        btns = tk.Frame(frame, bg="#FFFFFF")
        btns.grid(row=4, column=0, columnspan=2, pady=16)

        style = ttk.Style()
        style.configure("Big.TButton", font=("Segoe UI", 11, "bold"), padding=(12, 6))

        ttk.Button(btns, text="🧹 Limpiar", style="Big.TButton",
                   command=self._limpiar_form_lectura).pack(side="left", padx=8)
        ttk.Button(btns, text="💾 Guardar", style="Big.TButton",
                   command=self._guardar_lectura).pack(side="left", padx=8)

    def _obtener_usuarios_con_contador(self):
        with DatabaseManager.connect() as conn:
            rows = conn.execute("SELECT id, nombre, dpi FROM usuarios_registrados WHERE contador = 'Sí' OR contador = 'si' ORDER BY nombre COLLATE NOCASE").fetchall()
        vals = [f"{r['id']} - {r['nombre']} ({r['dpi']})" for r in rows]
        return vals

    def _limpiar_form_lectura(self):
        self.consumo_entry.delete(0, tk.END)
        self.fecha_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.lista_usuarios_cb['values'] = self._obtener_usuarios_con_contador()
        if self.lista_usuarios_cb['values']:
            self.lista_usuarios_cb.current(0)

    def _guardar_lectura(self):
        sel = self.lista_usuarios_cb.get().strip()
        consumo_text = self.consumo_entry.get().strip()
        if not sel:
            messagebox.showwarning("Validación", "Seleccione un usuario con contador.")
            return
        if not consumo_text:
            messagebox.showwarning("Validación", "Ingrese el consumo en m³.")
            return
        try:
            consumo = float(consumo_text)
            if consumo < 0:
                raise ValueError
        except:
            messagebox.showwarning("Validación", "El consumo debe ser un número válido (ej. 12.5).")
            return

        try:
            usuario_id = int(sel.split(" - ")[0])
        except:
            messagebox.showerror("Error", "Formato de usuario inválido.")
            return

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = consumo * LectorAguaPanel.TARIFA_POR_M3

        try:
            with DatabaseManager.connect() as conn:
                conn.execute("""
                    INSERT INTO lecturas_agua (usuario_id, consumo_m3, total_pagar, fecha, pagado)
                    VALUES (?, ?, ?, ?, 0)
                """, (usuario_id, consumo, total, fecha))
                conn.commit()
            messagebox.showinfo("Lectura", f"Lectura guardada.\nUsuario ID: {usuario_id}\nConsumo: {consumo:.2f} m³\nTotal: Q{total:.2f}")
            self._limpiar_form_lectura()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la lectura: {str(e)}")
# Programa principal
if __name__ == "__main__":
    DatabaseManager.init_tables()
    inicializar_usuarios()
    root = tk.Tk()
    app = Graficos(root)
    root.mainloop()