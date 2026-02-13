import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go

# Configuración básica
st.set_page_config(page_title="Scanner Live", layout="wide")

st.title("🏛️ Escáner NASDAQ & S&P 500")

# 1. Listas de Activos
indices = {
    "NASDAQ 100": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO", "PEP", "COST"],
    "S&P 500": ["JPM", "V", "MA", "PG", "HD", "UNH", "LLY", "ABBV", "BAC", "XOM"]
}

seleccion = st.sidebar.selectbox("Índice", list(indices.keys()))
tickers = indices[seleccion]

# 2. Función Robusta de Datos
def obtener_datos_seguros(symbol):
    try:
        # Descargamos un poco más de datos para asegurar que los indicadores se calculen
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 15:
            return None
        
        # Calcular indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        return df
    except:
        return None

# 3. Construcción de la Tabla
resumen = []
st.write("### 🔍 Análisis de Indicadores")

for t in tickers:
    df = obtener_datos_seguros(t)
    
    if df is not None:
        # Usamos .iloc[-1] pero verificamos que no sea NaN
        rsi_val = df['RSI'].iloc[-1]
        mfi_val = df['MFI'].iloc[-1]
        precio = df['Close'].iloc[-1]

        # Validamos que los valores sean números antes de comparar
        if pd.isna(rsi_val) or pd.isna(mfi_val):
            continue

        # Lógica de señales
        if rsi_val < 35: 
            estado = "🟢 COMPRA"
        elif rsi_val > 65: 
            estado = "🔴 VENTA"
        else: 
            estado = "Neutral"

        resumen.append({
            "Activo": t,
            "Precio": f"${float(precio):.2f}",
            "RSI": round(float(rsi_val), 1),
            "MFI": round(float(mfi_val), 1),
            "Señal": estado
        })

if resumen:
    st.table(pd.DataFrame(resumen))
else:
    st.warning("No hay datos disponibles en este momento (posible mercado cerrado).")

# 4. Gráfico Visual
st.divider()
if resumen:
    target = st.selectbox("Ver Gráfico:", [r['Activo'] for r in resumen])
    df_graf = obtener_datos_seguros(target)
    
    fig = go.Figure(data=[go.Candlestick(
        x=df_graf.index, open=df_graf['Open'], high=df_graf['High'],
        low=df_graf['Low'], close=df_graf['Close']
    )])
    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
