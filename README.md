# Simulador de Cartera Bursátil (Paper Trading)

## 1. Pregunta de Investigación e Hipótesis
**¿Es cierto que las acciones de empresas tecnológicas y mediáticas (como Tesla, Nvidia o Apple) sufren variaciones diarias más bruscas que las empresas tradicionales de consumo (como Walmart o Coca-Cola), y cómo afecta esa volatilidad al resultado económico (P&L) de un inversor?**

* **Hipótesis:** Las empresas tecnológicas y mediáticas presentan una amplitud de oscilación diaria significativamente mayor debido a su sensibilidad a noticias y expectativas de mercado, generando variaciones más acusadas en el beneficio/pérdida (P&L) frente a empresas tradicionales de consumo básico.

---

## 2. Metodología y Fórmulas Implementadas
Para comprobar la hipótesis con datos reales, el sistema aplica dos métricas financieras clave:
1. **Amplitud / Volatilidad Intradía (%):** Calculada a partir del precio máximo (`h`) y mínimo (`l`) de la sesión obtenidos mediante la API de Finnhub:
   $$\text{Oscilación (\%)} = \frac{\text{Máximo del día} - \text{Mínimo del día}}{\text{Mínimo del día}} \times 100$$
2. **Precio Medio Ponderado de Compra (PMPC):** Recalcula automáticamente el coste medio por acción al realizar compras sucesivas de una misma empresa a distintos precios:
   $$\text{PMPC} = \frac{(\text{Cantidad Anterior} \times \text{PMPC Anterior}) + (\text{Cantidad Nueva} \times \text{Precio Nuevo})}{\text{Cantidad Total}}$$

---

## 3. Arquitectura Modular del Proyecto
El código separa la lógica financiera del almacenamiento y las interfaces de usuario para evitar duplicidades:

* **`modulos/api_client.py`**: Conexión REST con Finnhub, sistema de caché local (10 minutos), cálculo de oscilación diaria y modo simulación offline ante fallos de red.
* **`modulos/portfolio_manager.py`**: Motor financiero compartido para compras, ventas, ingresos de capital, cálculo de PMPC y valoración de P&L.
* **`modulos/file_handler.py`**: Persistencia en `datos/cartera.json` y registro histórico de operaciones en `datos/transacciones.csv`.
* **`modulos/visualizer.py`**: Generación automática de informe visual HTML/SVG (`datos/graficas_analisis.html`) con comparativa por sectores.
* **`main.py`**: Interfaz de consola interactiva (8 opciones) con análisis gráfico en navegador.
* **`app.py` y `backend.py`**: Interfaz web desarrollada en Streamlit respaldada por base de datos SQLite (`datos/cartera_web.sqlite3`).

---

## 4. Cómo ejecutar el proyecto

**Opción A — Versión Terminal + Informe Gráfico HTML:**
```bash
python main.py