import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Crypto Scalper VET", layout="wide")

def obtener_datos(ticker):
    try:
        # Descarga simplificada
        df = yf.download(ticker, period="2d", interval="5min", auto_adjust=True)
        
        if df is None or len(df) == 0:
            return None
            
        # Limpieza agresiva de columnas MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Asegurar que las columnas sean 1D
        df = df.copy()
        
        # Calcular indicadores (usando pandas_ta)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except Exception as e:
        return None

# --- INTERFAZ ---
tz = pytz.timezone('America/Caracas')
st.title("₿ Monitor Cripto 24/7")
st.write(f"Sincronizado con Caracas: {datetime.now(tz).strftime('%I:%M %p')}")

# Usamos una lista para iterar
activos = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}

for nombre, ticker in activos.items():
    st.subheader(f"Activo: {nombre}")
    df = obtener_datos(ticker)
    
    if df is not None:
        ultimo_precio = float(df['Close'].iloc[-1])
        ultimo_rsi = float(df['RSI'].iloc[-1])
        
        col1, col2 = st.columns(2)
        col1.metric("Precio", f"${ultimo_precio:,.2f}")
        col2.metric("RSI", f"{ultimo_rsi:.2f}")

        # Gráfico
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close'], name="Precio"
        ))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange'), name="SMA50"))
        
        fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"⚠️ Error: No hay datos disponibles para {nombre} en este momento.")
