import json
import csv
import os
from datetime import datetime

RUTA_CARTERA = "datos/cartera.json"
RUTA_TRANSACCIONES = "datos/transacciones.csv"

def asegurar_directorio():
    """Crea la carpeta datos/ si no existe."""
    if not os.path.exists("datos"):
        os.makedirs("datos")

def cargar_cartera(ruta=RUTA_CARTERA):
    """Carga la cartera desde JSON. Si no existe, crea una nueva con 10.000 €."""
    asegurar_directorio()
    if not os.path.exists(ruta):
        cartera_inicial = {"saldo_euros": 10000.0, "acciones": {}}
        guardar_cartera(cartera_inicial, ruta)
        return cartera_inicial
    
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print(" Error al leer 'cartera.json'. Se cargará un estado por defecto.")
        return {"saldo_euros": 10000.0, "acciones": {}}

def guardar_cartera(datos_cartera, ruta=RUTA_CARTERA):
    """Guarda el diccionario de cartera en el fichero JSON."""
    asegurar_directorio()
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos_cartera, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        print(f" Error al guardar la cartera: {e}")
        return False

def registrar_transaccion(operacion, ticker, cantidad, precio_unitario, ruta=RUTA_TRANSACCIONES):
    """Añade una fila al fichero CSV con el registro de compra/venta."""
    asegurar_directorio()
    existe = os.path.exists(ruta)
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = round(cantidad * precio_unitario, 2)

    try:
        with open(ruta, "a", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f, delimiter=";")
            if not existe:
                escritor.writerow(["fecha_hora", "operacion", "ticker", "cantidad", "precio_unitario", "total"])
            escritor.writerow([fecha_hora, operacion.upper(), ticker.upper(), cantidad, precio_unitario, total])
        return True
    except IOError as e:
        print(f" Error al registrar la transacción en CSV: {e}")
        return False

def leer_historial(ruta=RUTA_TRANSACCIONES):
    """Lee y devuelve el historial de transacciones registradas en el CSV."""
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lector = csv.DictReader(f, delimiter=";")
            return list(lector)
    except IOError:
        return []