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
    
    if not mensaje:
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

def parse_hora_wttr(hora_str):
    """Convierte hora wttr.in a datetime Colombia"""
    try:
        hora_str = str(hora_str).zfill(4)
        hora_int = int(hora_str)
        horas = hora_int // 100
        minutos = hora_int % 100
        
        # Colombia UTC-5
        ahora = datetime.utcnow()
        fecha_hora = ahora.replace(hour=horas, minute=minutos, second=0)
        return fecha_hora - timedelta(hours=5)
    except:
        return None

def revisar_lluvia():
    ciudad = "Barrancabermeja,Colombia"
    print(f"🔍 Consultando: {ciudad}")
    
    # === MODO PRUEBA: FORZAR 6 AM ===
    # Para probar ahora mismo, descomentá la siguiente línea:
    # hora_actual = 6
    # Y comentá la línea normal:
    hora_actual = (datetime.utcnow() - timedelta(hours=5)).hour
    
    print(f"🕐 Hora detectada: {hora_actual:02d}:00 (Colombia)")
    
    try:
        # Datos de wttr.in
        url = f"https://wttr.in/{ciudad}?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        current = data.get("current_condition", [{}])[0]
        precip_hoy = float(current.get("precipMM", 0))
        
        chance = current.get("chanceofrain")
        if chance is None:
            chance_hoy = 100 if precip_hoy > 0 else 0
        else:
            chance_hoy = int(chance)
        
        print(f"🌧️ HOY: {precip_hoy}mm - Prob: {chance_hoy}%")
        
        # Datos horarios
        forecast = data.get("weather", [{}])[0]
        hourly_data = forecast.get("hourly", [])
        
        alertas_futuras = []
        for hour in hourly_data:
            precip = float(hour.get("precipMM", 0))
            hora_str = hour.get("time", "0")
            
            chance = hour.get("chanceofrain")
            if chance is None:
                chance = 100 if precip > 0 else 0
            else:
                chance = int(chance)
            
            if chance > 50 or precip > 0.5:
                alertas_futuras.append({
                    'hora_str': hora_str,
                    'hora_dt': parse_hora_wttr(hora_str),
                    'prob': chance,
                    'precip': precip
                })
        
        # === LÓGICA DE ENVÍO ===
        mensaje = None
        
        # CRITERIO 1: Resumen a las 6 AM
        if hora_actual == 6:
            print("🌅 MODO: Resumen matutino (6 AM)")
            mensaje = f"🌧️ *Resumen Matutino - Barrancabermeja*\n\n"
            mensaje += f"📅 HOY:\n• Precip: {precip_hoy}mm\n• Probabilidad: {chance_hoy}%\n\n"
            
            if alertas_futuras:
                mensaje += "⚠️ *Horas con riesgo:*\n"
                for alerta in alertas_futuras[:12]:
                    hora = alerta['hora_str']
                    prob = alerta['prob']
                    precip = alerta['precip']
                    mensaje += f"⏰ {hora}: *Precip {precip}mm ({prob}%)*\n"
            else:
                mensaje += "✅ No se esperan lluvias hoy"
        
        # CRITERIO 2: Alerta 1 hora antes
        elif hora_actual != 6 and alertas_futuras:
            print("🔍 MODO: Alerta anticipada")
            alertas_encontradas = []
            
            for alerta in alertas_futuras:
                hora_alert = alerta['hora_dt']
                if hora_alert is None:
                    continue
                
                diferencia = (hora_alert - (datetime.utcnow() - timedelta(hours=5))).total_seconds() / 3600
                diferencia_redondeada = round(diferencia)
                
                print(f"  Hora {alerta['hora_str']} - Falta: {diferencia_redondeada}h")
                
                if 0.5 < diferencia < 1.5:  # 30min a 1h30min
                    alertas_encontradas.append(alerta)
            
            if alertas_encontradas:
                print(f"⚠️ Enviando alerta anticipada")
                mensaje = f"⏰ *Alerta Inminente - Barrancabermeja*\n\n"
                mensaje += "¡Lluvia intensa en ~1 hora!\n\n"
                for alerta in alertas_encontradas:
                    hora = alerta['hora_str']
                    prob = alerta['prob']
                    precip = alerta['precip']
                    mensaje += f"⏰ Hora {hora}: *Precip {precip}mm ({prob}%)*\n"
        
        # CRITERIO 3: Sin alertas
        else:
            print("✅ Sin condiciones de alerta")
            sys.exit(0)
        
        # Enviar si hay mensaje
        if mensaje:
            print(f"\nMensaje:\n{mensaje}\n")
            enviar_telegram(mensaje)
        
        sys.exit(0)  # Siempre éxito
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(0)

if __name__ == "__main__":
    revisar_lluvia()
