import os
import requests
import sys

def enviar_telegram(mensaje):
    """Envía mensaje a Telegram usando los secrets"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️  Advertencia: Secrets de Telegram no configurados")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Telegram: Mensaje enviado")
        return True
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def revisar_lluvia():
    # --- CONFIGURACIÓN ---
    ciudad = "Barrancabermeja,Colombia"  # <-- CAMBIA TU CIUDAD AQUÍ
    
    print(f"🔍 Consultando clima para: {ciudad}")
    
    try:
        # --- LLAMADA A WTTR.IN (SIN API KEY) ---
        url = f"https://wttr.in/{ciudad}?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # --- PROCESAR DATOS ---
        # Datos actuales
        current = data["current_condition"][0]
        chance_hoy = int(current["chanceofrain"])
        
        # Datos por hora (próximas 12 horas)
        forecast = data["weather"][0]
        hourly = forecast["hourly"]
        
        alertas = []
        for i, hour in enumerate(hourly[:12]):
            pop = int(hour["chanceofrain"])
            if pop > 50:
                alertas.append(f"Hora {hour['time']}: {pop}%")
        
        # --- CREAR MENSAJE ---
        mensaje = f"🌧️ *Alerta de Lluvia*\n\n"
        mensaje += f"Probabilidad HOY: {chance_hoy}%\n\n"
        
        if alertas:
            mensaje += "⚠️ *Horas con alta probabilidad:*\n"
            mensaje += "\n".join(alertas)
        else:
            mensaje += "✅ No se esperan lluvias fuertes (12h)"
        
        print(f"\nMensaje:\n{mensaje}\n")
        
        # --- ENVIAR TELEGRAM ---
        enviar_telegram(mensaje)
        
        # Salir con error si hay alertas (para que aparezca en GitHub)
        sys.exit(1 if alertas else 0)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Intentar enviar mensaje de error
        enviar_telegram(f"❌ Falló la alerta: {str(e)[:100]}")
        sys.exit(1)

if __name__ == "__main__":
    revisar_lluvia()
