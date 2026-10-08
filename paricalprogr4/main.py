"""Punto de entrada: conecta la UI con el módulo API."""
import api
import ui

RUTA_EXCEL = "resultado_laboratorio_suelo.xlsx"

def main():
    print("Cargando y limpiando datos (puede tardar unos segundos)...")
    df = api.cargar_datos(RUTA_EXCEL)
    seguir = True
    while seguir:
        consulta = ui.pedir_consulta()
        filtrado = api.filtrar(
            df,
            consulta["departamento"],
            consulta["municipio"],
            consulta["cultivo"],
            consulta["n_registros"],
        )
        ui.mostrar_tabla(api.calcular_medianas(filtrado, df) if not filtrado.empty else filtrado)
        seguir = ui.preguntar_continuar()


if __name__ == "__main__":
    main()
