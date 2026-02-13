import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN ---
API_KEY_ALPHA = "F7HHVS6BLMN7A0LE"
TELEGRAM_TOKEN = "TU_TELEGRAM_TOKEN_AQUI"
TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUI"

st.set_page_config(page_title="Scalper Pro 5m - VET", layout="wide")

# Configuración de Hora Venezuela
venezuela_tz = pytz.timezone('America/Caracas')
hora_actual = datetime.now(venezuela_tz).strftime('%H:%M:%S')

# --- 2. FUNCIONES ---
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except:
        pass

def obtener_datos_5min(symbol):
    # Forzamos la descarga sin importar la hora del sistema
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={API_KEY_ALPHA}&outputsize=compact'
    try:
        r = requests.get(url).json()
        key = "Time Series (5min)"
        
        if key not in r:
            if "Note" in r:
                st.warning(f"⚠️ Límite de API. Espera un momento...")
            return None
        
        df = pd.DataFrame.from_dict(r[key], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1]
        
        # Indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except:
        return None

# --- 3. INTERFAZ ---
st.title("🚀 Scalper Pro 5m: NDX & SPX")
st.write(f"📍 **Zona Horaria:** Caracas (UTC-4) | **Hora Actual:** {hora_actual}")

# Verificación visual del horario de mercado para el usuario
ahora = datetime.now(venezuela_tz)
es_hora_mercado = ahora.hour >= 10 and ahora.hour < 17

if not es_hora_mercado:
    st.sidebar.warning("🌙 El mercado está fuera de horario oficial (10:30 AM - 5:00 PM VET), pero intentaré cargar datos recientes.")
else:
    st.sidebar.success("☀️ Mercado Abierto")

activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        if i > 0: time.sleep(2) 
        
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
            if rsi < 35 and mfi < 35:
                st.success("🟢 SEÑAL DE COMPRA")
                if st.button(f"Notificar Compra {ticker}"):
                    enviar_telegram(f"🟢 *COMPRA* {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}")
            elif rsi > 65 and mfi > 65:
                st.error("🔴 SEÑAL DE VENTA")
                if st.button(f"Notificar Venta {ticker}"):
                    enviar_telegram(f"🔴 *VENTA* {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}")

            # --- GRÁFICO ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
            
            fig.update_layout(height=450, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"⏳ Buscando datos de {ticker} en el servidor...")
