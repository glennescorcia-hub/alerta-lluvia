import os
import requests
import sys

def enviar_telegram(mensaje):
    """Envía mensaje Telegram con manejo de errores detallado"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not token or not chat_id:
        print("❌ ERROR: Secrets TELEGRAM_TOKEN o CHAT_ID no configurados")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Status Code: {response.status_code}")
        
        # Si hay error, mostramos el detalle
        if response.status_code != 200:
            print(f"Telegram Error Response: {response.text}")
            return False
        
        print("✅ Mensaje enviado a Telegram")
        return True
    except Exception as e:
        print(f"❌ Telegram Exception: {e}")
        return False

def revisar_lluvia():
    # CIUDAD ESPECÍFICA (URL-encoded para seguridad)
    ciudad = "Barrancabermeja,Colombia"
    print(f"🔍 Consultando clima para: {ciudad}")
    
    try:
        # Llamada a wttr.in
        url = f"https://wttr.in/{ciudad}?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Datos recibidos de wttr.in")
        
        # --- MANEJO DE DATOS DE BARRANCABERMEJA ---
        # Intentar obtener probabilidad de lluvia (no siempre está disponible)
        current = data.get("current_condition", [{}])[0]
        
        # wttr.in en Colombia a veces no devuelve 'chanceofrain'
        # Alternativa: verificar si hay precipitación prevista
        precip_mm = float(current.get("precipMM", 0))  # Milímetros de lluvia
        chance_rain = current.get("chanceofrain")
        
        # Si no hay chanceofrain, inferir de precipMM
        if chance_rain is None or chance_rain == "":
            chance_rain = 100 if precip_mm > 0 else 0
            print(f"⚠️ 'chanceofrain' no disponible, usando precipMM: {precip_mm}mm")
        else:
            chance_rain = int(chance_rain)
        
        # --- ANALISIS POR HORA ---
        forecast = data.get("weather", [{}])[0]
        hourly_data = forecast.get("hourly", [])
        
        alertas = []
        print(f"\n⏰ Próximas 12 horas en Barrancabermeja:")
        
        for i, hour in enumerate(hourly_data[:12]):
            # Manejo seguro de datos por hora
            hora = hour.get("time", f"H{i}")
            temp = hour.get("tempC", "N/A")
            precip = float(hour.get("precipMM", 0))
            
            # Intentar obtener chanceofrain, sino inferir
            chance = hour.get("chanceofrain")
            if chance is None or chance == "":
                chance = 100 if precip > 0 else 0
            else:
                chance = int(chance)
            
            print(f"   {hora}: Temp {temp}°C - Precip {precip}mm - Prob {chance}%")
            
            # Alerta si hay precipitación >0.5mm o chance>50%
            if precip > 0.5 or chance > 50:
                alertas.append(f"⏰ {hora}: *Precip {precip}mm ({chance}%)*")
        
        # --- CONSTRUIR MENSAJE ---
        mensaje = f"🌧️ *Alerta Clima - Barrancabermeja*\n\n"
        mensaje += f"Condición actual:\n"
        mensaje += f"• Precipitación: {precip_mm}mm\n"
        mensaje += f"• Probabilidad: {chance_rain}%\n\n"
        
        if alertas:
            mensaje += "⚠️ *ALERTA - Próximas 12 horas:*\n"
            mensaje += "\n".join(alertas)
        else:
            mensaje += "✅ No se esperan lluvias significativas en 12 horas"
        
        print(f"\nMensaje final:\n{mensaje}\n")
        
        # Enviar Telegram
        enviar_telegram(mensaje)
        
        # Exit code 1 si hay alertas
        sys.exit(1 if alertas else 0)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando a wttr.in: {e}")
        enviar_telegram("❌ Error: No se pudo conectar a wttr.in")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    revisar_lluvia()
