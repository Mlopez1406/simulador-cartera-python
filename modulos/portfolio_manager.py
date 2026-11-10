def comprar_accion(cartera, ticker, cantidad, precio_unitario):
    """
    Ejecuta la compra de acciones actualizando el saldo y el precio medio ponderado de compra (PMPC).
    """
    ticker = ticker.upper()
    coste_total = cantidad * precio_unitario

    if cartera["saldo_euros"] < coste_total:
        return False, f"Saldo insuficiente. Requieres {coste_total:.2f} € y dispones de {cartera['saldo_euros']:.2f} €."

    # Descontar el importe total del saldo libre
    cartera["saldo_euros"] -= coste_total

    # Actualizar la cartera de acciones
    posiciones = cartera["acciones"]
    if ticker in posiciones:
        cant_prev = posiciones[ticker]["cantidad"]
        pmpc_prev = posiciones[ticker]["precio_medio"]
        
        # Fórmula del Precio Medio Ponderado de Compra (PMPC)
        nueva_cant = cant_prev + cantidad
        nuevo_pmpc = ((cant_prev * pmpc_prev) + coste_total) / nueva_cant
        
        posiciones[ticker]["cantidad"] = nueva_cant
        posiciones[ticker]["precio_medio"] = round(nuevo_pmpc, 2)
    else:
        posiciones[ticker] = {
            "cantidad": cantidad,
            "precio_medio": round(precio_unitario, 2)
        }

    return True, f"Compra realizada con éxito: {cantidad} acciones de {ticker} a {precio_unitario:.2f} €."

def vender_accion(cartera, ticker, cantidad, precio_unitario):
    """
    Ejecuta la venta de acciones ingresando el importe y reduciendo la posición.
    """
    ticker = ticker.upper()
    posiciones = cartera["acciones"]

    if ticker not in posiciones or posiciones[ticker]["cantidad"] < cantidad:
        cant_disponible = posiciones.get(ticker, {}).get("cantidad", 0)
        return False, f"No tienes suficientes acciones de {ticker}. Dispones de {cant_disponible}."

    ingreso_total = cantidad * precio_unitario
    cartera["saldo_euros"] += ingreso_total

    posiciones[ticker]["cantidad"] -= cantidad
    # Si nos quedamos sin acciones de esa empresa, la eliminamos de la cartera activa
    if posiciones[ticker]["cantidad"] == 0:
        del posiciones[ticker]

    return True, f"Venta realizada con éxito: {cantidad} acciones de {ticker} a {precio_unitario:.2f} €."

def calcular_resumen(cartera, obtener_precio_func):
    """
    Calcula la valoración liquidativa total de la cartera y la ganancia/pérdida no realizada.
    """
    efectivo = cartera["saldo_euros"]
    valor_inversiones = 0.0
    coste_inversion_total = 0.0
    detalles = []

    for ticker, datos in cartera["acciones"].items():
        cant = datos["cantidad"]
        pmpc = datos["precio_medio"]
        precio_actual, origen = obtener_precio_func(ticker)

        valor_mercado = cant * precio_actual
        coste_inicial = cant * pmpc
        pnl_euros = valor_mercado - coste_inicial
        pnl_porcentaje = ((precio_actual - pmpc) / pmpc) * 100 if pmpc > 0 else 0.0

        valor_inversiones += valor_mercado
        coste_inversion_total += coste_inicial

        detalles.append({
            "ticker": ticker,
            "cantidad": cant,
            "pmpc": pmpc,
            "precio_actual": precio_actual,
            "valor_mercado": round(valor_mercado, 2),
            "pnl_euros": round(pnl_euros, 2),
            "pnl_pct": round(pnl_porcentaje, 2),
            "origen": origen
        })

    total_cuenta = efectivo + valor_inversiones
    pnl_global_euros = valor_inversiones - coste_inversion_total
    pnl_global_pct = ((valor_inversiones - coste_inversion_total) / coste_inversion_total * 100) if coste_inversion_total > 0 else 0.0

    return {
        "efectivo": round(efectivo, 2),
        "valor_inversiones": round(valor_inversiones, 2),
        "total_cuenta": round(total_cuenta, 2),
        "pnl_global_euros": round(pnl_global_euros, 2),
        "pnl_global_pct": round(pnl_global_pct, 2),
        "posiciones": detalles
    }
    
def ingresar_saldo(cartera, cantidad):
    """
    Añade dinero al saldo disponible en efectivo del usuario.
    """
    if cantidad <= 0:
        return False, "La cantidad a ingresar debe ser mayor que 0 €."
    
    cartera["saldo_euros"] += cantidad
    return True, f"Ingreso realizado con éxito. Nuevo saldo disponible: {cartera['saldo_euros']:.2f} €."