"""Frontend Streamlit del simulador de cartera."""
import json
import time
import altair as alt
import pandas as pd
import streamlit as st
from backend import PortfolioService, quote

st.set_page_config(page_title='Nexo | Simulador de cartera', page_icon='📈', layout='wide')
st.markdown('''<style>
.stApp {background: #0b1120;}
.block-container {padding-top: 2.5rem; max-width: 1400px;}
[data-testid="stSidebar"] {background: #101a2c;}
[data-testid="stMetric"] {background: #142038; border: 1px solid #243450; border-radius: 16px; padding: 20px;}
h1,h2,h3 {letter-spacing: -.035em;}
.eyebrow {color:#49dcb1; font-size:12px; letter-spacing:3px; font-weight:700;}
.hero {color:#98a9c4; font-size:17px; margin-bottom:24px;}
</style>''', unsafe_allow_html=True)

try:
    service = PortfolioService()
    state = service.state()
except Exception as exc:
    st.error(f'No se pudieron cargar los datos: {exc}')
    st.stop()

with st.sidebar:
    st.title('◈ Nexo')
    st.caption('TU ESPACIO DE INVERSIÓN VIRTUAL')
    st.divider()
    page = st.radio('Navegación', ['Resumen', 'Operar', 'Cotizaciones', 'Análisis', 'Historial', 'Cuenta'], label_visibility='collapsed')
    st.divider()
    st.markdown('**Cuenta de simulación**')
    st.caption('Guardado automático · SQLite')
    st.info('Modo demo: precios de referencia fijos, no cotizaciones actuales.')
    st.caption('Se mantiene la unidad € del proyecto original. Los precios de referencia no incluyen conversión de divisas.')

def money(n):
    return f'{n:,.2f} €'.replace(',', 'X').replace('.', ',').replace('X', '.')

def positions(summary):
    return pd.DataFrame(summary['posiciones']).rename(columns={'ticker':'Activo','cantidad':'Acciones','pmpc':'Coste medio','precio_actual':'Precio','valor_mercado':'Valor','pnl_euros':'Resultado','pnl_pct':'Resultado %','origen':'Fuente'})

st.markdown('<div class="eyebrow">NEXO / PAPER TRADING</div>', unsafe_allow_html=True)
st.title({'Resumen':'Tu cartera, de un vistazo','Operar':'Tu próxima operación','Cotizaciones':'Explora el mercado','Análisis':'Entiende tu cartera','Historial':'Cada movimiento cuenta','Cuenta':'Gestiona tu cuenta'}[page])
st.markdown('<div class="hero">Practica, analiza y controla tus inversiones desde un mismo lugar.</div>', unsafe_allow_html=True)
if 'notice' in st.session_state:
    st.success(st.session_state.pop('notice'))

if page in ('Resumen', 'Análisis'):
    try:
        summary = service.summary()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    cols = st.columns(4)
    for col, title, value in zip(cols, ['Patrimonio virtual','Efectivo disponible','Valor invertido','Resultado no realizado'], [summary['total_cuenta'],summary['efectivo'],summary['valor_inversiones'],summary['pnl_global_euros']]):
        col.metric(title, money(value))
    st.caption(f"Rentabilidad de posiciones abiertas: {summary['pnl_global_pct']:+.2f}% · Valoración con precios demo.")
    df = positions(summary)
    if df.empty:
        st.info('Todavía no tienes posiciones. Ve a Operar para realizar tu primera compra.')
    else:
        left, right = st.columns([1, 1.5])
        with left:
            st.subheader('Distribución del patrimonio')
            allocation = pd.DataFrame({'Activo': list(df['Activo'])+['Efectivo'], 'Valor':list(df['Valor'])+[summary['efectivo']]})
            chart = alt.Chart(allocation).mark_arc(innerRadius=75).encode(theta='Valor:Q', color=alt.Color('Activo:N', scale=alt.Scale(scheme='tealblues')), tooltip=['Activo',alt.Tooltip('Valor:Q',format='.2f')]).properties(height=300)
            st.altair_chart(chart, width='stretch')
        with right:
            st.subheader('Resultado por activo')
            chart = alt.Chart(df).mark_bar(cornerRadiusEnd=5).encode(x='Resultado:Q', y=alt.Y('Activo:N', sort='-x'),color=alt.condition(alt.datum.Resultado >= 0, alt.value('#49dcb1'), alt.value('#fb7185')),tooltip=['Activo',alt.Tooltip('Resultado:Q', format='.2f')]).properties(height=300)
            st.altair_chart(chart, width='stretch')
        st.subheader('Posiciones abiertas')
        st.dataframe(df, hide_index=True, width='stretch')
        if page == 'Análisis':
            st.subheader('Concentración de la inversión')
            largest = df.loc[df['Valor'].idxmax()]
            st.info(f"{largest['Activo']} representa el {largest['Valor']/summary['valor_inversiones']*100:.1f}% del capital invertido.")
            st.caption('No se muestra evolución temporal ni volatilidad histórica porque el proyecto no contiene una serie de precios históricos.')

elif page == 'Operar':
    left, right = st.columns([1.5,1])
    with left:
        with st.form('order'):
            operation = st.selectbox('Operación', ['COMPRA','VENTA'])
            ticker = st.selectbox('Activo', sorted(set(['AAPL','TSLA','NVDA','WMT','MSFT','AMZN','GOOGL','META']) | set(state['acciones'])))
            quantity = st.number_input('Número de acciones', min_value=1, max_value=1000000, value=1, step=1)
            preview = st.form_submit_button('Preparar operación', type='primary', width='stretch')
        if preview:
            st.session_state.pop('pending', None)
            try:
                price, source, timestamp = quote(ticker)
                st.session_state.pending = dict(operation=operation, ticker=ticker, quantity=int(quantity), price=price, timestamp=timestamp)
            except ValueError as exc:
                st.error(str(exc))
        pending = st.session_state.get('pending')
        if pending:
            with st.container(border=True):
                st.subheader('Revisa tu operación')
                st.write(f"{pending['operation']} · {pending['quantity']} acciones de {pending['ticker']}")
                st.metric('Total virtual', money(pending['price']*pending['quantity']))
                st.caption(f"Precio unitario: {money(pending['price'])} · DEMO · Validez: 5 minutos")
                confirm, cancel = st.columns(2)
                if confirm.button('Confirmar operación', type='primary', width='stretch'):
                    try:
                        if time.time()-pending['timestamp'] > 300:
                            raise ValueError('La propuesta ha caducado. Prepara la operación de nuevo.')
                        st.session_state.notice = service.execute(**{k:v for k,v in pending.items() if k != 'timestamp'})
                        del st.session_state.pending
                        st.rerun()
                    except (ValueError, OSError) as exc:
                        st.error(str(exc))
                if cancel.button('Cancelar', width='stretch'):
                    del st.session_state.pending
                    st.rerun()
    with right:
        st.metric('Efectivo disponible', money(state['saldo_euros']))
        st.subheader('Tus acciones')
        for ticker, data in state['acciones'].items():
            st.write(f"**{ticker}** · {data['cantidad']} acciones")

elif page == 'Cotizaciones':
    with st.form('quote'):
        ticker = st.text_input('Símbolo bursátil', value='AAPL')
        search = st.form_submit_button('Consultar precio', type='primary')
    st.caption('Disponibles en demo: AAPL, TSLA, NVDA, WMT, MSFT, AMZN, GOOGL y META.')
    if search:
        try:
            price, source, _ = quote(ticker)
            st.metric(ticker.strip().upper(), money(price))
            st.info(source)
        except ValueError as exc:
            st.error(str(exc))

elif page == 'Historial':
    history = pd.DataFrame(service.history())
    if history.empty:
        st.info('Aún no hay movimientos.')
    else:
        kinds = st.multiselect('Filtrar operaciones', ['COMPRA','VENTA','INGRESO'], default=['COMPRA','VENTA','INGRESO'])
        filtered = history[history.operacion.isin(kinds)]
        st.dataframe(filtered, hide_index=True, width='stretch')
        st.download_button('Descargar historial completo CSV', service.export_csv(), 'historial.csv', 'text/csv')

elif page == 'Cuenta':
    st.metric('Saldo disponible', money(state['saldo_euros']))
    with st.form('deposit'):
        st.subheader('Añadir saldo virtual')
        amount = st.number_input('Importe (€)', min_value=0.01, max_value=10000000.0, value=1000.0, step=100.0)
        submit = st.form_submit_button('Ingresar saldo virtual', type='primary')
    if submit:
        try:
            st.session_state.notice = service.execute('INGRESO', price=float(amount))
            st.rerun()
        except (ValueError, OSError) as exc:
            st.error(str(exc))
    st.subheader('Copia de tus datos')
    st.download_button('Descargar cartera JSON', json.dumps(state, indent=2, ensure_ascii=False), 'cartera.json', 'application/json')
    st.caption('La web importa una vez los JSON/CSV originales y guarda sus cambios en datos/cartera_web.sqlite3. La versión de terminal conserva sus archivos independientes.')
