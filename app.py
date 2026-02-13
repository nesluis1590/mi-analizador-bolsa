import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Índices Master Scanner", layout="wide")

st.title("🏛️ Escáner de Índices Mayores")
st.write("Análisis de sobrecompra/venta con Volumen (MFI) y RSI")

# 1. Listas de Tickers (Simplificadas para velocidad)
indices = {
    "NASDAQ 100 (Top)": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO", "PEP", "COST"],
    "S&P 500 (Top)": ["JPM", "V", "MA", "PG", "HD", "UNH", "LLY", "ABBV", "BAC", "XOM"]
}

seleccion = st.sidebar.selectbox("Selecciona el Índice a escanear", list(indices.keys()))
tickers = indices[seleccion]

# 2. Función de descarga segura
def obtener_datos(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if len(df) < 20: return None
        
        # Calculamos indicadores
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        return df
    except:
        return None

# 3. Proceso de Escaneo
st.subheader(f"Analizando componentes de {seleccion}")
resumen = []

for t in tickers:
    data = obtener_datos(t)
    if data is not None:
        # Extraemos valores asegurando que sean números puros
        try:
            ultimo_cierre = float(data['Close'].iloc[-1])
            rsi_actual = float(data['RSI'].iloc[-1])
            mfi_actual = float(data['MFI'].iloc[-1])
            
            # Lógica de señales
            if rsi_actual < 30 and mfi_actual < 30:
                señal = "🔥 SOBREVENTA (Compra)"
            elif rsi_actual > 70 and mfi_actual > 70:
                señal = "⚠️ SOBRECOMPRA (Venta)"
            else:
                señal = "Neutral"
            
            resumen.append({
                "Activo": t,
                "Precio": f"{ultimo_cierre:.2f}",
                "RSI": round(rsi_actual, 1),
                "MFI (Vol)": round(mfi_actual, 1),
                "Señal": señal
            })
        except:
            continue

# 4. Mostrar Resultados
if resumen:
    df_final = pd.DataFrame(resumen)
    
    # Aplicar color a las señales
    def color_señal(val):
        if 'Compra' in val: return 'background-color: #004d00'
        if 'Venta' in val: return 'background-color: #4d0000'
        return ''

    st.table(df_final.style.applymap(color_señal, subset=['Señal']))
else:
    st.error("No se pudieron cargar los datos. Intenta refrescar la página.")

# 5. Gráfico rápido del primero de la lista
st.divider()
st.subheader(f"Gráfico de Referencia: {tickers[0]}")
df_graf = obtener_datos(tickers[0])
if df_graf is not None:
    fig = go.Figure(data=[go.Candlestick(x=df_graf.index,
                open=df_graf['Open'], high=df_graf['High'],
                low=df_graf['Low'], close=df_graf['Close'])])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
