import json
from pathlib import Path
from notifier import enviar_telegram
from seated_monitor import obtener_eventos_web, filtrar_relevantes

# Construimos la ruta absoluta hacia data/eventos_vistos.json sin importar desde dónde se ejecute el script
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_ESTADO = RAIZ_PROYECTO / "data" / "eventos_vistos.json"


def cargar_estado() -> dict:
    """Lee el diccionario de eventos ya conocidos desde disco. Si no existe, devuelve vacío."""
    if not RUTA_ESTADO.exists():
        return {}

    with open(RUTA_ESTADO, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_estado(estado: dict) -> None:
    """Guarda el diccionario actualizado en disco con formato legible."""
    RUTA_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_ESTADO, "w", encoding="utf-8") as archivo:
        json.dump(estado, archivo, ensure_ascii=False, indent=2)


def comprobar_novedades_web() -> int:
    """Compara los eventos actuales con los guardados, avisa por Telegram si hay cambios y actualiza el JSON."""
    vistos = cargar_estado()
    eventos_actuales = filtrar_relevantes(obtener_eventos_web())

    novedades = []

    for ev in eventos_actuales:
        ev_id = ev["id"]

        # Caso 1: Es un evento completamente nuevo que no estaba en nuestro JSON
        if ev_id not in vistos:
            novedades.append(
                f"NUEVA FECHA: {ev['recinto']} ({ev['ubicacion']})\n"
                f"Fecha: {ev['fecha']} | Estado: {ev['estado_venta']}"
            )
            vistos[ev_id] = ev

        # Caso 2: Ya lo conocíamos, pero ha cambiado su estado de venta (ej. de 'Sign Up' a 'Tickets')
        elif vistos[ev_id].get("estado_venta") != ev["estado_venta"]:
            estado_anterior = vistos[ev_id].get("estado_venta")
            novedades.append(
                f"CAMBIO DE VENTA: {ev['recinto']} ({ev['ubicacion']})\n"
                f"Fecha: {ev['fecha']} | Antes: {estado_anterior} -> Ahora: {ev['estado_venta']}"
            )
            vistos[ev_id] = ev

    if novedades:
        # Agrupamos todas las alertas en un solo mensaje para evitar bloqueos por spam si anuncian 20 fechas de golpe
        cuerpo_mensaje = (
            "ALERTA GIRA BILLIE EILISH (Web Oficial)\n"
            "https://store.billieeilish.com/pages/tour\n\n"
            + "\n\n".join(novedades)
        )
        enviar_telegram(cuerpo_mensaje)
        guardar_estado(vistos)

    return len(novedades)


if __name__ == "__main__":
    print("Comprobando novedades...")
    total_avisos = comprobar_novedades_web()
    print(f"Proceso terminado. Novedades enviadas a Telegram: {total_avisos}")