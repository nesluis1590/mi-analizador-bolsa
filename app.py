import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(page_title="Índices Live Pro", layout="wide")

# CONFIGURACIÓN
API_KEY = "O3WS2QJRIR0DDWLG" # Asegúrate de que no tenga espacios
activos = {"NASDAQ 100 (QQQ)": "QQQ", "S&P 500 (SPY)": "SPY"}

st.title("🏛️ Monitor Maestro: NDX & SPX")

def obtener_datos_api(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact'
    try:
        response = requests.get(url)
        data = response.json()
        
        # Si la API nos frena por límite de tiempo
        if "Note" in data:
            st.warning(f"Límite de API alcanzado para {symbol}. Espera 60 segundos.")
            return None
            
        if "Time Series (Daily)" not in data:
            st.error(f"No se encontraron datos para {symbol}. Revisa tu API Key.")
            return None

        # Procesamiento de datos
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1] # Orden cronológico
        
        # Indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- EJECUCIÓN ---
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        st.subheader(nombre)
        
        # Pequeña pausa para no saturar la API gratuita
        if i > 0:
            time.sleep(2) 
            
        df = obtener_datos_api(ticker)
        
        if df is not None:
            # Extraer últimos valores
            ultimo = df.iloc[-1]
            precio, rsi_v, mfi_v = ultimo['Close'], ultimo['RSI'], ultimo['MFI']
            
            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("RSI", f"{rsi_v:.1f}")
            m3.metric("MFI", f"{mfi_v:.1f}")

            # Gráfico interactivo
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='cyan')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MFI'], name="MFI", line=dict(color='magenta')), row=2, col=1)
            
            fig.update_layout(height=400, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
