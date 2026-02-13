import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Nasdaq & SP500 Live", layout="wide")

# 1. ACTUALIZACIÓN AUTOMÁTICA (Cada 60 segundos)
# Nota: Esto hará que la app se ejecute sola cada minuto
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.title("🏛️ Escáner en Tiempo Real")
st.write(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# 2. SELECCIÓN DE ÍNDICES
indices = {
    "NASDAQ 100 (Top)": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO", "PEP", "COST"],
    "S&P 500 (Top)": ["JPM", "V", "MA", "PG", "HD", "UNH", "LLY", "ABBV", "BAC", "XOM"]
}

seleccion = st.sidebar.selectbox("Índice a escanear", list(indices.keys()))
tickers = indices[seleccion]

# 3. FUNCIÓN DE CÁLCULO
@st.cache_data(ttl=60) # Guarda los datos por 60 seg para no saturar
def obtener_datos(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False) # Intervalo de 1 minuto para "Tiempo Real"
    hist = yf.download(symbol, period="1mo", interval="1d", progress=False) # Para indicadores diarios
    if df.empty or hist.empty: return None
    
    # Indicadores en el histórico diario
    hist['RSI'] = ta.rsi(hist['Close'], length=14)
    hist['MFI'] = ta.mfi(hist['High'], hist['Low'], hist['Close'], hist['Volume'], length=14)
    
    return {"actual": df, "indicadores": hist}

# 4. TABLA DE MONITOREO
resumen = []
for t in tickers:
    data_dict = obtener_datos(t)
    if data_dict:
        precio_actual = data_dict["actual"]['Close'].iloc[-1]
        rsi_val = data_dict["indicadores"]['RSI'].iloc[-1]
        mfi_val = data_dict["indicadores"]['MFI'].iloc[-1]
        
        estado = "Neutral"
        if rsi_val < 35: estado = "🟢 SOBREVENTA"
        elif rsi_val > 65: estado = "🔴 SOBRECOMPRA"
        
        resumen.append({
            "Activo": t,
            "Precio": f"${precio_actual:.2f}",
            "RSI": round(rsi_val, 1),
            "MFI": round(mfi_val, 1),
            "Señal": estado
        })

st.table(pd.DataFrame(resumen))

# 5. GRÁFICO INTERACTIVO DE VELAS (1 MINUTO)
st.divider()
target = st.selectbox("Ver gráfico detallado (1 min):", tickers)
data_graf = obtener_datos(target)

if data_graf:
    df_m = data_graf["actual"]
    fig = go.Figure(data=[go.Candlestick(
        x=df_m.index, open=df_m['Open'], high=df_m['High'],
        low=df_m['Low'], close=df_m['Close'], name="1 min"
    )])
    
    fig.update_layout(
        title=f"Gráfico Intradía: {target}",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
