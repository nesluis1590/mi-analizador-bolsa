import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import pytz

st.set_page_config(page_title="Crypto Scalper 24/7", layout="wide")

def obtener_datos_crypto(ticker):
    try:
        # Para Cripto, bajamos los últimos 2 días con velas de 5 min
        df = yf.download(ticker, period="2d", interval="5min", progress=False)
        
        if df.empty:
            return None
        
        # LIMPIEZA DE COLUMNAS (Importante para yfinance en Cripto)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        # Indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

# --- INTERFAZ ---
tz = pytz.timezone('America/Caracas')
st.title("₿ Scalper Cripto 24/7 (En Vivo)")
st.write(f"📍 **Hora VET:** {datetime.now(tz).strftime('%I:%M:%S %p')}")

# CAMBIAMOS A CRIPTO PARA PROBAR AHORA QUE LA BOLSA CERRÓ
activos = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        df = obtener_datos_crypto(ticker)
        
        if df is not None and not df.empty:
            ultimo = df.iloc[-1]
            precio = float(ultimo['Close'])
            rsi = float(ultimo['RSI'])
            
            st.subheader(f"{nombre}")
            st.metric("Precio Actual", f"${precio:,.2f}")
            st.metric("RSI (5m)", f"{rsi:.1f}")

            # Gráfico
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange'), name="SMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
            
            fig.update_layout(height=450, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Buscando señal de {nombre}...")
