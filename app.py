import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración de la App
st.set_page_config(page_title="Índices Live Pro", layout="wide")

# API KEY (Consíguela gratis en alphavantage.co)
API_KEY = "O3WS2QJRIR0DDWLG"

st.title("🏛️ Monitor Maestro: NASDAQ 100 & S&P 500")
st.write("Análisis de alta precisión basado en volumen institucional.")

# Diccionario de traducción (ETF de referencia para los índices)
activos = {
    "NASDAQ 100 (NDX)": "QQQ",
    "S&P 500 (SPX)": "SPY"
}

def obtener_datos_alpha(symbol):
    try:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact'
        r = requests.get(url)
        data = r.json()
        
        if "Time Series (Daily)" not in data:
            st.error(f"Error de API en {symbol}. Verifica tu clave o límite de tiempo.")
            return None
        
        # Procesar datos
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float)
        df = df.iloc[::-1] # Ordenar cronológicamente
        
        # Indicadores Técnicos
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- INTERFAZ ---
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        st.subheader(nombre)
        df = obtener_datos_alpha(ticker)
        
        if df is not None:
            ultimo = df.iloc[-1]
            precio = ultimo['Close']
            rsi_val = ultimo['RSI']
            mfi_val = ultimo['MFI']
            
            # Métricas rápidas
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("RSI", f"{rsi_val:.1f}")
            m3.metric("MFI (Vol)", f"{mfi_val:.1f}")
            
            # Alertas visuales
            if rsi_val < 35 and mfi_val < 35:
                st.success(f"🔥 SEÑAL: {nombre} en Sobreventa Extrema")
            elif rsi_val > 65 and mfi_val > 65:
                st.error(f"⚠️ SEÑAL: {nombre} en Sobrecompra Extrema")
            else:
                st.info("Estado: Tendencia Neutral")

            # Gráfico avanzado
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Velas
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='yellow', width=1), name="EMA 20"), row=1, col=1)
            
            # RSI y MFI juntos abajo
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='cyan')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MFI'], name="MFI", line=dict(color='magenta')), row=2, col=1)
            
            fig.update_layout(height=500, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
