import os
import requests
import sys

def revisar_lluvia():
    # 1. OBTENER API KEY (debe coincidir exactamente con tu YAML)
    API_KEY = os.getenv('OWM_API_KEY')
    
    # 2. DEBUG INICIAL - NO BORRAR hasta que funcione
    print("=" * 50)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 50)
    print(f"• Variable OWM_API_KEY configurada: {'✅ SÍ' if API_KEY else '❌ NO'}")
    
    if not API_KEY:
        print("\n❌ ERROR CRÍTICO: La API key no está llegando al script.")
        print("  → Revisá que el secreto en GitHub se llame exactamente: OWM_API_KEY")
        print("  → La ejecución se detiene aquí.")
        sys.exit(1)  # Detiene el workflow con error
    
    print(f"• API Key (oculta): {API_KEY[:5]}...{API_KEY[-5:]}")
    
    # 3. CONFIGURAR LA LLAMADA A LA API
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        'lat': -33.4489,  # Santiago de Chile (cambiá si necesitás otra ubicación)
        'lon': -70.6693,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'es',
        'exclude': 'current,minutely,daily,alerts'  # Opcional: reduce el tamaño
    }
    
    print(f"\n• URL solicitada: {url}")
    print(f"• Parámetros: {params}")
    
    # 4. HACER LA PETICIÓN
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"\n📡 Status Code: {response.status_code}")
        
        # Convertir a JSON
        resp = response.json()
        print(f"📦 Respuesta completa: {resp}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR DE CONEXIÓN: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        sys.exit(1)
    
    # 5. VERIFICAR QUE EXISTE 'HOURLY'
    if "hourly" not in resp:
        print(f"\n❌ KeyError: 'hourly' no existe en la respuesta")
        print(f"   Claves disponibles: {list(resp.keys())}")
        
        # Mensaje específico según el error común
        if resp.get('cod') == 401:
            print("\n💡 SOLUCIÓN: API Key inválida. Regenerala en OpenWeatherMap")
        elif resp.get('cod') == 429:
            print("\n💡 SOLUCIÓN: Límite de llamadas excedido. Esperá 10 min o usa key de pago")
        elif 'message' in resp:
            print(f"\n💡 Mensaje de la API: {resp['message']}")
        
        sys.exit(1)
    
    print(f"\n✅ 'hourly' encontrado con {len(resp['hourly'])} registros")
    
    # 6. PROCESAR DATOS (tu lógica original)
    print("\n" + "=" * 50)
    print("🌧️  ANÁLISIS DE LLUVIA")
    print("=" * 50)
    
    alertas_encontradas = 0
    
    for i, hour in enumerate(resp["hourly"][:12]):  # Próximas 12 horas
        pop = hour.get("pop", 0)  # Probability of Precipitation (0-1)
        temp = hour.get("temp", 0)
        time = hour.get("dt", 0)  # Timestamp
        
        if pop > 0.5:  # Más del 50% de probabilidad
            print(f"⏰ Hora {i}: ⚠️  ALERTA - Prob. lluvia: {pop*100:.0f}% - Temp: {temp}°C")
            alertas_encontradas += 1
    
    # 7. RESUMEN FINAL
    print("\n" + "=" * 50)
    if alertas_encontradas == 0:
        print("✅ No se esperan lluvias fuertes en las próximas horas")
    else:
        print(f"⚠️  Se encontraron {alertas_encontradas} períodos con alta probabilidad de lluvia")
    print("=" * 50)

if __name__ == "__main__":
    revisar_lluvia()
