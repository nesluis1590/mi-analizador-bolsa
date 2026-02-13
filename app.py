import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf  # Nueva librería para Yahoo Finance
import requests
from requests.exceptions import RequestException
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import pytz

# --- 1. CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"  # Reemplaza con tu token real
TELEGRAM_CHAT_ID = "841967788"       # Reemplaza con tu chat ID real

st.set_page_config(page_title="Scalper Pro 5m - VET", layout="wide")

# Configuración de Hora Venezuela
venezuela_tz = pytz.timezone('America/Caracas')
hora_actual = datetime.now(venezuela_tz).strftime('%H:%M:%S')

# Cache simple para evitar llamadas repetidas (en memoria)
cache_datos = {}

# --- 2. FUNCIONES ---
def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("⚠️ Telegram no configurado. Revisa el token y chat ID.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, timeout=10)
        if response.status_code != 200:
            st.error(f"Error al enviar Telegram: {response.text}")
    except RequestException as e:
        st.error(f"Error de conexión con Telegram: {e}")

def obtener_datos_5min(symbol, max_retries=3):
    if symbol in cache_datos and (time.time() - cache_datos[symbol]['timestamp']) < 300:  # Cache de 5 minutos
        return cache_datos[symbol]['data']
    
    for attempt in range(max_retries):
        try:
            st.write(f"🔄 Intentando obtener datos de {symbol} (intento {attempt+1})...")
            # Descargar datos de Yahoo Finance: 1 día, intervalo 5m
            df = yf.download(tickers=symbol, period="1d", interval="5m", prepost=True)  # prepost=True para datos fuera de horario
            
            if df.empty:
                st.error(f"❌ No se encontraron datos para {symbol}. Verifica el símbolo o la conexión.")
                return None
            
            # Renombrar columnas para coincidir con el formato original
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            if len(df) < 50:  # Necesitamos al menos 50 filas para SMA50
                st.warning(f"⚠️ Datos insuficientes para {symbol} (solo {len(df)} filas). Mercado cerrado o datos limitados.")
                return None
            
            # Indicadores
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
            df['SMA50'] = ta.sma(df['Close'], length=50)
            
            df = df.dropna()
            if df.empty:
                st.warning(f"⚠️ No hay datos válidos después de calcular indicadores para {symbol}.")
                return None
            
            # Guardar en cache
            cache_datos[symbol] = {'data': df, 'timestamp': time.time()}
            return df
        
        except Exception as e:  # yfinance puede lanzar excepciones variadas
            st.error(f"❌ Error al descargar datos para {symbol} (intento {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial
            else:
                enviar_telegram(f"❌ Falló la obtención de datos para {symbol} después de {max_retries} intentos.")
                return None
    
    return None

# --- 3. INTERFAZ ---
st.title("🚀 Scalper Pro 5m: NDX & SPX")
st.write(f"📍 **Zona Horaria:** Caracas (UTC-4) | **Hora Actual:** {hora_actual}")

# Verificación visual del horario de mercado para el usuario
ahora = datetime.now(venezuela_tz)
es_hora_mercado = ahora.hour >= 10 and ahora.hour < 17

if not es_hora_mercado:
    st.sidebar.warning("🌙 El mercado está fuera de horario oficial (10:30 AM - 5:00 PM VET), pero intentaré cargar datos recientes.")
else:
    st.sidebar.success("☀️ Mercado Abierto")

activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}
col1, col2 = st.columns(2)

for i, (nombre, ticker) in enumerate(activos.items()):
    with [col1, col2][i]:
        if i > 0:
            time.sleep(2)  # Pequeño delay para evitar sobrecargar
        
        df = obtener_datos_5min(ticker)
        
        if df is not None and not df.empty:
            val = df.iloc[-1]
            precio, rsi, mfi, sma50 = val['Close'], val['RSI'], val['MFI'], val['SMA50']
            margen_tendencia = 0.001  # 0.1% margen para evitar ruido
            tendencia = "📈 ALCISTA" if precio > sma50 * (1 + margen_tendencia) else "📉 BAJISTA" if precio < sma50 * (1 - margen_tendencia) else "➡️ LATERAL"

            st.subheader(f"{nombre}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Precio", f"${precio:.2f}")
            m2.metric("Tendencia", tendencia)
            m3.metric("RSI", f"{rsi:.1f}")

            # Lógica de Alerta mejorada
            if rsi < 35 and mfi < 35 and precio > sma50 * (1 + margen_tendencia):
                st.success("🟢 SEÑAL DE COMPRA")
                if st.button(f"Notificar Compra {ticker}"):
                    enviar_telegram(f"🟢 *COMPRA* {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}\nRSI: {rsi:.1f}, MFI: {mfi:.1f}")
            elif rsi > 65 and mfi > 65 and precio < sma50 * (1 - margen_tendencia):
                st.error("🔴 SEÑAL DE VENTA")
                if st.button(f"Notificar Venta {ticker}"):
                    enviar_telegram(f"🔴 *VENTA* {nombre}\nPrecio: ${precio:.2f}\nTendencia: {tendencia}\nRSI: {rsi:.1f}, MFI: {mfi:.1f}")

            # --- GRÁFICO ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='orange', width=2), name="SMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='cyan'), name="RSI"), row=2, col=1)
            
            fig.update_layout(height=450, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"⏳ No se pudieron obtener datos de {ticker}. Revisa la conexión o intenta más tarde.")
