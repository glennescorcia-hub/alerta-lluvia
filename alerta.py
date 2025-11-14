import os
import requests
import sys
from datetime import datetime

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
    # === MODO PRUEBA: FORZAR 6 AM ===
    # Descomentá esta línea para probar ahora:
    # hora_actual = 6
    
    # === MODO AUTOMÁTICO ===
    hora_actual = (datetime.utcnow() - datetime.timedelta(hours=5)).hour
    
    print(f"🔍 Barrancabermeja - Hora Colombia: {hora_actual:02d}:00")
    
    try:
        # Datos de wttr.in (siempre en UTC)
        url = "https://wttr.in/Barrancabermeja,Colombia?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Obtener datos actuales
        current = data["current_condition"][0]
        precip_hoy = float(current.get("precipMM", 0))
        chance_hoy = current.get("chanceofrain")
        if chance_hoy is None:
            chance_hoy = 100 if precip_hoy > 0 else 0
        else:
            chance_hoy = int(chance_hoy)
        
        print(f"🌧️ HOY: {precip_hoy}mm - Probabilidad: {chance_hoy}%")
        
        # Obtener datos horarios
        forecast = data["weather"][0]
        hourly_data = forecast["hourly"]
        
        # Convertir hora UTC a Colombia
        ahora_utc = datetime.utcnow()
        ahora_col = ahora_utc.hour - 5  # Restar 5 horas (UTC-5)
        if ahora_col < 0:
            ahora_col += 24  # Ajustar si pasa de medianoche
        
        print(f"🌐 Hora actual UTC: {ahora_utc.hour:02d}:00 -> Colombia: {ahora_col:02d}:00")
        
        # === LÓGICA DE ENVÍO ===
        mensaje = None
        
        # CRITERIO 1: Resumen a las 6 AM
        if hora_actual == 6:
            print("🌅 MODO: Resumen matutino")
            mensaje = f"🌧️ *Resumen Matutino - Barrancabermeja*\n\n"
            mensaje += f"📅 HOY:\n• Precipitación: {precip_hoy}mm\n• Probabilidad: {chance_hoy}%\n\n"
            
            # Listar todas las horas con riesgo HOY
            horas_alertas = []
            for hour in hourly_data:
                precip = float(hour.get("precipMM", 0))
                chance = hour.get("chanceofrain")
                hora_utc = int(hour["time"])
                
                if chance is None:
                    chance = 100 if precip > 0 else 0
                else:
                    chance = int(chance)
                
                # Solo incluir si hay riesgo
                if chance > 50 or precip > 0.5:
                    # Convertir hora UTC a Colombia
                    hora_col = hora_utc - 500  # Restar 5 horas (en formato HH00)
                    if hora_col < 0:
                        hora_col += 2400
                    hora_str = f"{hora_col:04d}"
                    horas_alertas.append(f"⏰ {hora_str}: *Precip {precip}mm ({chance}%)*")
            
            if horas_alertas:
                mensaje += "⚠️ *Horas con riesgo:*\n" + "\n".join(horas_alertas[:12])
            else:
                mensaje += "✅ No se esperan lluvias significativas hoy"
        
        # CRITERIO 2: Alerta 1 hora antes
        elif hora_actual != 6:
            print("🔍 MODO: Alerta anticipada")
            
            # Buscar lluvia en la próxima hora
            for hour in hourly_data:
                precip = float(hour.get("precipMM", 0))
                chance = hour.get("chanceofrain")
                hora_utc = int(hour["time"])
                
                if chance is None:
                    chance = 100 if precip > 0 else 0
                else:
                    chance = int(chance)
                
                # ¿Es esta hora la próxima hora de lluvia?
                hora_col = hora_utc - 500
                if hora_col < 0:
                    hora_col += 2400
                
                # Comparar solo horas (ignorar minutos)
                if 0 <= (hora_col // 100) - ahora_col <= 1:  # Falta 0 a 1 hora
                    if chance > 50 or precip > 0.5:
                        print(f"⚠️ Alerta inminente detectada: {hora_col:04d}")
                        mensaje = f"⏰ *Alerta Inminente - Barrancabermeja*\n\n"
                        mensaje += f"¡Lluvia intensa en aproximadamente 1 hora!\n\n"
                        mensaje += f"⏰ Hora {hora_col:04d}: *Precip {precip}mm ({chance}%)*"
                        break  # Solo la primera alerta
        
        # CRITERIO 3: Sin nada que reportar
        if mensaje is None:
            print("✅ Sin condiciones de alerta")
            sys.exit(0)
        
        # Enviar mensaje
        print(f"\nMensaje:\n{mensaje}\n")
        enviar_telegram(mensaje)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(0)

if __name__ == "__main__":
    revisar_lluvia()
