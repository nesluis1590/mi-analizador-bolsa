import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

st.set_page_config(page_title="Crypto Tracker Pro", layout="wide")

def obtener_datos_limpios(ticker):
    try:
        # 1. Descarga con auto_adjust activo
        data = yf.download(ticker, period="2d", interval="5min", auto_adjust=True, progress=False)
        
        if data.empty:
            return None
        
        # 2. LIMPIEZA CRÍTICA: Eliminamos los niveles extra de las columnas
        # Esto soluciona el error de "Buscando señal..."
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # 3. Aseguramos que las columnas tengan los nombres correctos
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # 4. Cálculo de indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df.dropna()
    except Exception as e:
        st.error(f"Error técnico detectado: {e}")
        return None

# --- INTERFAZ ---
tz = pytz.timezone('America/Caracas')
st.title("₿ Monitor Cripto en Tiempo Real")
st.write(f"Sincronizado con Caracas: {datetime.now(tz).strftime('%I:%M %p')}")

activos = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        df = obtener_datos_limpios(ticker)
        
        if df is not None and not df.empty:
            ultimo = df.iloc[-1]
            precio = float(ultimo['Close'])
            rsi = float(ultimo['RSI'])
            
            st.metric(f"Precio {nombre}", f"${precio:,.2f}")
            
            # Gráfico de Velas
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], 
                low=df['Low'], close=df['Close'], name="Precio"
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
            
            fig.update_layout(height=500, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"❌ No se pudieron recibir datos de {nombre}. Verifica la conexión.")
