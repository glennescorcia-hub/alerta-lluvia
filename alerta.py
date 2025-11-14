import os
import requests
import sys
from datetime import datetime, timedelta

def enviar_telegram(mensaje):
    """Envía mensaje Telegram"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Secrets no configurados")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'Markdown'}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return False
        print("✅ Mensaje enviado")
        return True
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def revisar_lluvia():
    # === MODO PRUEBA 6 AM: Descomentá para probar ahora ===
    hora_actual = 6
    
    # === MODO AUTOMÁTICO ===
    # hora_actual = (datetime.utcnow() - timedelta(hours=5)).hour
    
    print(f"="*60)
    print(f"🔍 BARRANCABERMEJA - Hora Colombia: {hora_actual:02d}:00")
    print(f"="*60)
    
    try:
        # Datos de wttr.in
        url = f"https://wttr.in/Barrancabermeja,Colombia?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Datos actuales
        current = data["current_condition"][0]
        precip_hoy = float(current.get("precipMM", 0))
        chance_hoy = current.get("chanceofrain")
        if chance_hoy is None:
            chance_hoy = 100 if precip_hoy > 0 else 0
        else:
            chance_hoy = int(chance_hoy)
        
        print(f"🌧️ CONDICIÓN ACTUAL: {precip_hoy}mm - Probabilidad: {chance_hoy}%")
        
        # Datos horarios
        forecast = data["weather"][0]
        hourly_data = forecast["hourly"]
        
        # === LÓGICA DE ENVÍO ===
        mensaje = None
        
        # CRITERIO 1: Resumen a las 6 AM
        if hora_actual == 6:
            print("🌅 MODO: Resumen matutino")
            mensaje = f"🌧️ *Resumen Matutino - Barrancabermeja*\n\n"
            mensaje += f"📅 HOY:\n• Precipitación: {precip_hoy}mm\n• Probabilidad: {chance_hoy}%\n\n"
            
            print("📊 Analizando próximas 12 horas...")
            horas_riesgo = []
            
            for i, hour in enumerate(hourly_data[:12]):
                precip = float(hour.get("precipMM", 0))
                chance = hour.get("chanceofrain")
                hora_utc = int(hour["time"])
                
                if chance is None:
                    chance = 100 if precip > 0 else 0
                else:
                    chance = int(chance)
                
                # Convertir hora UTC a Colombia
                hora_col = hora_utc - 500
                if hora_col < 0:
                    hora_col += 2400
                
                print(f"  [{i}] Hora {hora_col:04d}: Precip {precip}mm - Prob {chance}%")
                
                if chance > 50 or precip > 0.5:
                    horas_riesgo.append(f"⏰ {hora_col:04d}: *Precip {precip}mm ({chance}%)*")
            
            if horas_riesgo:
                mensaje += "⚠️ *Horas con riesgo:*\n" + "\n".join(horas_riesgo)
            else:
                mensaje += "✅ No se esperan lluvias significativas hoy"
        
        # CRITERIO 2: Alerta 1 hora antes
        else:
            print("🔍 MODO: Buscando lluvia en próxima hora...")
            
            # Buscar en el próximo periodo
            for i, hour in enumerate(hourly_data):
                precip = float(hour.get("precipMM", 0))
                chance = hour.get("chanceofrain")
                hora_utc = int(hour["time"])
                
                if chance is None:
                    chance = 100 if precip > 0 else 0
                else:
                    chance = int(chance)
                
                # Convertir hora UTC a Colombia
                hora_col = hora_utc - 500
                if hora_col < 0:
                    hora_col += 2400
                
                # Obtener solo la hora numérica (0-23)
                hora_col_num = hora_col // 100
                
                # DEBUG: Mostrar cada hora
                print(f"  [{i}] Hora {hora_col:04d} (num: {hora_col_num}) - Precip {precip}mm - Prob {chance}%")
                
                # Evaluar si falta EXACTAMENTE 1 hora
                hora_siguiente = (hora_actual + 1) % 24
                if hora_col_num == hora_siguiente and (chance > 50 or precip > 0.5):
                    print(f"  ✓ ALERTA DETECTADA: Lluvia a las {hora_siguiente:02d}:00")
                    mensaje = f"⏰ *Alerta Inminente - Barrancabermeja*\n\n"
                    mensaje += f"¡Lluvia intensa en ~1 hora!\n\n"
                    mensaje += f"⏰ Hora {hora_col:04d}: *Precip {precip}mm ({chance}%)*"
                    break  # Solo la primera alerta
        
        # CRITERIO 3: Sin alertas
        if mensaje is None:
            print("✅ Sin condiciones de alerta")
            sys.exit(0)
        
        # Enviar mensaje
        print(f"\nMensaje a enviar:\n{mensaje}\n")
        enviar_telegram(mensaje)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(0)

if __name__ == "__main__":
    revisar_lluvia()
