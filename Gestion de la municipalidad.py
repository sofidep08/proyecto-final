class Empleados:
    def __init__(self):
        self.empleados = {}
        self.cargar_empleados()

    def cargar_empleados(self):
        try:
            with open("empleados.txt", "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if linea:
                        usuario, nombre, contrasenia = linea.split(":")
                        self.empleados[usuario] = {
                            "Nombre": nombre,
                            "Contraseña" : contrasenia
                        }
            if not self.empleados:
                self.crear_empleados_defecto()
            print("Empleados importados desde empleados.txt")
        except FileNotFoundError:
            print("No existe el archivo empleados.txt, se crearán dos empleados por defecto.")
            self.crear_empleados_defecto()
            self.guardar_empleados()

    def crear_empleados_defecto(self):
                self.empleados = {
                    "empleado1": {"Nombre": "Victor Pérez","Contraseña": "victor123"},
                    "empleado2": {"Nombre": "Luis Gonzalez", "Contraseña": "luis123"}
                }
    def guardar_empleados(self):
        with open("empleados.txt", "w", encoding="utf-8") as archivo:
            for usuario, datos in self.empleados.items():
                archivo.write(f"{usuario}:{datos['Nombre']}\n")
        print("Empleados guardados correctamente")

    def agregar_empleado(self):
        if len(self.empleados)  >= 2:
            print(f"Ya existe 2 empleados contratados. No se puede agregar a nadie más. ")
            return
        usuario = input("Ingrese el nombre del usuario:")
        nombre = input("Ingrese el nombre completo:")
        contrasenia = input("Ingrese la contraseña:")
        self.empleados[usuario] = {"Nombre": nombre, "Contraseña": contrasenia}
        self.guardar_empleados()
        print(f"Empleado '{usuario}' agregar correctamente.")

    def mostrar_empleado(self):
        print("\n---EMPLEADOS CONTRATADOS---")
        for usuario, datos in self.empleados.items():
            print(f"Usuario: {usuario}| Nombre{datos['Nombre']}")

    def validar_login(self, usuario, contrasenia):
        if usuario in self.empleados and self.empleados[usuario]["Contraseña"]== contrasenia:
            return True
        return False

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



