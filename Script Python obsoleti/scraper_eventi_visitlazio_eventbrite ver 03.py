import sys
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# =====================
# CONFIGURAZIONE DRIVER
# =====================
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

# ========================
# SCRAPING DA VISIT LAZIO
# ========================
def scrape_visitlazio(max_eventi=10):
    print("🔸 Scraping VisitLazio...")
    driver = setup_driver()
    url = "https://www.visitlazio.com/eventi-lazio/"
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("div.mec-event-article")
    eventi = []

    for i, card in enumerate(cards[:max_eventi]):
        titolo = card.select_one("h4.mec-event-title a")
        link = titolo["href"] if titolo else ""
        titolo_text = titolo.text.strip() if titolo else ""

        # Vai nella pagina dell'evento
        if link:
            driver.get(link)
            time.sleep(2)
            soup_evento = BeautifulSoup(driver.page_source, "html.parser")

            # Data
            data_div = soup_evento.find("dt", string="Data")
            data_inizio = data_fine = orario = ""
            if data_div:
                data_val = data_div.find_next_sibling("dd")
                if data_val:
                    data_txt = data_val.get_text(strip=True)
                    parts = data_txt.split("–")
                    data_inizio = parts[0].strip()
                    if len(parts) > 1:
                        data_fine = parts[1].strip()
            
            # Orario
            abbr_tag = soup_evento.find("abbr", class_="mec-events-abbr")
            if abbr_tag:
                orario = abbr_tag.text.strip()

            # Luogo
            luogo_tag = soup_evento.find("dd", class_="author fn org")
            luogo = luogo_tag.text.strip() if luogo_tag else ""

            eventi.append({
                "Titolo": titolo_text,
                "Data Inizio": data_inizio,
                "Data Fine": data_fine,
                "Orario": orario,
                "Luogo": luogo,
                "Link": link,
                "Fonte": "VisitLazio"
            })

    driver.quit()
    return eventi

# ========================
# SCRAPING DA EVENTBRITE
# ========================
def scrape_eventbrite(max_eventi=10):
    print("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)

    links = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    eventi = []
    count = 0
    for el in links:
        titolo = el.text.strip()
        link = el.get_attribute("href")
        if titolo and link:
            eventi.append({
                "Titolo": titolo,
                "Data Inizio": "",
                "Data Fine": "",
                "Orario": "",
                "Luogo": "",
                "Link": link,
                "Fonte": "Eventbrite"
            })
            count += 1
            if count >= max_eventi:
                break

    driver.quit()
    return eventi

# =====================
# FUNZIONE PRINCIPALE
# =====================
def main():
    # Prendi numero max righe da riga di comando
    max_eventi = 10
    if len(sys.argv) > 1:
        try:
            max_eventi = int(sys.argv[1])
        except ValueError:
            print("❌ Inserisci un numero intero valido come argomento.")
            return

    eventi_lazio = scrape_visitlazio(max_eventi=max_eventi)
    eventi_eventbrite = scrape_eventbrite(max_eventi=max_eventi)

    eventi_totali = eventi_lazio + eventi_eventbrite
    df = pd.DataFrame(eventi_totali)

    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Scraping completato! {len(df)} eventi salvati.")
    print("📁 File salvati in: output/eventi_unificati.csv e .xlsx")

if __name__ == "__main__":
    main()
