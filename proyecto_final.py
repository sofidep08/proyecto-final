class Usuario:
    def __init__(self):
        self.cargar_usuario()
    def cargar_usuario(self):
        try:
            with open('usuario.txt', 'r', encoding="utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if linea:
                        direccion, nombre, numCasa, dpi, nit, contador = linea.split(":")
                        AgregarUsuario.usuarios[direccion] = {
                            "Nombre": nombre,
                            "NumCasa": numCasa,
                            "DPI": dpi,
                            "NIT": nit,
                            "Contador": contador
                        }
            print("usuarios importados desde usuario.txt")
        except FileNotFoundError:
            print("El archivo usuario aun no existe, se creara automaticamente después de guardar")


class AgregarUsuario:
    usuarios ={}
    def __init__(self, direccion, nombre, numCasa, dpi, nit, contador):
        self.direccion = direccion
        self.nombre = nombre
        self.numCasa = numCasa
        self.dpi = dpi
        self.nit = nit
        self.contador = contador
        usuarios[self.direccion] = {
            "Nombre": nombre,
            "NumCasa": numCasa,
            "DPI": dpi,
            "NIT": nit,
            "Contador": contador
        }
        self.guardar_usuario()
        print("Se guardo el usuario con exito")

    def guardar_usuario (self):
        with open('usuario.txt', 'w', encoding="utf-8") as archivo:
            for direccion, persona in AgregarUsuario.usuarios.items():
                archivo.write(f"Direccion: {direccion}| Nombre:{persona['Nombre']}"
                f" | Numero de casa:{persona['NumCasa']} | DPI:{persona['DPI']} | NIT:{persona['NIT']}"
                f"| Contador:{persona['Contador']}")