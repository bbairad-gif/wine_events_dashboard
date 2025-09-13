import time
from bs4 import BeautifulSoup
from utils import setup_driver, log_to_gui, salva_parziale

def scrape_wineriesexperience(max_eventi, update_counter, update_total):
    if max_eventi == -1:
        log_to_gui("⏭ Skip WineriesExperience (max_eventi = -1)")
        return []

    log_to_gui("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    base_url = "https://wineriesexperience.it"
    driver.get(f"{base_url}/collections/degustazioni-vini-lazio")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = [base_url + a['href'] for a in soup.select("a.product-grid-item--link")]

    seen_links = set()
    unique_links = []
    for l in links:
        if l not in seen_links:
            seen_links.add(l)
            unique_links.append(l)

    eventi = []
    for idx, link in enumerate(unique_links[:max_eventi if max_eventi > 0 else len(unique_links)], start=1):
        driver.get(link)
        time.sleep(2)
        page = BeautifulSoup(driver.page_source, 'html.parser')
        titolo = page.find("h1").text.strip() if page.find("h1") else ""
        prezzo_tag = page.find("span", attrs={"data-product-price": True})
        prezzo = prezzo_tag.text.strip() if prezzo_tag else "Consulta sito"
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Prenotare",
            "Data Fine": "Prenotare",
            "Orario": "Consulta sito",
            "Luogo": "Consulta sito",
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "WineriesExperience"
        })
        update_counter("WineriesExperience", len(eventi))
        update_total()

        salva_parziale(eventi, "WineriesExperience")
        log_to_gui(f"💾 Salvataggio parziale WineriesExperience: {len(eventi)} eventi (step {idx})")

    driver.quit()
    return eventi
