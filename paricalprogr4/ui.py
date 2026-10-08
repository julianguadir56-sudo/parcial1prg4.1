"""Módulo UI: interacción con el usuario por línea de comandos."""


def pedir_texto(mensaje):
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("  El campo no puede estar vacío.")


def pedir_entero_positivo(mensaje):
    while True:
        try:
            numero = int(input(mensaje))
            if numero > 0:
                return numero
        except ValueError:
            pass
        print("  Ingresa un número entero mayor que 0.")


def pedir_consulta():
    """Pide al usuario los 4 datos de la consulta."""
    print("\n=== Consulta de propiedades edáficas ===")
    return {
        "departamento": pedir_texto("Departamento: "),
        "municipio": pedir_texto("Municipio: "),
        "cultivo": pedir_texto("Cultivo: "),
        "n_registros": pedir_entero_positivo("Número de registros a consultar: "),
    }


def mostrar_tabla(resumen):
    """Imprime el DataFrame resumen como tabla."""
    if resumen.empty:
        print("\nNo se encontraron registros con esos datos.")
        return
    print("\n" + resumen.to_string(index=False))


def preguntar_continuar():
    return input("\n¿Hacer otra consulta? (s/n): ").strip().lower() == "s"
