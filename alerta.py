import requests
import json
import os

# --- CONFIGURACIÓN (reemplaza los valores ENTRE comillas) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OWM_API_KEY = os.getenv("OWM_API_KEY")
LAT = "7.041866"   # ← TU LATITUD AQUÍ
LON = "-73.851708"   # ← TU LONGITUD AQUÍ
# -----------------------------------------------------------

def enviar_mensaje(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": texto}
    requests.post(url, data=data)

def revisar_lluvia():
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={LAT}&lon={LON}&exclude=current,minutely,daily,alerts&appid={OWM_API_KEY}&units=metric"
    resp = requests.get(url).json()
    
    # Revisar los primeros 2 periodos (0-30 min y 30-60 min)
    for i in range(2):
        pop = resp["hourly"][i].get("pop", 0)
        if pop >= 0.6:
            enviar_mensaje("🌧️ ¡Atención! Probabilidad de lluvia ≥60% en menos de 1 hora. ¡Recoge la ropa!")
            return
    print("No hay lluvia prevista.")

if __name__ == "__main__":
    revisar_lluvia()
