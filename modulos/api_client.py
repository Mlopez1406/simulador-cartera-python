import requests
import json
import os
import time
import random

API_KEY_FINNHUB = "dboq4vhr01qo2f3ncp10dboq4vhr01qo2f3ncp1g"
RUTA_CACHE = "datos/cache_cotizaciones.json"
TIEMPO_EXPIRACION_SEGUNDOS = 600  # 10 minutos de validez de caché

def _cargar_cache():
    if os.path.exists(RUTA_CACHE):
        try:
            with open(RUTA_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _guardar_cache(cache):
    try:
        with open(RUTA_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4)
    except Exception:
        pass

def obtener_precio_actual(ticker):
    """
    Obtiene el precio actual de un ticker. 
    Aplica caché local y fallback a simulación si no hay conexión a la API.
    """
    ticker = ticker.upper()
    cache = _cargar_cache()
    ahora = time.time()

    # 1. Comprobar si está en caché y sigue vigente
    if ticker in cache:
        datos_guardados = cache[ticker]
        if ahora - datos_guardados.get("timestamp", 0) < TIEMPO_EXPIRACION_SEGUNDOS:
            return datos_guardados["precio"], "CACHE"

    # 2. Intentar llamada HTTP a la API REST (Finnhub)
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={API_KEY_FINNHUB}"
    try:
        respuesta = requests.get(url, timeout=4)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            precio_cierre = datos.get("c", 0)
            if precio_cierre and precio_cierre > 0:
                # Actualizar caché local
                cache[ticker] = {"precio": precio_cierre, "timestamp": ahora}
                _guardar_cache(cache)
                return precio_cierre, "API_LIVE"
    except Exception:
        pass  # Si ocurre un fallo de red, se gestiona con el modo contingencia/offline

    # 3. Fallback: Modo Simulación Offline si falla la API
    precio_base = cache.get(ticker, {}).get("precio", 150.0)
    variacion = random.uniform(-0.015, 0.015)  # Variación aleatoria de ±1.5%
    precio_simulado = round(precio_base * (1 + variacion), 2)
    
    return precio_simulado, "OFFLINE_SIMULACION"

def obtener_datos_volatilidad(ticker):
    """
    Obtiene el precio máximo, mínimo y el porcentaje de oscilación diaria de una acción
    para medir si sufre variaciones bruscas o estables.
    """
    ticker = ticker.upper()
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={API_KEY_FINNHUB}"
    
    try:
        respuesta = requests.get(url, timeout=4)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            precio_actual = datos.get("c", 0)
            max_dia = datos.get("h", 0)
            min_dia = datos.get("l", 0)
            cambio_pct = datos.get("dp", 0)

            if precio_actual > 0 and max_dia > 0 and min_dia > 0:
                # Fórmula de amplitud/volatilidad intradía (%)
                oscilacion_pct = ((max_dia - min_dia) / min_dia) * 100
                return {
                    "ticker": ticker,
                    "oscilacion_pct": round(oscilacion_pct, 2),
                    "cambio_pct": round(cambio_pct, 2),
                    "fuente": "API_LIVE"
                }
    except Exception:
        pass

    # Modo simulación si no hay internet o el mercado está cerrado
    tecnologicas = ["TSLA", "NVDA", "AAPL", "MSFT", "META", "AMZN", "GOOGL"]
    if ticker in tecnologicas:
        oscilacion_sim = round(random.uniform(3.2, 6.5), 2)
        cambio_sim = round(random.uniform(-4.0, 4.5), 2)
    else:
        oscilacion_sim = round(random.uniform(0.6, 1.6), 2)
        cambio_sim = round(random.uniform(-1.0, 1.2), 2)

    return {
        "ticker": ticker,
        "oscilacion_pct": oscilacion_sim,
        "cambio_pct": cambio_sim,
        "fuente": "OFFLINE_SIMULACION"
    }