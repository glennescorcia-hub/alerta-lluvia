import os
import requests
import sys
from datetime import datetime, timedelta

def enviar_telegram(mensaje):
    """Envía mensaje a Telegram"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Secrets no configurados: TELEGRAM_TOKEN y/o CHAT_ID faltantes")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'Markdown'}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error en Telegram: {response.text}")
            return False
        print("✅ Mensaje de alerta enviado por Telegram")
        return True
    except Exception as e:
        print(f"❌ Error al enviar por Telegram: {e}")
        return False

def parse_wttr_hour(time_str):
    """
    Convierte el campo 'time' de wttr.in (ej. '0', '600', '1230') a (hora_utc, minuto_utc).
    Devuelve (h, m) o (None, None) si inválido.
    """
    if not isinstance(time_str, str) or not time_str.isdigit():
        return None, None
    time_clean = time_str.strip()
    if not time_clean:
        return None, None

    time_padded = time_clean.zfill(4)
    if len(time_padded) > 4:
        return None, None

    try:
        h = int(time_padded[:2])
        m = int(time_padded[2:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except (ValueError, IndexError):
        pass
    return None, None

def utc_to_colombia_hour(h_utc, m_utc):
    """
    Convierte hora UTC a hora en Colombia (UTC-5), devolviendo solo la hora (0-23).
    Asume que la fecha es la misma o ajusta si cruza medianoche.
    """
    total_minutes = h_utc * 60 + m_utc
    total_minutes_col = (total_minutes - 5 * 60) % (24 * 60)
    return total_minutes_col // 60  # solo la hora (0-23)

def revisar_lluvia():
    CIUDAD = os.getenv("CIUDAD", "Barrancabermeja,Colombia")
    UMBRAL_LLUVIA = int(os.getenv("UMBRAL_LLUVIA", "50"))

    # Hora actual en Colombia (UTC-5)
    ahora_col = datetime.utcnow() - timedelta(hours=5)
    hora_actual = ahora_col.hour  # 0-23
    hora_objetivo = (hora_actual + 1) % 24  # próxima hora completa

    print("=" * 60)
    print(f"🔍 Ciudad: {CIUDAD}")
    print(f"🕒 Hora actual en Colombia: {hora_actual:02d}:00")
    print(f"🎯 Buscando lluvia a las: {hora_objetivo:02d}:00 (≥{UMBRAL_LLUVIA}%)")
    print("=" * 60)

    try:
        url = f"https://wttr.in/{CIUDAD}?format=j1"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Validar estructura mínima
        if not data.get("weather") or len(data["weather"]) == 0:
            raise ValueError("No hay datos meteorológicos en la respuesta")

        hourly_data = data["weather"][0].get("hourly", [])

        if not hourly_data:
            raise ValueError("No hay pronóstico horario disponible")

        alerta = None

        for hour_entry in hourly_data:
            time_str = hour_entry.get("time", "")
            chance_str = hour_entry.get("chanceofrain", "0")

            # Parsear hora UTC desde wttr.in
            h_utc, m_utc = parse_wttr_hour(time_str)
            if h_utc is None:
                print(f"  ⚠️  Hora inválida ignorada: '{time_str}'")
                continue

            # Solo consideramos entradas con minutos = 0 (horas completas)
            if m_utc != 0:
                continue

            # Convertir a hora de Colombia
            hora_col = utc_to_colombia_hour(h_utc, m_utc)

            # Parsear probabilidad de lluvia
            try:
                chance = int(chance_str) if chance_str.isdigit() else 0
            except:
                chance = 0

            print(f"  Pronóstico → UTC {h_utc:02d}:{m_utc:02d} → COL {hora_col:02d}:00 | Lluvia: {chance}%")

            # ¿Coincide con la hora que buscamos?
            if hora_col == hora_objetivo:
                if chance >= UMBRAL_LLUVIA:
                    alerta = (
                        f"⏰ *Alerta de Lluvia - {CIUDAD.split(',')[0].title()}*\n\n"
                        f"¡Alta probabilidad de lluvia en ~1 hora!\n\n"
                        f"📅 Hora local: {hora_col:02d}:00\n"
                        f"📊 Probabilidad: *{chance}%*"
                    )
                break  # Solo la primera coincidencia (debería ser única)

        if alerta:
            print(f"\n📩 Enviando alerta:\n{alerta}")
            if enviar_telegram(alerta):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("✅ No se detectó lluvia ≥{UMBRAL_LLUVIA}% en la próxima hora. Sin alerta.")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    revisar_lluvia()
