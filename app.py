import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- CONFIGURACIÓN DE IDENTIDAD ---
API_KEY_ALPHA = "SKCONN9Z5D62QACK"
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"
TELEGRAM_CHAT_ID = "841967788"

st.set_page_config(page_title="Scanner Pro Elite", layout="wide")

# Función para enviar alertas
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except:
        st.error("Error al enviar a Telegram. Revisa el Token/ID.")

def obtener_datos(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY_ALPHA}&outputsize=compact'
    try:
        r = requests.get(url).json()
        if "Time Series (Daily)" not in r: return None
        df = pd.DataFrame.from_dict(r["Time Series (Daily)"], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1]
        
        # Indicadores Profesionales
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        return df
    except:
        return None

# --- INTERFAZ ---
st.title("🏛️ Monitor Pro: NDX & SPX")
st.write("Conectado a Telegram | Filtro de Tendencia SMA 50")

activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        if i > 0: time.sleep(2) # Pausa técnica para la API
        df = obtener_datos(ticker)
        
        if df is not None:
            val = df.iloc[-1]
            precio, rsi, mfi, sma50 = val['Close'], val['RSI'], val['MFI'], val['SMA50']
            
            # Lógica de Tendencia
            es_alcista = precio > sma50
            txt_tendencia = "📈 ALCISTA" if es_alcista else "📉 BAJISTA"
            
            st.subheader(f"{nombre}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("Tendencia", txt_tendencia)
            m3.metric("RSI", f"{rsi:.1f}")

            # --- GENERADOR DE ALERTAS ---
            mensaje_alerta = ""
            
            if rsi < 35 and mfi < 35:
                st.success("🔥 SEÑAL DE COMPRA DETECTADA")
                mensaje_alerta = f"🟢 *COMPRA* en {nombre}\nPrecio: ${precio:.2f}\nIndicadores: RSI {rsi:.1f} | MFI {mfi:.1f}\nTendencia: {txt_tendencia}"
                
            elif rsi > 65 and mfi > 65:
                st.error("🔴 SEÑAL DE VENTA DETECTADA")
                mensaje_alerta = f"🔴 *VENTA* en {nombre}\nPrecio: ${precio:.2f}\nIndicadores: RSI {rsi:.1f} | MFI {mfi:.1f}\nTendencia: {txt_tendencia}"

            # Botón manual por si quieres avisar a otros o a ti mismo de nuevo
            if mensaje_alerta != "":
                if st.button(f"Enviar Alerta de {ticker} ahora"):
                    enviar_telegram(mensaje_alerta)
                    st.balloons()

            # Gráfico con SMA 50 (Línea naranja de tendencia)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="Tendencia"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='cyan')), row=2, col=1)
            
            fig.update_layout(height=400, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
