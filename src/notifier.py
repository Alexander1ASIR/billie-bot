import os
import requests
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env al entorno del sistema
load_dotenv()


def enviar_telegram(mensaje: str) -> None:
    """Envía un mensaje de texto al chat configurado en el archivo .env."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Comprobación preventiva por si falta alguna variable en el .env
    if not token or not chat_id:
        raise ValueError("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en el archivo .env")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
    }

    # Hacemos la petición POST con un timeout de 10s para que el bot nunca se quede colgado
    respuesta = requests.post(url, json=payload, timeout=10)

    # Si Telegram devuelve un error HTTP (ej. 401 token inválido o 400 chat_id erróneo), lanza excepción
    respuesta.raise_for_status()


# Este bloque solo se ejecuta si lanzamos este archivo directamente (no al importarlo)
if __name__ == "__main__":
    print("Enviando mensaje de prueba a Telegram...")
    enviar_telegram("Hola! El bot de Billie Eilish ya está conectado correctamente.")
    print("¡Mensaje enviado con éxito!")