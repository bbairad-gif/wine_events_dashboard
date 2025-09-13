import requests
from bs4 import BeautifulSoup
from utils import log_to_gui, salva_parziale

def scrape_winedering_latium(max_eventi, update_counter, update_total):
    if max_eventi == -1:
        log_to_gui("⏭ Skip Winedering (max_eventi = -1)")
        return []

    log_to_gui("🔹 Scraping Winedering Lazio...")
    url = "https://www.winedering.com/it/wine-tourism_latium_g3174976_ta10_wine-tastings"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        log_to_gui(f"❌ Errore HTTP: {resp.status_code}", True)
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    schede = soup.select("div.col-lg-3.col-md-6.col-sm-6.col-xs-6.pad-v.thumb.item")

    eventi = []
    seen_links = set()
    for idx, scheda in enumerate(schede[:max_eventi if max_eventi > 0 else len(schede)], start=1):
        titolo_tag = scheda.select_one("h3.name a")
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"
        link = "https://www.winedering.com" + titolo_tag.get("href", "") if titolo_tag else url
        if link in seen_links:
            continue
        seen_links.add(link)
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Prenotare",
            "Data Fine": "Prenotare",
            "Orario": "Consulta sito",
            "Luogo": "Consulta sito",
            "Prezzo": "Consulta sito",
            "Link": link,
            "Fonte": "Winedering"
        })
        update_counter("Winedering", len(eventi))
        update_total()

        salva_parziale(eventi, "Winedering")
        log_to_gui(f"💾 Salvataggio parziale Winedering: {len(eventi)} eventi (step {idx})")

    return eventi
