import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
import time

# --- CONFIGURACIÓN ---
API_KEY_ALPHA = "FZEZWV0VBR5BN4Y7"
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"
TELEGRAM_CHAT_ID = "841967788"

st.set_page_config(page_title="Scanner Pro + Alertas", layout="wide")

def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except:
        pass

def obtener_datos(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY_ALPHA}&outputsize=compact'
    try:
        r = requests.get(url)
        data = r.json()
        if "Time Series (Daily)" not in data: return None
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1]
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        return df
    except:
        return None

# --- INTERFAZ ---
st.title("🚀 Sistema de Señales con Alerta Telegram")
activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}

col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        if i > 0: time.sleep(2)
        df = obtener_datos(ticker)
        
        if df is not None:
            val = df.iloc[-1]
            rsi, mfi = val['RSI'], val['MFI']
            precio = val['Close']

            st.subheader(f"{nombre}: ${precio:.2f}")
            
            # LÓGICA DE ENTRADA
            if rsi < 35 and mfi < 35:
                msg = f"🟢 *ALERTA DE ALZA (LONG)* 🟢\nActivo: {nombre}\nPrecio: ${precio:.2f}\nRSI: {rsi:.1f} | MFI: {mfi:.1f}"
                st.success("SEÑAL DE COMPRA DETECTADA")
                if st.button(f"Enviar alerta de {ticker} a Telegram"):
                    enviar_telegram(msg)
                    st.toast("Enviado!")
            
            elif rsi > 65 and mfi > 65:
                msg = f"🔴 *ALERTA DE BAJA (SHORT)* 🔴\nActivo: {nombre}\nPrecio: ${precio:.2f}\nRSI: {rsi:.1f} | MFI: {mfi:.1f}"
                st.error("SEÑAL DE VENTA DETECTADA")
                if st.button(f"Enviar alerta de {ticker} a Telegram"):
                    enviar_telegram(msg)
                    st.toast("Enviado!")
            else:
                st.info("Sin señales claras en este momento.")

            # Gráfico minimalista para móvil
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(height=300, template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
