import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go

# Configuración
st.set_page_config(page_title="Scanner Pro Alpha", layout="wide")
API_KEY = "O3WS2QJRIR0DDWLG" # <--- PEGA AQUÍ TU CLAVE DE ALPHA VANTAGE

st.title("🏛️ Escáner Profesional (Alpha Vantage)")

indices = {
    "NASDAQ 100": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
    "S&P 500": ["JPM", "V", "PG", "HD", "XOM"]
}

seleccion = st.sidebar.selectbox("Selecciona Índice", list(indices.keys()))
tickers = indices[seleccion]

def obtener_datos_alpha(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=compact'
    r = requests.get(url)
    data = r.json()
    
    if "Time Series (Daily)" not in data:
        return None
    
    # Convertir JSON a DataFrame de Pandas
    df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient='index')
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype(float)
    df = df.iloc[::-1] # Invertir para que el orden sea cronológico
    
    # Calcular indicadores
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
    return df

resumen = []

if st.sidebar.button("🚀 Iniciar Escaneo"):
    for t in tickers:
        with st.spinner(f'Analizando {t}...'):
            df = obtener_datos_alpha(t)
            if df is not None:
                rsi_val = df['RSI'].iloc[-1]
                mfi_val = df['MFI'].iloc[-1]
                precio = df['Close'].iloc[-1]
                
                estado = "Neutral"
                if rsi_val < 30: estado = "🟢 COMPRA"
                elif rsi_val > 70: estado = "🔴 VENTA"
                
                resumen.append({
                    "Activo": t,
                    "Precio": f"${precio:.2f}",
                    "RSI": round(rsi_val, 1),
                    "MFI": round(mfi_val, 1),
                    "Señal": estado
                })

if resumen:
    st.table(pd.DataFrame(resumen))
else:
    st.info("Presiona el botón en el menú lateral para escanear.")
