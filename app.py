import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración de la página para móvil
st.set_page_config(page_title="Scanner Pro AI", layout="wide")

st.title("📊 Mi Analizador de Bolsa v1.0")
st.sidebar.header("Configuración")

# Selección de activos
tickers_input = st.sidebar.text_input("Lista de Tickers (separados por coma)", "AAPL, NVDA, TSLA, BTC-USD, MSFT, AMD")
tickers = [t.strip().upper() for t in tickers_input.split(",")]

periodo = st.sidebar.selectbox("Rango de tiempo", ["3mo", "6mo", "1y", "2y"], index=1)

def analizar_activo(ticker):
    df = yf.download(ticker, period=periodo, interval="1d", progress=False)
    if df.empty: return None
    
    # Cálculos
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    
    return df

# --- INTERFAZ PRINCIPAL ---
tab1, tab2 = st.tabs(["🔍 Escáner Rápido", "📈 Gráfico Detallado"])

with tab1:
    st.subheader("Estado actual del mercado")
    resumen = []
    
    import pandas as pd # Aseguramos que pandas esté disponible
    
    for t in tickers:
        datos = analizar_activo(t)
        
        if datos is not None and not datos.empty and len(datos) > 14:
            try:
                # Extraemos el último valor y lo forzamos a ser un número decimal (float)
                rsi_val = float(datos['RSI'].iloc[-1])
                mfi_val = float(datos['MFI'].iloc[-1])
                precio = float(datos['Close'].iloc[-1])
                
                # Verificamos que no sean valores nulos (NaN)
                if pd.isna(rsi_val) or pd.isna(mfi_val):
                    estado = "Calculando..."
                else:
                    estado = "Neutral"
                    if rsi_val < 35 and mfi_val < 35: 
                        estado = "COMPRA (Sobreventa)"
                    elif rsi_val > 65 and mfi_val > 65: 
                        estado = "VENTA (Sobrecompra)"
                
                resumen.append({
                    "Ticker": t, 
                    "Precio": f"${precio:.2f}", 
                    "RSI": round(rsi_val, 2), 
                    "MFI Vol": round(mfi_val, 2), 
                    "Señal": estado
                })
            except Exception as e:
                # Si algo falla con un ticker, lo saltamos y seguimos con el siguiente
                st.error(f"Error en {t}: {e}")
                continue
    
    if resumen:
        st.table(resumen)
    else:
        st.info("Escribe los Tickers en el menú lateral para empezar el escaneo.")

with tab2:
    target = st.selectbox("Selecciona activo para ver gráfico", tickers)
    df_plot = analizar_activo(target)
    
    if df_plot is not None:
        # Crear gráfico con subplots (Precio + RSI/MFI abajo)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Velas y EMA
        fig.add_trace(go.Candlestick(x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], low=df_plot['Low'], close=df_plot['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA50'], line=dict(color='yellow', width=1), name="EMA 50"), row=1, col=1)
        
        # RSI y MFI
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['RSI'], name="RSI", line=dict(color='cyan')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MFI'], name="MFI (Vol)", line=dict(color='magenta')), row=2, col=1)
        
        fig.update_layout(height=600, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
