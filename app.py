import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Scalper Pro", layout="wide")

def obtener_datos(ticker):
    try:
        # Descarga forzada sin hilos (más lenta pero segura)
        df = yf.download(ticker, period="2d", interval="5min", group_by='column', threads=False)
        
        if df.empty:
            return None

        # --- LIMPIEZA DEFINITIVA DE COLUMNAS ---
        # Si Yahoo manda columnas dobles, nos quedamos solo con la primera fila de nombres
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Reset de seguridad
        df = df.copy()
        
        # Calcular indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

st.title("🚀 Scalper Pro 5m")

# Activos
activos = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}

for nombre, ticker in activos.items():
    df = obtener_datos(ticker)
    
    if df is not None and not df.empty:
        # Tomamos el último valor de forma ultra-segura
        ultimo_p = float(df['Close'].iloc[-1])
        ultimo_r = float(df['RSI'].iloc[-1])
        
        st.subheader(f"📊 {nombre}")
        st.metric("Precio", f"${ultimo_p:,.2f}", delta=f"RSI: {ultimo_r:.2f}")

        # Gráfico Simple para asegurar que cargue
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close'], name="Velas"
        ))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange'), name="SMA50"))
        
        fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"⏳ Buscando conexión para {nombre}...")
