def revisar_lluvia():
    API_KEY = os.getenv('OPENWEATHER_API_KEY')
    
    # ----- DEBUG: Esto te mostrará el problema -----
    print("=== DEBUG INFO ===")
    print(f"API Key presente: {'Sí' if API_KEY else 'NO'}")
    print(f"API Key valor: {API_KEY[:5]}... (oculta)" if API_KEY else "API Key es None")
    
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        'lat': -33.4489,
        'lon': -70.6693,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'es'
    }
    
    print(f"Haciendo request a: {url}")
    print(f"Con parámetros: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status code: {response.status_code}")
        
        # Imprime la respuesta COMPLETA para ver qué contiene
        resp = response.json()
        print(f"Respuesta JSON completa: {resp}")
        
        # AHORA verificamos si 'hourly' existe
        if "hourly" not in resp:
            print(f"❌ ERROR: La clave 'hourly' NO existe en la respuesta")
            print(f"Claves disponibles: {list(resp.keys())}")
            return  # Termina la función para evitar el crash
        
        # Si llegamos aquí, todo está bien
        for i in range(len(resp["hourly"])):
            pop = resp["hourly"][i].get("pop", 0)
            print(f"Hora {i}: Probabilidad de lluvia = {pop}")
            
    except Exception as e:
        print(f"❌ Excepción capturada: {e}")
        import traceback
        traceback.print_exc()
