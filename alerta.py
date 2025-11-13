import requests
import sys
import json

def revisar_lluvia():
    # NO necesitas API key con wttr.in
    ciudad = "Santiago,Chile"  # Usá ciudad y país para precisión
    
    try:
        # URL de wttr.in con formato JSON
        url = f"https://wttr.in/{ciudad}?format=j1"
        
        print(f"🔍 Consultando clima para: {ciudad}")
        print(f"📡 URL: {url}")
        
        # Hacer la petición
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Lanza error si status != 200
        
        # Parsear JSON
        data = response.json()
        
        # Debug: mostrar estructura completa (útil para ver qué hay)
        print(f"📦 Respuesta completa:\n{json.dumps(data, indent=2)}")
        
        # Obtener datos actuales
        current = data.get("current_condition", [{}])[0]
        temp_actual = current.get("temp_C", "N/A")
        humedad = current.get("humidity", "N/A")
        chance_rain_hoy = current.get("chanceofrain", "N/A")
        
        print(f"\n🌡️ Temperatura actual: {temp_actual}°C")
        print(f"💧 Humedad: {humedad}%")
        print(f"🌧️ Probabilidad lluvia HOY: {chance_rain_hoy}%")
        
        # Obtener datos por hora (forecast)
        # wttr.in devuelve 3 días de datos, tomamos el primero
        forecast = data.get("weather", [{}])[0]
        hourly_data = forecast.get("hourly", [])
        
        print(f"\n⏰ Próximas 6 horas:")
        alertas = 0
        
        for i, hour in enumerate(hourly_data[:6]):
            # wttr.in usa 'chanceofrain' como string
            pop = int(hour.get("chanceofrain", "0"))
            temp = hour.get("tempC", "N/A")
            hora_local = hour.get("time", "N/A")
            
            print(f"   {hora_local}: Temp {temp}°C - Lluvia {pop}%")
            
            if pop > 50:
                alertas += 1
        
        # Resumen final
        print(f"\n{'='*50}")
        if alertas > 0:
            print(f"⚠️  ALERTA: {alertas} horas con >50% probabilidad de lluvia")
            sys.exit(1)  # Marca el workflow como "fallido" para que lo veas
        else:
            print("✅ No se esperan lluvias fuertes en las próximas 6 horas")
        print(f"{'='*50}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    revisar_lluvia()
