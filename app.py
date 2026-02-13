import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- 1. CONFIGURACIÓN ---
API_KEY_ALPHA = "5D3KE1ZCPW9RG2NB"
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"
TELEGRAM_CHAT_ID = "841967788"

st.set_page_config(page_title="Scalper Pro 5m", layout="wide")

# --- 2. FUNCIONES ---
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except:
        pass

def obtener_datos_5min(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={API_KEY_ALPHA}&outputsize=compact'
    try:
        r = requests.get(url).json()
        
        # Validación de respuesta
        key = "Time Series (5min)"
        if key not in r:
            if "Note" in r: 
                st.warning(f"⏸️ Límite de API alcanzado para {symbol}. Reintentando en automático...")
            return None
        
        # Creación de DataFrame
        df = pd.DataFrame.from_dict(r[key], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1]
        
        # Indicadores Técnicos
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        # CORRECCIÓN: Eliminar filas con valores nulos (SMA50 necesita 50 velas previas)
        df = df.dropna()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- 3. INTERFAZ ---
st.title("🚀 Scalper Pro 5m: NDX & SPX")
st.markdown(f"**Estado:** Conectado | **Horario Local:** {time.strftime('%H:%M')} VET")

activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        if i > 0: time.sleep(1) 
        
        df = obtener_datos_5min(ticker)
        
        if df is not None and not df.empty:
            val = df.iloc[-1]
            precio, rsi, mfi, sma50 = val['Close'], val['RSI'], val['MFI'], val['SMA50']
            tendencia = "📈 ALCISTA" if precio > sma50 else "📉 BAJISTA"

            st.subheader(f"{nombre}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("Tendencia", tendencia)
            m3.metric("RSI", f"{rsi:.1f}")

            # Lógica de Alerta
            mensaje_alerta = ""
            if rsi < 35 and mfi < 35:
                st.success("🟢 SEÑAL DE COMPRA")
                mensaje_alerta = f"🟢 *SCALP COMPRA* en {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}"
            elif rsi > 65 and mfi > 65:
                st.error("🔴 SEÑAL DE VENTA")
                mensaje_alerta = f"🔴 *SCALP VENTA* en {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}"

            if mensaje_alerta != "" and st.button(f"Notificar {ticker}"):
                enviar_telegram(mensaje_alerta)
                st.toast("Enviado!")

            # Gráfico Robusto
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"), row=1,
