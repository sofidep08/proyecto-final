def menu_principal()
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
