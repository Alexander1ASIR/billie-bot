import requests

# Endpoint oficial de gira incrustado en store.billieeilish.com/pages/tour
SEATED_TOUR_URL = (
    "https://cdn.seated.com/api/tour/"
    "21c77512-0c52-415b-9e47-63e82396da63?include=tour-events"
)

# Palabras clave de interés (en minúsculas para comparar sin importar mayúsculas)
PALABRAS_CLAVE = [
    "tour", "tickets", "entradas", "gira", "presale", "on sale",
    "spain", "españa", "madrid", "barcelona",
    "portugal", "lisbon", "lisboa",
    "france", "paris", "lyon",
    "england", "uk", "london", "manchester", "glastonbury",
    "germany", "berlin", "munich", "cologne",
    "italy", "milan", "rome", "bologna",
    "netherlands", "amsterdam", "belgium", "brussels",
    "ireland", "dublin", "denmark", "roskilde", "copenhagen",
    "sweden", "stockholm", "norway", "oslo", "poland", "warsaw",
    "switzerland", "zurich", "austria", "vienna", "europe"
]


def obtener_eventos_web() -> list[dict]:
    """Descarga el JSON oficial de gira y devuelve los eventos normalizados."""
    headers = {
        "User-Agent": "BillieEilishTourMonitor/1.0 (Proyecto educativo personal)"
    }

    respuesta = requests.get(SEATED_TOUR_URL, headers=headers, timeout=10)
    respuesta.raise_for_status()
    datos = respuesta.json()

    eventos = []
    # En este JSON (formato JSON:API), los detalles de cada fecha están en 'included'
    for item in datos.get("included", []):
        if item.get("type") != "tour-events":
            continue

        atributos = item.get("attributes", {})
        eventos.append({
            "id": item.get("id"),
            "recinto": atributos.get("venue-name") or "Recinto por confirmar",
            "ubicacion": atributos.get("formatted-address") or "Ubicación por confirmar",
            "fecha": atributos.get("starts-at-date-local") or "Fecha por confirmar",
            "estado_venta": atributos.get("on-sale-date-name") or "Sin estado",
            "agotado": atributos.get("is-sold-out", False),
            "detalles": atributos.get("details") or "",
        })

    return eventos


def filtrar_relevantes(eventos: list[dict]) -> list[dict]:
    """Filtra los eventos cuyo texto contenga alguna palabra clave europea o de venta."""
    relevantes = []
    for ev in eventos:
        # Unimos todos los campos de texto del evento en una sola cadena en minúsculas
        texto_completo = (
            f"{ev['recinto']} {ev['ubicacion']} {ev['estado_venta']} {ev['detalles']}"
        ).lower()

        # any() devuelve True en cuanto encuentra la primera palabra clave coincidente
        if any(palabra in texto_completo for palabra in PALABRAS_CLAVE):
            relevantes.append(ev)

    return relevantes


if __name__ == "__main__":
    print("Consultando fechas en la web oficial (Seated)...")
    todos = obtener_eventos_web()
    filtrados = filtrar_relevantes(todos)

    print(f"Total eventos en la web: {len(todos)} | Coinciden con tu filtro: {len(filtrados)}\n")
    for ev in filtrados:
        print(
            f"- [{ev['fecha']}] {ev['recinto']} ({ev['ubicacion']}) "
            f"| Estado: {ev['estado_venta']} | ID: {ev['id']}"
        )