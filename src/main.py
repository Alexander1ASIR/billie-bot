import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from storage import comprobar_novedades_web
from notifier import enviar_telegram

# Configuración general
INTERVALO_SEGUNDOS = 180  # 3 minutos (dentro del rango seguro de 2-5 min)
MAX_REINTENTOS = 3        # Intentos por ciclo ante un microcorte de red
ESPERA_REINTENTO = 10     # Segundos entre reintentos
UMBRAL_FALLOS_ALERTA = 3  # Ciclos completos fallidos antes de avisar por Telegram

# Configuración de rutas y logs
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_LOG = RAIZ_PROYECTO / "data" / "bot.log"
RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Muestra los mensajes en la terminal
        RotatingFileHandler(RUTA_LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
    ],
)


def ejecutar_ciclo_con_reintentos() -> int:
    """Intenta comprobar novedades hasta MAX_REINTENTOS veces antes de dar el ciclo por fallido."""
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            return comprobar_novedades_web()
        except Exception as error:
            logging.warning(f"Fallo en intento {intento}/{MAX_REINTENTOS}: {error}")
            if intento < MAX_REINTENTOS:
                time.sleep(ESPERA_REINTENTO)
            else:
                # Si agota los reintentos, relanzamos la excepción para que el bucle principal la gestione
                raise


def iniciar_bot() -> None:
    """Bucle principal del monitor con control de salud y auto-notificación de errores."""
    logging.info("Iniciando monitor de Billie Eilish (intervalo: %d segundos)...", INTERVALO_SEGUNDOS)
    fallos_consecutivos = 0
    alerta_fallo_enviada = False

    while True:
        try:
            novedades = ejecutar_ciclo_con_reintentos()
            logging.info("Comprobación completada sin errores. Novedades enviadas: %d", novedades)

            # Si venía de una racha de fallos y se ha recuperado, avisamos por Telegram
            if alerta_fallo_enviada:
                try:
                    enviar_telegram("RECUPERADO: El bot de Billie Eilish vuelve a funcionar con normalidad.")
                except Exception as err_tg:
                    logging.error("No se pudo enviar el aviso de recuperación a Telegram: %s", err_tg)
                alerta_fallo_enviada = False

            fallos_consecutivos = 0

        except Exception as error_grave:
            fallos_consecutivos += 1
            logging.error(
                "Ciclo fallido (%d/%d seguidos): %s",
                fallos_consecutivos,
                UMBRAL_FALLOS_ALERTA,
                error_grave,
            )

            # Avisamos una sola vez cuando alcanza el umbral de fallos consecutivos
            if fallos_consecutivos >= UMBRAL_FALLOS_ALERTA and not alerta_fallo_enviada:
                try:
                    enviar_telegram(
                        f"ERROR EN EL BOT: Lleva {fallos_consecutivos} ciclos seguidos fallando.\n"
                        f"Último error: {error_grave}"
                    )
                    alerta_fallo_enviada = True
                except Exception as err_tg:
                    logging.error("No se pudo enviar la alerta de fallo a Telegram: %s", err_tg)

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    try:
        iniciar_bot()
    except KeyboardInterrupt:
        # Captura Ctrl + C para cerrar el programa limpiamente sin mostrar un error feo
        logging.info("Bot detenido manualmente por el usuario (Ctrl + C). ¡Hasta pronto!")