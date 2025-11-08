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

        tk.Button(root, text="Iniciar Sesión", width=21, command=self.login).pack(pady=10)

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
                AdminApp(root)
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
        tk.Label(self.content, text="Registrar Cliente", font=("Arial", 14, "bold"), bg="#EFEFEF").pack(pady=10)

        frm = tk.Frame(self.content, bg="#EFEFEF")
        frm.pack(pady=5)

        tk.Label(frm, text="Nombre: ", bg="#EFEFEF").grid(row=0, column=0, sticky="e")
        e_nombre = ttk.Entry(frm, width=40); e_nombre.grid(row=0, column=1, pady=4)

        tk.Label(frm, text="DPI: ", bg="#EFEFEF").grid(row=1, column=0, sticky="e")
        e_dpi = ttk.Entry(frm, width=40); e_dpi.grid(row=1, column=1, pady=4)

        tk.Label(frm, text="Dirección: ", bg="#EFEFEF").grid(row=2, column=0, sticky="e")
        e_direccion = ttk.Entry(frm, width=40); e_direccion.grid(row=2, column=1, pady=4)

        tk.Label(frm, text="Número de casa: ", bg="#EFEFEF").grid(row=3, column=0, sticky="e")
        e_casa = ttk.Entry(frm, width=40); e_casa.grid(row=3, column=1, pady=4)

        tk.Label(frm, text="Tipo de servicio: ", bg="#EFEFEF").grid(row=4, column=0, sticky="e")
        cb_tipo = ttk.Combobox(frm, values=["fijo", "contador"], width=37, state="readonly"); cb_tipo.grid(row=4, column=1, pady=4)
        cb_tipo.current(0)

        def guardar_cliente():
            nombre = e_nombre.get().strip()
            dpi = e_dpi.get().strip()
            direccion = e_direccion.get().strip()
            numero_casa = e_casa.get().strip()
            tipo = cb_tipo.get()
            if not nombre or not numero_casa or not tipo:
                messagebox.showwarning("Atención", "Complete los campos obligatorios (Nombre y Número de casa).")
                return
            with DatabaseManager.connect() as conn:
                # por cada cliente nuevo, ultimo_pago se inicializa al día de registro (no hay deuda aún)
                conn.execute("""
                    INSERT INTO clientes (nombre, dpi, direccion, numero_casa, tipo, total_mes, ultimo_pago, mora)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nombre, dpi, direccion, numero_casa, tipo, 12.0 if tipo == "fijo" else 0.0, datetime.now().strftime("%Y-%m-%d") if tipo == "fijo" else None, 0.0))
                conn.commit()
            messagebox.showinfo("Éxito", f"Cliente '{nombre}' registrado.")
            e_nombre.delete(0, tk.END); e_dpi.delete(0, tk.END); e_direccion.delete(0, tk.END); e_casa.delete(0, tk.END)
            cb_tipo.current(0)

        ttk.Button(self.content, text="Guardar Cliente", command=guardar_cliente).pack(pady=10)

    def pantalla_listar_clientes(self):
        self.limpiar_content()
        tk.Label(self.content, text="Clientes Registrados", font=("Arial", 14, "bold"), bg="#EFEFEF").pack(pady=10)

        tree = ttk.Treeview(self.content, columns=("ID","Nombre","Tipo","Casa","DPI","Mora","Último Pago"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        with DatabaseManager.connect() as conn:
            for r in conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall():
                tree.insert("", tk.END, values=(r["id"], r["nombre"], r["tipo"], r["numero_casa"], r["dpi"] or "", f"Q{r['mora']:.2f}", r["ultimo_pago"] or "-"))

    def pantalla_cobro(self):
        self.limpiar_content()
        tk.Label(self.content, text="Cobro de Agua (Buscar usuario para cobrar)", font=("Arial", 14, "bold"), bg="#EFEFEF").pack(pady=8)

        frm = tk.Frame(self.content, bg="#EFEFEF")
        frm.pack(pady=6)
        tk.Label(frm, text="Nombre o DPI:", bg="#EFEFEF").grid(row=0, column=0, padx=5, pady=5)
        e_buscar = ttk.Entry(frm, width=40); e_buscar.grid(row=0, column=1, padx=5, pady=5)
        btn_buscar = ttk.Button(frm, text="Buscar", command=lambda: self.buscar_para_cobro(e_buscar.get().strip(), resultado_frame)); btn_buscar.grid(row=0, column=2, padx=5)

        resultado_frame = tk.Frame(self.content, bg="#EFEFEF")
        resultado_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def buscar_para_cobro(self, valor, contenedor):
            for w in contenedor.winfo_children():
                w.destroy()
            if not valor:
                messagebox.showwarning("Atención", "Ingrese nombre o DPI.")
                return
            with DatabaseManager.connect() as conn:
                fila = conn.execute("SELECT * FROM clientes WHERE nombre=? OR dpi=?", (valor, valor)).fetchone()
                if not fila:
                    messagebox.showerror("No encontrado", "Cliente no registrado.")
                    return

                tk.Label(contenedor, text=f"Nombre: {fila['nombre']}", bg="#EFEFEF").pack(anchor="w")
                tk.Label(contenedor, text=f"Dirección: {fila['direccion'] or '-'}", bg="#EFEFEF").pack(anchor="w")
                tk.Label(contenedor, text=f"Número casa: {fila['numero_casa']}", bg="#EFEFEF").pack(anchor="w")
                tk.Label(contenedor, text=f"Tipo: {fila['tipo']}", bg="#EFEFEF").pack(anchor="w")

                if fila["tipo"] == "fijo":
                    # calcular meses y mora
                    calc = calcular_mora_fijo(fila)
                    tk.Label(contenedor, text=f"Meses adeudados: {calc['meses']}", bg="#EFEFEF").pack(anchor="w")
                    tk.Label(contenedor, text=f"Mora acumulada: Q{calc['mora']:.2f}", bg="#EFEFEF").pack(anchor="w")
                    tk.Label(contenedor, text=f"Total a pagar: Q{calc['total_deuda']:.2f}", bg="#EFEFEF").pack(
                        anchor="w")

                    def confirmar_pago_fijo():
                        with DatabaseManager.connect() as conn2:
                            # actualizar ultimo_pago a hoy y poner mora=0
                            conn2.execute("UPDATE clientes SET ultimo_pago=?, mora=? WHERE id=?",
                                          (datetime.now().strftime("%Y-%m-%d"), 0.0, fila["id"]))
                            conn2.commit()
                        messagebox.showinfo("Pago",
                                            f"Pago de Q{calc['total_deuda']:.2f} registrado para {fila['nombre']}.")
                        for w in contenedor.winfo_children():
                            w.destroy()

                    ttk.Button(contenedor, text="Confirmar Pago", command=confirmar_pago_fijo).pack(pady=8)
                    ttk.Button(contenedor, text="Regresar",
                               command=lambda: [w.destroy() for w in contenedor.winfo_children()]).pack()
                    return

                lecturas = conn.execute("SELECT * FROM lecturas WHERE cliente_id=? AND pagado=0 ORDER BY fecha DESC",
                                        (fila["id"],)).fetchall()
                if not lecturas:
                    tk.Label(contenedor, text="No hay lecturas pendientes para este cliente.", bg="#EFEFEF").pack(
                        anchor="w")
                    ttk.Button(contenedor, text="Regresar",
                               command=lambda: [w.destroy() for w in contenedor.winfo_children()]).pack(pady=6)
                    return

                total_sum = 0.0
                detalles_frame = tk.Frame(contenedor, bg="#EFEFEF")
                detalles_frame.pack(anchor="w", pady=6)
                tk.Label(detalles_frame, text="Lecturas pendientes:", bg="#EFEFEF",
                         font=("Arial", 11, "underline")).pack(anchor="w")
                for l in lecturas:
                    calc = calcular_mora_lectura(l)
                    total_sum += calc["total"]
                    tk.Label(detalles_frame,
                             text=f"- Fecha: {l['fecha']} | Consumo: {l['consumo']} | Base: Q{l['total_pagar']:.2f} | Mora: Q{calc['mora']:.2f} | Total: Q{calc['total']:.2f}",
                             bg="#EFEFEF").pack(anchor="w")

                tk.Label(contenedor, text=f"Total a pagar (todas lecturas): Q{total_sum:.2f}", bg="#EFEFEF",
                         font=("Arial", 12, "bold")).pack(anchor="w", pady=8)

                def confirmar_pago_contador():
                    with DatabaseManager.connect() as conn2:
                        for l in lecturas:
                            conn2.execute("UPDATE lecturas SET pagado=1, fecha_pago=? WHERE id=?",
                                          (datetime.now().strftime("%Y-%m-%d"), l["id"]))
                        conn2.commit()
                    messagebox.showinfo("Pago", f"Pago de Q{total_sum:.2f} registrado para {fila['nombre']}.")
                    for w in contenedor.winfo_children():
                        w.destroy()

                ttk.Button(contenedor, text="Confirmar Pago (todas lecturas)", command=confirmar_pago_contador).pack(
                    pady=6)
                ttk.Button(contenedor, text="Regresar",
                           command=lambda: [w.destroy() for w in contenedor.winfo_children()]).pack(pady=4)

        def cerrar(self):
            self.root.destroy()

class LectorApp:
    def __init__(self, root):
        self.root = root
        root.title("Lector de Agua - Registrar Lecturas")
        root.geometry("600x420")
        root.resizable(False, False)

        tk.Label(root, text="Registrar Lectura (solo usuarios con contador)", font=("Arial", 13, "bold")).pack(pady=10)

        frm = tk.Frame(root)
        frm.pack(pady=8)

        tk.Label(frm, text="Usuario (seleccione):").grid(row=0, column=0, sticky="e", padx=5, pady=6)
        self.cb_usuarios = ttk.Combobox(frm, width=45, state="readonly")
        self.cb_usuarios.grid(row=0, column=1, padx=5, pady=6)

        tk.Label(frm, text="Consumo (galones):").grid(row=1, column=0, sticky="e", padx=5, pady=6)
        self.e_consumo = ttk.Entry(frm, width=30);
        self.e_consumo.grid(row=1, column=1, padx=5, pady=6)

        tk.Label(frm, text="Fecha (YYYY-MM-DD):").grid(row=2, column=0, sticky="e", padx=5, pady=6)
        self.e_fecha = ttk.Entry(frm, width=30);
        self.e_fecha.grid(row=2, column=1, padx=5, pady=6)
        self.e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Button(root, text="Cargar usuarios (contador)", command=self.cargar_usuarios).pack(pady=6)
        ttk.Button(root, text="Guardar Lectura", command=self.guardar_lectura).pack(pady=6)
        ttk.Button(root, text="Cerrar sesión", command=self.root.destroy).pack(pady=10)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        with DatabaseManager.connect() as conn:
            filas = conn.execute(
                "SELECT id, nombre, numero_casa FROM clientes WHERE tipo='contador' ORDER BY nombre").fetchall()
            items = [f"{r['id']} - {r['nombre']} ({r['numero_casa']})" for r in filas]
        self.cb_usuarios["values"] = items
        if items:
            self.cb_usuarios.current(0)

    def guardar_lectura(self):
        sel = self.cb_usuarios.get()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un usuario válido.")
            return
        try:
            cliente_id = int(sel.split(" - ")[0])
        except Exception:
            messagebox.showerror("Error", "Selección inválida.")
            return
        consumo_txt = self.e_consumo.get().strip()
        fecha_txt = self.e_fecha.get().strip()
        if not consumo_txt:
            messagebox.showwarning("Atención", "Ingrese consumo.")
            return
        try:
            consumo = float(consumo_txt)
        except ValueError:
            messagebox.showerror("Error", "El consumo debe ser un número.")
            return
        tarifa_galon = 1.0
        total = consumo * tarifa_galon
        with DatabaseManager.connect() as conn:
            conn.execute(
                "INSERT INTO lecturas (cliente_id, consumo, total_pagar, fecha, pagado) VALUES (?, ?, ?, ?, 0)",
                (cliente_id, consumo, total, fecha_txt))
            conn.commit()
        messagebox.showinfo("Éxito", f"Lectura guardada: Consumo={consumo} | Total Q{total:.2f}")
        self.e_consumo.delete(0, tk.END)
        self.e_fecha.delete(0, tk.END)
        self.e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))

if __name__ == "__main__":
    DatabaseManager.setup()
    inicializar_credenciales()
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()