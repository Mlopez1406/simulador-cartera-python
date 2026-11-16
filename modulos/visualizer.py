import os
import webbrowser

def generar_panel_graficas(resumen, obtener_volatilidad_func):
    """Genera un informe visual HTML con 3 gráficas SVG y lo abre en el navegador."""
    print("\n [1/3] Comprobando posiciones en cartera...", flush=True)

    posiciones = resumen["posiciones"]
    if not posiciones:
        print(" Aún no tienes acciones compradas. Compra al menos una tecnológica (ej. TSLA) y una tradicional (ej. WMT) primero.")
        return

    tickers = [pos["ticker"] for pos in posiciones]
    pnl_euros = [pos["pnl_euros"] for pos in posiciones]
    valores_mercado = [pos["valor_mercado"] for pos in posiciones]

    tecnologicas = {"TSLA", "NVDA", "AAPL", "MSFT", "META", "AMZN", "GOOGL"}
    oscilaciones = []
    vol_tech = []
    vol_trad = []

    print(f" [2/3] Analizando volatilidad diaria de {len(tickers)} empresas...", flush=True)
    for t in tickers:
        datos_vol = obtener_volatilidad_func(t)
        osc = datos_vol["oscilacion_pct"]
        oscilaciones.append(osc)
        if t in tecnologicas:
            vol_tech.append(osc)
        else:
            vol_trad.append(osc)

    print(" [3/3] Generando panel visual y abriendo navegador...", flush=True)

    # 1. Barras de Volatilidad (%)
    ancho1 = max(360, len(tickers) * 75 + 60)
    max_osc = max(oscilaciones) if max(oscilaciones) > 0 else 1.0
    svg_vol = ""
    for i, (t, osc) in enumerate(zip(tickers, oscilaciones)):
        x = 45 + i * 70
        h = (osc / max_osc) * 145
        y = 185 - h
        color = "#8e44ad" if t in tecnologicas else "#2980b9"
        svg_vol += f'<rect x="{x}" y="{y:.1f}" width="40" height="{h:.1f}" fill="{color}" rx="4"/>'
        svg_vol += f'<text x="{x+20}" y="{y-6:.1f}" text-anchor="middle" font-size="11" font-weight="bold" fill="#2c3e50">{osc:.2f}%</text>'
        svg_vol += f'<text x="{x+20}" y="205" text-anchor="middle" font-size="12" font-weight="bold" fill="#34495e">{t}</text>'

    # 2. Barras de P&L (€)
    ancho2 = max(360, len(tickers) * 75 + 60)
    max_pnl = max([abs(p) for p in pnl_euros]) or 1.0
    svg_pnl = ""
    y0 = 110
    for i, (t, pnl) in enumerate(zip(tickers, pnl_euros)):
        x = 45 + i * 70
        h = (abs(pnl) / max_pnl) * 75
        if pnl >= 0:
            y, color, yt = y0 - h, "#27ae60", y0 - h - 6
        else:
            y, color, yt = y0, "#e74c3c", y0 + h + 14
        svg_pnl += f'<rect x="{x}" y="{y:.1f}" width="40" height="{max(h, 2):.1f}" fill="{color}" rx="3"/>'
        svg_pnl += f'<text x="{x+20}" y="{yt:.1f}" text-anchor="middle" font-size="11" font-weight="bold" fill="{color}">{pnl:+.1f}€</text>'
        svg_pnl += f'<text x="{x+20}" y="210" text-anchor="middle" font-size="12" font-weight="bold" fill="#34495e">{t}</text>'

    # 3. Gráfico Donut de Patrimonio
    etiquetas = ["Efectivo"] + tickers
    cantidades = [resumen["efectivo"]] + valores_mercado
    total = sum(cantidades) or 1.0
    paleta = ["#95a5a6", "#8e44ad", "#2980b9", "#16a085", "#f39c12", "#d35400", "#2c3e50", "#c0392b"]
    circ = 2 * 3.14159 * 65
    acum = 0.0
    svg_donut = ""
    leyenda = ""
    for i, (et, cant) in enumerate(zip(etiquetas, cantidades)):
        pct = (cant / total) * 100
        tramo = (cant / total) * circ
        c = paleta[i % len(paleta)]
        svg_donut += f'<circle r="65" cx="105" cy="105" fill="transparent" stroke="{c}" stroke-width="26" stroke-dasharray="{tramo:.2f} {circ:.2f}" stroke-dashoffset="-{acum:.2f}" transform="rotate(-90 105 105)"/>'
        acum += tramo
        leyenda += f'<div style="margin-bottom:6px;font-size:13px;"><span style="display:inline-block;width:11px;height:11px;background:{c};margin-right:7px;border-radius:2px;"></span><b>{et}:</b> {pct:.1f}% ({cant:.2f} €)</div>'

    # Conclusión automática
    if vol_tech and vol_trad:
        m_tech = sum(vol_tech) / len(vol_tech)
        m_trad = sum(vol_trad) / len(vol_trad)
        conclusion = f"Las empresas <b>tecnológicas/mediáticas</b> tienen una oscilación media hoy del <b>{m_tech:.2f}%</b>, frente al <b>{m_trad:.2f}%</b> de las <b>tradicionales</b>. Se confirma que reaccionan con variaciones más bruscas."
    else:
        conclusion = "Añade al menos una acción tecnológica (TSLA, NVDA, AAPL) y una tradicional (WMT, KO) para comparar ambas barras."

    plantilla = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Análisis Visual de Cartera</title>
<style>
body{font-family:'Segoe UI',Arial,sans-serif;background:#f4f6f9;color:#2c3e50;padding:25px;margin:0}
.wrap{max-width:1180px;margin:auto}
h1{text-align:center;margin-bottom:4px}
.sub{text-align:center;color:#5d6d7e;margin-bottom:22px}
.grid{display:flex;flex-wrap:wrap;gap:18px;justify-content:center}
.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 4px 12px rgba(0,0,0,.08);flex:1;min-width:330px}
.card h2{font-size:15px;margin-top:0;border-bottom:1px solid #eee;padding-bottom:8px}
.box{background:#ebf5fb;border-left:5px solid #2980b9;padding:15px;border-radius:8px;margin-top:22px;font-size:15px}
</style></head><body><div class="wrap">
<h1>Análisis de Cartera: Tecnológicas vs. Empresas Tradicionales</h1>
<div class="sub">Hipótesis: ¿Sufren las acciones tecnológicas variaciones más bruscas que las tradicionales?</div>
<div class="grid">
<div class="card"><h2>1. Variación Brusca Hoy (Oscilación %)</h2>
<div style="font-size:12px;margin-bottom:8px"><b style="color:#8e44ad">■</b> Tecnológicas &nbsp;&nbsp; <b style="color:#2980b9">■</b> Tradicionales</div>
<svg width="100%" height="220" viewBox="0 0 __W1__ 220"><line x1="30" y1="185" x2="__W1B__" y2="185" stroke="#bdc3c7" stroke-width="1.5"/>__SVG_VOL__</svg></div>
<div class="card"><h2>2. Impacto en tu Dinero (P&L en €)</h2>
<div style="font-size:12px;margin-bottom:8px"><b style="color:#27ae60">■</b> Beneficio (+) &nbsp;&nbsp; <b style="color:#e74c3c">■</b> Pérdida (-)</div>
<svg width="100%" height="220" viewBox="0 0 __W2__ 220"><line x1="30" y1="110" x2="__W2B__" y2="110" stroke="#7f8c8d" stroke-width="1.5" stroke-dasharray="4"/>__SVG_PNL__</svg></div>
<div class="card"><h2>3. Distribución del Patrimonio</h2>
<div style="display:flex;align-items:center;justify-content:space-around;flex-wrap:wrap;margin-top:12px">
<svg width="210" height="210" viewBox="0 0 210 210">__SVG_DONUT__<text x="105" y="102" text-anchor="middle" font-size="11" fill="#7f8c8d">TOTAL</text><text x="105" y="120" text-anchor="middle" font-size="14" font-weight="bold" fill="#2c3e50">__TOTAL__ €</text></svg>
<div>__LEYENDA__</div></div></div></div>
<div class="box"><b>Conclusión del experimento:</b> __CONCLUSION__</div>
</div></body></html>"""

    html_final = (plantilla
        .replace("__W1__", str(ancho1))
        .replace("__W1B__", str(ancho1 - 20))
        .replace("__SVG_VOL__", svg_vol)
        .replace("__W2__", str(ancho2))
        .replace("__W2B__", str(ancho2 - 20))
        .replace("__SVG_PNL__", svg_pnl)
        .replace("__SVG_DONUT__", svg_donut)
        .replace("__TOTAL__", f"{resumen['total_cuenta']:.0f}")
        .replace("__LEYENDA__", leyenda)
        .replace("__CONCLUSION__", conclusion)
    )

    if not os.path.exists("datos"):
        os.makedirs("datos")
    ruta_html = os.path.abspath("datos/graficas_analisis.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f" ¡Listo! Gráficas generadas en: {ruta_html}", flush=True)
    webbrowser.open(f"file:///{ruta_html.replace(os.sep, '/')}")