import os
import time
import argparse
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def mese_validato(data_str):
    """Verifica se il mese di data_str è lo stesso o successivo al mese attuale."""
    try:
        mesi = {
            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
            'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
            'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
        }
        for nome_mese, num in mesi.items():
            if nome_mese in data_str.lower():
                mese_corrente = datetime.now().month
                return num >= mese_corrente
    except:
        pass
    return True  # In caso di problemi, non filtrare

def scrape_visitlazio(max_eventi=5):
    print("🔹 Scraping VisitLazio...")
    driver = setup_driver()
    driver.get("https://www.visitlazio.com/web/eventi")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.mec-color-hover"))
        )
        time.sleep(2)
    except:
        print("❌ Timeout VisitLazio")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    event_links = soup.select("a.mec-color-hover")

    eventi = []
    count = 0
    for a in event_links:
        if count >= max_eventi:
            break
        titolo = a.get_text(strip=True)
        link = a['href']
        driver.get(link)
        time.sleep(2)
        event_soup = BeautifulSoup(driver.page_source, 'html.parser')

        raw_start_date = event_soup.find("span", class_="mec-start-date-label")
        raw_end_date = event_soup.find("span", class_="mec-end-date-label")
        raw_times = event_soup.find_all("abbr", class_="mec-events-abbr")
        luogo_preciso = event_soup.find("dd", class_="author fn org")
        luogo_generico = event_soup.find("span", class_="mec-event-location")
        prezzo_tag = event_soup.find("dd", class_="event-cost")

        orari = [abbr.get_text(strip=True) for abbr in raw_times if abbr.get_text(strip=True)]
        final_orario = " – ".join(orari) if orari else ""

        start_date = raw_start_date.get_text(strip=True) if raw_start_date else ""
        end_date = raw_end_date.get_text(strip=True) if raw_end_date else ""

        if "–" in start_date:
            final_start_date = start_date
            final_end_date = ""
        else:
            final_start_date = start_date
            final_end_date = end_date.lstrip("–").strip() if end_date else ""

        # ⏳ Filtro per mese corrente o successivo
        if not mese_validato(final_start_date):
            continue

        eventi.append({
            "Titolo": titolo,
            "Data Inizio": final_start_date,
            "Data Fine": final_end_date,
            "Orario": final_orario,
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (
                luogo_generico.get_text(strip=True) if luogo_generico else ""
            ),
            "Prezzo": prezzo_tag.get_text(strip=True) if prezzo_tag else "",
            "Link": link,
            "Fonte": "VisitLazio"
        })
        count += 1

    driver.quit()
    return eventi

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
                "Prezzo": "",  # Aggiunto campo prezzo
                "Link": link,
                "Fonte": "Eventbrite"
            })
            count += 1
            if count >= max_eventi:
                break

    driver.quit()
    return eventi

def main():
    parser = argparse.ArgumentParser(description="Scrape eventi da VisitLazio e Eventbrite")
    parser.add_argument('--max', type=int, default=5, help='Numero massimo di eventi da estrarre per ciascuna fonte')
    args = parser.parse_args()

    eventi_lazio = scrape_visitlazio(max_eventi=args.max)
    eventi_eventbrite = scrape_eventbrite(max_eventi=args.max)
    all_eventi = eventi_lazio + eventi_eventbrite

    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Salvati {len(df)} eventi in CSV e Excel in cartella 'output/'.")

if __name__ == "__main__":
    main()
