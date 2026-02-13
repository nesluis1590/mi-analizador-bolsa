import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go

# Configuración visual
st.set_page_config(page_title="Scanner Total", layout="wide")
st.title("🏛️ Escáner NASDAQ & S&P 500")

# 1. Listas de Activos
indices = {
    "NASDAQ 100": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO", "PEP", "COST"],
    "S&P 500": ["JPM", "V", "MA", "PG", "HD", "UNH", "LLY", "ABBV", "BAC", "XOM"]
}

seleccion = st.sidebar.selectbox("Selecciona Índice", list(indices.keys()))
tickers = indices[seleccion]

# 2. Función de Descarga Mejorada
def obtener_datos(symbol):
    try:
        # Descargamos 60 días para asegurar que los indicadores tengan datos de sobra
        df = yf.download(symbol, period="60d", interval="1d", progress=False, multi_level=False)
        
        if df.empty or len(df) < 20:
            return None
        
        # Limpieza de datos por si vienen columnas duplicadas
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        # Calculamos indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        
        return df
    except Exception as e:
        return None

# 3. Procesamiento
resumen = []

with st.spinner('Escaneando mercado...'):
    for t in tickers:
        df = obtener_datos(t)
        
        if df is not None:
            # Tomamos el último valor que no sea nulo
            ultimo_val = df.dropna(subset=['RSI', 'MFI']).iloc[-1]
            
            precio = ultimo_val['Close']
            rsi_val = ultimo_val['RSI']
            mfi_val = ultimo_val['MFI']

            # Lógica de señales
            if rsi_val < 30: señal = "🟢 COMPRA"
            elif rsi_val > 70: señal = "🔴 VENTA"
            else: señal = "Neutral"

            resumen.append({
                "Activo": t,
                "Precio": f"${float(precio):.2f}",
                "RSI": round(float(rsi_val), 1),
                "MFI": round(float(mfi_val), 1),
                "Señal": señal
            })

# 4. Mostrar Resultados
if resumen:
    st.table(pd.DataFrame(resumen))
    
    st.divider()
    target = st.selectbox("Analizar gráfico de:", [r['Activo'] for r in resumen])
    df_graf = obtener_datos(target)
    
    if df_graf is not None:
        fig = go.Figure(data=[go.Candlestick(
            x=df_graf.index, open=df_graf['Open'], high=df_graf['High'],
            low=df_graf['Low'], close=df_graf['Close']
        )])
        fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Error de conexión con Yahoo Finance. Intenta cambiar de índice en el menú lateral.")
