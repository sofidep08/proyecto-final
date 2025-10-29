import tkinter as tk
from tkinter import messagebox

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Sistema Municipal")

# Maximizar ventana (ocupa toda la pantalla)
ventana.state('zoomed')  # En Windows
# ventana.attributes('-zoomed', True)  # En Linux (opcional)

# Crear barra de menú
menu_bar = tk.Menu(ventana)
ventana.config(menu=menu_bar)

# ===== MENÚ USUARIOS =====
menu_usuarios = tk.Menu(menu_bar, tearoff=0)
menu_usuarios.add_command(label="Nuevo", command=lambda: messagebox.showinfo("Usuarios", "Registrar nuevo usuario"))
menu_usuarios.add_command(label="Buscar", command=lambda: messagebox.showinfo("Usuarios", "Buscar usuario existente"))
menu_usuarios.add_command(label="Ver todos", command=lambda: messagebox.showinfo("Usuarios", "Listado de todos los usuarios"))
menu_bar.add_cascade(label="Usuarios", menu=menu_usuarios)

# ===== MENÚ BOLETA DE ORNATO =====
menu_ornato = tk.Menu(menu_bar, tearoff=0)
menu_ornato.add_command(label="Nuevo", command=lambda: messagebox.showinfo("Boleta de Ornato", "Crear nueva boleta"))
menu_ornato.add_command(label="Buscar", command=lambda: messagebox.showinfo("Boleta de Ornato", "Buscar boleta existente"))
menu_bar.add_cascade(label="Boleta de Ornato", menu=menu_ornato)

# ===== MENÚ SERVICIO DE AGUA =====
menu_agua = tk.Menu(menu_bar, tearoff=0)
menu_agua.add_command(label="Pago", command=lambda: messagebox.showinfo("Servicio de Agua", "Registrar pago de servicio"))
menu_agua.add_command(label="Buscar", command=lambda: messagebox.showinfo("Servicio de Agua", "Buscar registro de servicio"))
menu_bar.add_cascade(label="Servicio de Agua", menu=menu_agua)

# ===== MENÚ MULTAS =====
menu_multas = tk.Menu(menu_bar, tearoff=0)
menu_multas.add_command(label="Pago", command=lambda: messagebox.showinfo("Multas", "Registrar pago de multa"))
menu_multas.add_command(label="Buscar", command=lambda: messagebox.showinfo("Multas", "Buscar multa registrada"))
menu_bar.add_cascade(label="Multas", menu=menu_multas)

# ===== MENÚ AYUDA =====
menu_ayuda = tk.Menu(menu_bar, tearoff=0)
menu_ayuda.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Acerca de", "Sistema Municipal\nCreado por Ing. Jorge Tello"))
menu_bar.add_cascade(label="Ayuda", menu=menu_ayuda)

# ===== CONTENIDO DE LA VENTANA =====
etiqueta = tk.Label(ventana, text="Bienvenido al Sistema Municipal", font=("Arial", 18))
etiqueta.pack(pady=50)

entrada = tk.Entry(ventana, font=("Arial", 14))
entrada.pack(pady=10, ipadx=100, ipady=5)

def saludar():
    nombre = entrada.get()
    etiqueta.config(text=f"Hola, {nombre}!")

def limpiar():
    entrada.delete(0, tk.END)
    etiqueta.config(text="Bienvenido al Sistema Municipal")

# Botones principales
boton_saludar = tk.Button(ventana, text="Saludar", command=saludar, font=("Arial", 12), width=15)
boton_saludar.pack(pady=10)

boton_limpiar = tk.Button(ventana, text="Limpiar", command=limpiar, font=("Arial", 12), width=15)
boton_limpiar.pack(pady=5)

boton_salir = tk.Button(ventana, text="Salir", command=ventana.quit, font=("Arial", 12), width=15)
boton_salir.pack(pady=5)

# Ejecutar ventana
ventana.mainloop()