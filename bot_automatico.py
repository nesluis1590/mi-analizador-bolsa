import os
import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz

# Configuración (Usa tus claves aquí)
API_KEY_ALPHA = "FZEZWV0VBR5BN4Y7"
TELEGRAM_TOKEN = "8216027796:AAGLDodiewu80muQFo1s0uDXl3tf5aiK5ew"
TELEGRAM_CHAT_ID = "841967788"

activos = {"NASDAQ 100": "QQQ", "S&P 500": "SPY"}

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})

def analizar():
    for nombre, ticker in activos.items():
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY_ALPHA}&outputsize=compact'
        r = requests.get(url).json()
        
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r["Time Series (Daily)"], orient='index')
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float).iloc[::-1]
            
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            mfi = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14).iloc[-1]
            precio = df['Close'].iloc[-1]

            # Lógica de señales
            if rsi < 35 and mfi < 35:
                enviar_telegram(f"🚀 *OPORTUNIDAD ALZA EN {nombre}*\nPrecio: ${precio:.2f}\nRSI: {rsi:.1f} | MFI: {mfi:.1f}")
            elif rsi > 65 and mfi > 65:
                enviar_telegram(f"📉 *RIESGO BAJA EN {nombre}*\nPrecio: ${precio:.2f}\nRSI: {rsi:.1f} | MFI: {mfi:.1f}")

if __name__ == "__main__":
    # Verificar horario de Venezuela (VET)
    venezuela_tz = pytz.timezone('America/Caracas')
    hora_ve = datetime.now(venezuela_tz).hour
    
    # Solo ejecuta entre las 10 AM y las 12 PM
    if 10 <= hora_ve <= 12:
        analizar()
