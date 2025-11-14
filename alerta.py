import os
import requests
import sys
from datetime import datetime, timedelta

def enviar_telegram(mensaje):
    """Envía mensaje Telegram con manejo robusto de errores"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️  Secrets de Telegram no configurados")
        return False
    
    if not mensaje:
        print("⚠️  Mensaje vacío, no se envía")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'Markdown'}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Telegram: {response.text}")
            return False
        
        print("✅ Mensaje enviado a Telegram")
        return True
    except Exception as e:
        print(f"❌ Telegram Exception: {e}")
        return False

def parse_hora_wttr(hora_str):
    """Convierte hora wttr.in (HHMM) a objeto datetime"""
    try:
        # wttr.in devuelve horas como "0", "300", "900", "2100"
        hora_str = str(hora_str).zfill(4)  # Asegura formato 4 dígitos
        hora_int = int(hora_str)
        horas = hora_int // 100
        minutos = hora_int % 100
        
        # Usar fecha actual (UTC) y convertir a Colombia (UTC-5)
        ahora = datetime.utcnow()
        fecha_hora = ahora.replace(hour=horas, minute=minutos, second=0, microsecond=0)
        
        # Ajustar a zona horaria de Colombia (UTC-5)
        colombia_time = fecha_hora - timedelta(hours=5)
        return colombia_time
    except:
        return None

def revisar_lluvia():
    ciudad = "Barrancabermeja,Colombia"
    print(f"🔍 Consultando clima para: {ciudad}")
    
    try:
        # Obtener datos de wttr.in
        url = f"https://wttr.in/{ciudad}?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # --- VERIFICAR HORA ACTUAL (Colombia UTC-5) ---
        ahora_col = datetime.utcnow() - timedelta(hours=5)
        hora_actual = ahora_col.hour
        print(f"🕐 Hora actual en Colombia: {hora_actual:02d}:00")
        
        # --- PROCESAR DATOS HOY ---
        current = data.get("current_condition", [{}])[0]
        precip_hoy = float(current.get("precipMM", 0))
        
        # Intentar obtener probabilidad (si no existe, inferir de precipitación)
        chance_rain = current.get("chanceofrain")
        if chance_rain is None or chance_rain == "":
            chance_hoy = 100 if precip_hoy > 0 else 0
            print(f"⚠️ chanceofrain no disponible, usando precipMM: {precip_hoy}mm")
        else:
            chance_hoy = int(chance_rain)
        
        print(f"🌧️ Precipitación HOY: {precip_hoy}mm - Probabilidad: {chance_hoy}%")
        
        # --- PROCESAR HORAS FUTURAS ---
        forecast = data.get("weather", [{}])[0]
        hourly_data = forecast.get("hourly", [])
        
        # Filtrar horas con alta probabilidad (>50% o precip >0.5mm)
        alertas_futuras = []
        for hour in hourly_data:
            precip = float(hour.get("precipMM", 0))
            hora_str = hour.get("time", "0")
            
            # Obtener probabilidad
            chance = hour.get("chanceofrain")
            if chance is None or chance == "":
                chance = 100 if precip > 0 else 0
            else:
                chance = int(chance)
            
            # Guardar si cumple criterio
            if chance > 50 or precip > 0.5:
                alertas_futuras.append({
                    'hora_str': hora_str,
                    'hora_dt': parse_hora_wttr(hora_str),
                    'prob': chance,
                    'precip': precip
                })
        
        # --- LOGICA DE ENVÍO ---
        mensaje = None
        
        # CRITERIO 1: Son las 7:00 AM → Resumen completo del día
        if hora_actual == 7:
            print("🌅 Enviando resumen matutino (7:00 AM)")
            mensaje = f"🌧️ *Alerta Matutina - Barrancabermeja*\n\n"
            mensaje += f"📅 Resumen del día:\n"
            mensaje += f"• Precipitación total: {precip_hoy}mm\n"
            mensaje += f"• Probabilidad máxima: {chance_hoy}%\n\n"
            
            if alertas_futuras:
                mensaje += "⚠️ *Horas con riesgo de lluvia:*\n"
                for alerta in alertas_futuras[:12]:  # Máximo 12 horas
                    hora = alerta['hora_str']
                    prob = alerta['prob']
                    precip = alerta['precip']
                    mensaje += f"  ⏰ {hora}: *Precip {precip}mm ({prob}%)*\n"
            else:
                mensaje += "✅ No se esperan lluvias significativas hoy"
        
        # CRITERIO 2: Verificar si falta 1 hora para una alerta
        elif hora_actual != 7 and alertas_futuras:
            print("🔍 Verificando si falta 1 hora para alerta...")
            alertas_encontradas = []
            
            for alerta in alertas_futuras:
                hora_alert = alerta['hora_dt']
                if hora_alert is None:
                    continue
                
                # Calcular diferencia de horas
                diferencia = (hora_alert - ahora_col).total_seconds() / 3600
                diferencia_redondeada = round(diferencia)
                
                print(f"  Hora alerta: {alerta['hora_str']} - Diferencia: {diferencia_redondeada}h")
                
                # Solo alertar si falta exactamente 1 hora
                if 0.5 < diferencia < 1.5:  # Margen de 30min a 1h30min
                    alertas_encontradas.append(alerta)
            
            if alertas_encontradas:
                print(f"⚠️ Enviando alerta anticipada ({len(alertas_encontradas)} evento(s))")
                mensaje = f"⏰ *Alerta Inminente - Barrancabermeja*\n\n"
                mensaje += "¡Lluvia intensa en aproximadamente 1 hora!\n\n"
                for alerta in alertas_encontradas:
                    hora = alerta['hora_str']
                    prob = alerta['prob']
                    precip = alerta['precip']
                    mensaje += f"⏰ Hora {hora}: *Precip {precip}mm ({prob}%)*\n"
        
        # CRITERIO 3: No hay nada que reportar
        else:
            print("✅ Sin condiciones de alerta en este momento")
            # No enviamos mensaje para no spamear
            sys.exit(0)
        
        # --- ENVIAR MENSAJE SI EXISTE ---
        if mensaje:
            print(f"\nMensaje a enviar:\n{mensaje}\n")
            enviar_telegram(mensaje)
        
        # NO retornar error (siempre exit 0)
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(0)  # Aún así, no marcar como error

if __name__ == "__main__":
    revisar_lluvia()
