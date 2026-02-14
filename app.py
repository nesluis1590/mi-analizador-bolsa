import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Scalper Pro Binance", layout="wide")

def obtener_datos_binance(symbol):
    try:
        # Traemos las últimas 100 velas de 5 minutos
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100"
        res = requests.get(url).json()
        
        # Estructura de Binance: [Tiempo, Open, High, Low, Close, Volume, ...]
        df = pd.DataFrame(res, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVolume', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
        
        # Convertir a formato numérico
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = df[col].astype(float)
            
        df.set_index('Time', inplace=True)

        # Indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except Exception as e:
        return None

# --- INTERFAZ ---
tz = pytz.timezone('America/Caracas')
st.title("⚡ Scalper Pro: Conexión Directa Binance")
st.write(f"Sincronizado con Caracas: {datetime.now(tz).strftime('%I:%M %p')}")

# Símbolos en formato Binance (BTCUSDT es Bitcoin vs Dólar)
activos = {"Bitcoin": "BTCUSDT", "Ethereum": "ETHUSDT"}

for nombre, ticker in activos.items():
    st.subheader(f"📊 {nombre} (5 min)")
    df = obtener_datos_binance(ticker)
    
    if df is not None:
        val = df.iloc[-1]
        precio, rsi, sma50 = val['Close'], val['RSI'], val['SMA50']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Precio", f"${precio:,.2f}")
        c2.metric("RSI (14)", f"{rsi:.2f}")
        c3.metric("Tendencia", "📈 ALCISTA" if precio > sma50 else "📉 BAJISTA")

        # Gráfico
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange'), name="SMA50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
        
        fig.update_layout(height=450, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"⚠️ No se pudo conectar con Binance para {nombre}")
