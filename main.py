from modulos.file_handler import cargar_cartera, guardar_cartera, registrar_transaccion, leer_historial
from modulos.api_client import obtener_precio_actual
from modulos.portfolio_manager import comprar_accion, vender_accion, calcular_resumen, ingresar_saldo

def mostrar_menu():
    print("\n" + "="*45)
    print("   SIMULADOR DE TRADING VIRTUAL (PAPER TRADING)")
    print("="*45)
    print(" 1. Ver estado de la cartera y P&L")
    print(" 2. Consultar cotización en tiempo real")
    print(" 3. Comprar acciones")
    print(" 4. Vender acciones")
    print(" 5. Ingresar saldo a la cuenta")
    print(" 6. Ver historial de transacciones (CSV)")
    print(" 7. Guardar y Salir")
    print("="*45)

def ejecutar():
    cartera = cargar_cartera()
    print("\n Sesión iniciada con éxito.")

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción (1-7): ").strip()

        if opcion == "1":
            resumen = calcular_resumen(cartera, obtener_precio_actual)
            print(f"\n--- ESTADO DE LA CUENTA ---")
            print(f"Efectivo Disponible:  {resumen['efectivo']:.2f} €")
            print(f"Valor en Acciones:    {resumen['valor_inversiones']:.2f} €")
            print(f"VALOR TOTAL CUENTA:   {resumen['total_cuenta']:.2f} €")
            print(f"P&L No Realizada:     {resumen['pnl_global_euros']:+.2f} € ({resumen['pnl_global_pct']:+.2f}%)")
            
            if resumen["posiciones"]:
                print("\nPOSICIONES EN CARTERA:")
                print(f"{'TICKER':<8} {'CANT':<6} {'PMPC (€)':<10} {'ACTUAL (€)':<12} {'VALOR (€)':<10} {'P&L (€)':<10} {'P&L (%)':<8}")
                print("-" * 70)
                for pos in resumen["posiciones"]:
                    print(f"{pos['ticker']:<8} {pos['cantidad']:<6} {pos['pmpc']:<10.2f} {pos['precio_actual']:<12.2f} {pos['valor_mercado']:<10.2f} {pos['pnl_euros']:<+10.2f} {pos['pnl_pct']:<+8.2f}%")
            else:
                print("\nNo tienes acciones en propiedad actualmente.")

        elif opcion == "2":
            ticker = input("Introduce el Ticker (ej. AAPL, MSFT, TSLA): ").strip().upper()
            if ticker:
                precio, fuente = obtener_precio_actual(ticker)
                print(f"\n Cotización de {ticker}: {precio:.2f} € (Fuente: {fuente})")

        elif opcion == "3":
            ticker = input("Ticker de la empresa a COMPRAR: ").strip().upper()
            if not ticker:
                print(" Error: Debes introducir un Ticker válido.")
                continue
            try:
                cant = int(input("Cantidad de acciones: "))
                if cant <= 0:
                    print(" La cantidad debe ser mayor que 0.")
                    continue
                precio, fuente = obtener_precio_actual(ticker)
                print(f"Precio actual de {ticker}: {precio:.2f} € ({fuente})")
                confirmar = input(f"¿Confirmar compra por un total de {cant * precio:.2f} €? (s/n): ").strip().lower()
                if confirmar == 's':
                    exito, msj = comprar_accion(cartera, ticker, cant, precio)
                    print(f"\n{msj}")
                    if exito:
                        guardar_cartera(cartera)
                        registrar_transaccion("COMPRA", ticker, cant, precio)
            except ValueError:
                print(" Error: Introduce un número entero válido para la cantidad.")

        elif opcion == "4":
            ticker = input("Ticker de la empresa a VENDER: ").strip().upper()
            if not ticker:
                print(" Error: Debes introducir un Ticker válido.")
                continue
            try:
                cant = int(input("Cantidad de acciones a vender: "))
                if cant <= 0:
                    print(" La cantidad debe ser mayor que 0.")
                    continue
                precio, fuente = obtener_precio_actual(ticker)
                exito, msj = vender_accion(cartera, ticker, cant, precio)
                print(f"\n{msj}")
                if exito:
                    guardar_cartera(cartera)
                    registrar_transaccion("VENTA", ticker, cant, precio)
            except ValueError:
                print(" Error: Introduce un número entero válido para la cantidad.")

        elif opcion == "5":
            try:
                monto = float(input("Introduce la cantidad de dinero a ingresar (€): "))
                exito, msj = ingresar_saldo(cartera, monto)
                print(f"\n{msj}")
                if exito:
                    guardar_cartera(cartera)
                    registrar_transaccion("INGRESO", "CASH", 1, monto)
            except ValueError:
                print(" Error: Introduce un número decimal/entero válido para el importe.")

        elif opcion == "6":
            historial = leer_historial()
            print("\n--- HISTORIAL DE TRANSACCIONES ---")
            if not historial:
                print("No hay operaciones registradas aún.")
            else:
                print(f"{'FECHA':<20} {'TIPO':<8} {'TICKER':<8} {'CANT':<6} {'PRECIO (€)':<12} {'TOTAL (€)':<10}")
                print("-" * 68)
                for reg in historial:
                    fecha = reg.get('fecha_hora', '-')
                    op = reg.get('operacion', '-')
                    tick = reg.get('ticker', '-')
                    cant = reg.get('cantidad', '0')
                    precio = float(reg.get('precio_unitario', 0))
                    total = float(reg.get('total', 0))
                    print(f"{fecha:<20} {op:<8} {tick:<8} {cant:<6} {precio:<12.2f} {total:<10.2f}")

        elif opcion == "7":
            guardar_cartera(cartera)
            print("\n Cartera guardada correctamente. ¡Hasta pronto!")
            break
        else:
            print(" Opción no válida. Por favor, elige un número del 1 al 7.")

if __name__ == "__main__":
    ejecutar()