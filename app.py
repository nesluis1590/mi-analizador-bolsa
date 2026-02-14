import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import pytz

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"
TELEGRAM_CHAT_ID = "841967788"

st.set_page_config(page_title="Scalper Pro VET - yfinance", layout="wide")

# Función para enviar a Telegram
def enviar_telegram(mensaje):
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except:
        pass

# --- FUNCIÓN DE DATOS (MÁS RÁPIDA) ---
def obtener_datos_yf(ticker):
    try:
        # Descargamos 2 días de datos con velas de 5 minutos
        df = yf.download(ticker, period="5d", interval="60min", progress=False)
        if df.empty: return None
        
        # Ajuste de columnas para yfinance
        df = df.copy()
        
        # Indicadores Técnicos
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except Exception as e:
        st.error(f"Error en {ticker}: {e}")
        return None

# --- INTERFAZ ---
tz = pytz.timezone('America/Caracas')
st.title("🚀 Scalper Pro 5m (Online)")
st.write(f"📍 **Hora Caracas:** {datetime.now(tz).strftime('%I:%M:%S %p')}")

activos = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        df = obtener_datos_yf(ticker)
        
        if df is not None and not df.empty:
            ultimo = df.iloc[-1]
            precio = float(ultimo['Close'])
            rsi = float(ultimo['RSI'])
            mfi = float(ultimo['MFI'])
            sma50 = float(ultimo['SMA50'])
            
            tendencia = "📈 ALCISTA" if precio > sma50 else "📉 BAJISTA"
            color_t = "green" if precio > sma50 else "red"

            st.subheader(f"{nombre}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("Tendencia", tendencia)
            m3.metric("RSI", f"{rsi:.1f}")

            # Lógica de Alerta
            if rsi < 35 and mfi < 35:
                st.success("🟢 OPORTUNIDAD DE COMPRA")
                if st.button(f"Alertar Compra {ticker}"):
                    enviar_telegram(f"🟢 *COMPRA* {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}")
            elif rsi > 65 and mfi > 65:
                st.error("🔴 OPORTUNIDAD DE VENTA")
                if st.button(f"Alertar Venta {ticker}"):
                    enviar_telegram(f"🔴 *VENTA* {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}")

            # Gráfico Plotly
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
            
            fig.update_layout(height=400, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Esperando datos de {nombre}...")
