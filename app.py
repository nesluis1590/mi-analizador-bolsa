import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- 1. CONFIGURACIÓN DE CREDENCIALES ---
API_KEY_ALPHA = "LZAJW21LIGQNRQA4"
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"
TELEGRAM_CHAT_ID = "841967788"

st.set_page_config(page_title="Scalper Pro 5m - NDX/SPX", layout="wide")

# --- 2. FUNCIONES CORE ---
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})
    except:
        pass

def obtener_datos_5min(symbol):
    # Función específica para 5 minutos (Intraday)
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={API_KEY_ALPHA}&outputsize=compact'
    try:
        r = requests.get(url).json()
        
        # Alpha Vantage entrega los datos de 5min bajo esta clave exacta
        key = "Time Series (5min)"
        if key not in r:
            if "Note" in r: st.error(f"⚠️ Límite de API alcanzado para {symbol}. Espera 60s.")
            return None
        
        df = pd.DataFrame.from_dict(r[key], orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float).iloc[::-1] # Ordenar de más antiguo a más reciente
        
        # Indicadores Técnicos
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        
        return df
    except Exception as e:
        st.error(f"Error de conexión en {symbol}: {e}")
        return None

# --- 3. INTERFAZ DE USUARIO ---
st.title("🏛️ Scalper Pro: NASDAQ & S&P 500 (5 min)")
st.info(f"Escaneando señales de alta precisión cada 5 minutos. Horario VET: {time.strftime('%H:%M')}")

activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        # Pausa de 2 segundos entre activos para no saturar la API gratuita
        if i > 0: time.sleep(2)
        
        df = obtener_datos_5min(ticker)
        
        if df is not None:
            val = df.iloc[-1]
            precio = val['Close']
            rsi = val['RSI']
            mfi = val['MFI']
            sma50 = val['SMA50']
            
            # Lógica de Tendencia y Señal
            tendencia = "📈 ALCISTA" if precio > sma50 else "📉 BAJISTA"
            
            st.subheader(f"{nombre} (5m)")
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("Tendencia", tendencia)
            m3.metric("RSI", f"{rsi:.1f}")

            # --- SISTEMA DE ALERTAS ---
            mensaje_alerta = ""
            # Definimos niveles de 35/65 para 5min (puedes bajarlos a 30/70 si quieres menos señales)
            if rsi < 35 and mfi < 35:
                st.success("🟢 SEÑAL DE COMPRA (LONG)")
                mensaje_alerta = f"🚀 *SCALP COMPRA* en {nombre} (5m)\nPrecio: ${precio:.2f}\nRSI: {rsi:.1f} | MFI: {mfi:.1f}\nTendencia: {tendencia}"
            elif rsi > 65 and mfi > 65:
                st.error("🔴 SEÑAL DE VENTA (SHORT)")
                mensaje_alerta = f"📉 *SCALP VENTA* en {nombre} (5m)\nPrecio: ${precio:.2f}\nRSI: {rsi:.1f} | MFI: {mfi:.1f}\nTendencia: {tendencia}"
            else:
                st.write("⏱️ Buscando entrada...")

            # Botón para enviar la alerta actual a Telegram
            if mensaje_alerta != "":
                if st.button(f"Enviar Alerta {ticker} a Telegram"):
                    enviar_telegram(mensaje_alerta)
                    st.toast("¡Mensaje enviado!")

            # --- GRÁFICO ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            
            # Velas y SMA50
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="Tendencia"), row=1, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(height=500, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Cargando datos de {ticker}... Si tarda, refresca en 1 minuto.")
