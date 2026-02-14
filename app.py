import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Scalper Pro Universal", layout="wide")

def obtener_datos_seguros(ticker):
    try:
        # Descargamos los últimos 2 días con velas de 5 min
        # Usamos period="2d" para asegurar que siempre haya datos aunque sea fin de semana
        df = yf.download(ticker, period="2d", interval="5min", progress=False)
        
        if df.empty or len(df) < 50:
            return None
            
        # LIMPIEZA DE COLUMNAS (Para evitar el error de Multi-Index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.copy()
        
        # Indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        # Quitamos los nulos iniciales del SMA50
        df = df.dropna()
        
        return df if not df.empty else None
    except Exception as e:
        st.sidebar.error(f"Error en {ticker}: {e}")
        return None

# --- INTERFAZ ---
tz = pytz.timezone('America/Caracas')
st.title("🚀 Scalper Pro 5m")
st.write(f"Sincronizado con Caracas: {datetime.now(tz).strftime('%I:%M %p')}")

# Lista de activos (Bitcoin y Ethereum para probar ahorita)
activos = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}

for nombre, ticker in activos.items():
    df = obtener_datos_seguros(ticker)
    
    if df is not None:
        # Extraemos los valores de forma segura
        ultimo_precio = float(df['Close'].iloc[-1])
        ultimo_rsi = float(df['RSI'].iloc[-1])
        sma50 = float(df['SMA50'].iloc[-1])
        
        st.subheader(f"📊 {nombre}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Precio", f"${ultimo_precio:,.2f}")
        c2.metric("RSI", f"{ultimo_rsi:.2f}")
        c3.metric("SMA50", "📈 Arriba" if ultimo_precio > sma50 else "📉 Abajo")

        # Gráfico Robusto
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close'], name="Velas"
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
        
        fig.update_layout(height=450, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"⏳ {nombre}: Esperando datos del mercado...")
