import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(page_title="Scanner de Entradas Pro", layout="wide")

# CONFIGURACIÓN
API_KEY = "FZEZWV0VBR5BN4Y7" 
activos = {"NASDAQ 100 (QQQ)": "QQQ", "S&P 500 (SPY)": "SPY"}

st.title("🏛️ Sistema de Señales: NDX & SPX")
st.write("Confirmación basada en Impulso (RSI) y Flujo de Dinero (MFI)")

def obtener_datos_api(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact'
    try:
        response = requests.get(url)
        data = response.json()
        if "Note" in data:
            st.warning(f"Límite de API alcanzado para {symbol}. Espera un minuto.")
            return None
        if "Time Series (Daily)" not in data:
            return None

        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1]
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        return df
    except:
        return None

# --- LÓGICA DE SEÑALES ---
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        st.subheader(nombre)
        if i > 0: time.sleep(2) 
        
        df = obtener_datos_api(ticker)
        
        if df is not None:
            ultimo = df.iloc[-1]
            rsi_v, mfi_v = ultimo['RSI'], ultimo['MFI']
            
            # --- SISTEMA DE INDICACIÓN VISUAL ---
            st.write("#### 🚥 Indicador de Entrada:")
            
            # Caso 1: ALZA (Ambos indicadores en sobreventa)
            if rsi_v < 35 and mfi_v < 35:
                st.success("🚀 **SEÑAL DE ALZA (LONG)**: Mercado muy castigado. Probable rebote inminente.")
                st.balloons() # Animación de celebración
            
            # Caso 2: BAJA (Ambos indicadores en sobrecompra)
            elif rsi_v > 65 and mfi_v > 65:
                st.error("📉 **SEÑAL DE BAJA (SHORT)**: Mercado agotado. Riesgo de caída o corrección.")
            
            # Caso 3: NEUTRAL
            else:
                st.warning("⚖️ **ESPERAR**: No hay una ventaja clara. El precio está en zona de equilibrio.")

            # Mostrar métricas en tarjetas
            c1, c2 = st.columns(2)
            c1.metric("Fuerza (RSI)", f"{rsi_v:.1f}")
            c2.metric("Dinero (MFI)", f"{mfi_v:.1f}")

            # Gráfico con zonas de alerta sombreadas
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
            
            # RSI con líneas de referencia
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='cyan')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(height=450, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
