import os
import argparse
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime


def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def scrape_visitlazio(max_eventi):
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
    if max_eventi > 0:
        event_links = event_links[:max_eventi]

    eventi = []
    mese_attuale = datetime.now().month

    for a in event_links:
        titolo = a.get_text(strip=True)
        link = a['href']
        driver.get(link)
        time.sleep(2)
        event_soup = BeautifulSoup(driver.page_source, 'html.parser')

        expired_tag = event_soup.find("span", class_="mec-holding-status mec-holding-status-expired")
        if expired_tag and "Expired!" in expired_tag.text:
            continue

        raw_start_date = event_soup.find("span", class_="mec-start-date-label")
        raw_end_date = event_soup.find("span", class_="mec-end-date-label")
        raw_times = event_soup.find_all("abbr", class_="mec-events-abbr")
        luogo_preciso = event_soup.find("dd", class_="author fn org")
        luogo_generico = event_soup.find("span", class_="mec-event-location")

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

        try:
            data_obj = datetime.strptime(final_start_date, "%d %B %Y")
            if data_obj.month < mese_attuale:
                continue
        except:
            pass

        if not final_start_date:
            final_start_date = "Varie date"
        if not final_end_date:
            final_end_date = "Varie date"

        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Attività varie",
            "Data Inizio": final_start_date,
            "Data Fine": final_end_date,
            "Orario": final_orario,
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (
                luogo_generico.get_text(strip=True) if luogo_generico else ""
            ),
            "Prezzo": "consulta sito",
            "Link": link,
            "Fonte": "VisitLazio"
        })

    driver.quit()
    return eventi


def scrape_eventbrite(max_eventi):
    print("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)

    elementi = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    links = []
    for el in elementi:
        href = el.get_attribute("href")
        if href and href not in links:
            links.append(href)

    eventi = []
    count = 0

    for link in links:
        try:
            driver.get(link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            time.sleep(2)

            titolo = driver.find_element(By.TAG_NAME, "h1").text.strip()

            try:
                data_orario_raw = driver.find_element(By.CLASS_NAME, "date-info__full-datetime").text.strip()
                parts = data_orario_raw.split("·")
                data_inizio = parts[0].strip()
                orario = parts[1].strip() if len(parts) > 1 else "consulta sito"
            except:
                data_inizio = "date multiple"
                orario = "consulta sito"

            data_fine = "consulta sito"

            try:
                luogo = driver.find_element(By.CLASS_NAME, "location-info__address-text").text.strip()
            except:
                luogo = ""

            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Attività varie",
                "Data Inizio": data_inizio,
                "Data Fine": data_fine,
                "Orario": orario,
                "Luogo": luogo,
                "Prezzo": "consulta sito",
                "Link": link,
                "Fonte": "Eventbrite"
            })

            count += 1
            if max_eventi > 0 and count >= max_eventi:
                break

        except Exception as e:
            print(f"❌ Errore con link: {link}\n{e}")
            continue

    driver.quit()
    return eventi


def scrape_wineriesexperience(max_eventi):
    print("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    url_base = "https://wineriesexperience.it"
    driver.get(f"{url_base}/collections/degustazioni-vini-lazio")
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.select("a.product-grid-item--link")
    if max_eventi > 0:
        links = links[:max_eventi]

    eventi = []
    for a in links:
        href = a['href']
        link = url_base + href
        driver.get(link)
        time.sleep(2)
        page = BeautifulSoup(driver.page_source, 'html.parser')

        titolo = page.find("h1").text.strip() if page.find("h1") else ""
        prezzo_tag = page.find("span", attrs={"data-product-price": True})
        prezzo = prezzo_tag.text.strip() if prezzo_tag else "consulta sito"

        luogo_container = page.find("div", class_="standard__rte hero__description h5--body body-size-4 columns--1")
        luogo = luogo_container.get_text(strip=True) if luogo_container else ""

        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "da prenotazione",
            "Data Fine": "da prenotazione",
            "Orario": "consulta sito",
            "Luogo": luogo,
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "WineriesExperience"
        })

    driver.quit()
    return eventi


import requests
from bs4 import BeautifulSoup

def scrape_winedering_latium(max_eventi=20):
    print("🔹 Scraping Winedering Lazio con BeautifulSoup...")

    url = "https://www.winedering.com/it/wine-tourism_latium_g3174976_ta10_wine-tastings"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Errore HTTP: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    schede = soup.select("div.col-lg-3.col-md-6.col-sm-6.col-xs-6.pad-v.thumb.item")

    eventi = []

    for scheda in schede[:max_eventi]:
        try:
            titolo_tag = scheda.select_one("h3.name a")
            titolo = titolo_tag.get_text(strip=True)
            link = "https://www.winedering.com" + titolo_tag.get("href", "")

            contenitore_info = scheda.select_one("div.col-sm-12[style*='font-size']")

            # Estrai il luogo (dopo l’icona map-marker)
            luogo = ""
            if contenitore_info:
                marker = contenitore_info.find("i", class_="glyphicon glyphicon-map-marker")
                if marker and marker.next_sibling:
                    luogo = marker.next_sibling.strip()

            # Estrai orario (dopo l’icona time)
            orario = ""
            if contenitore_info:
                time_icon = contenitore_info.find("i", class_="glyphicon glyphicon-time")
                if time_icon and time_icon.next_sibling:
                    orario = time_icon.next_sibling.strip()

            # Estrai prezzo
            prezzo_tag = scheda.select_one("div.price")
            prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "consulta sito"

            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Degustazione",
                "Data Inizio": "da prenotazione",
                "Data Fine": "da prenotazione",
                "Orario": orario if orario else "consulta sito",
                "Luogo": luogo if luogo else "consulta sito",
                "Prezzo": prezzo,
                "Link": link,
                "Fonte": "winedering"
            })

        except Exception as e:
            print(f"⚠️ Errore su una scheda: {e}")
            continue

    print(f"✅ Estratti {len(eventi)} eventi.")
    return eventi


def main():
    print("Inserisci il numero massimo di eventi da estrarre per ciascuna fonte (0 = tutti):")
    max_lazio = int(input("VisitLazio: "))
    max_eventbrite = int(input("Eventbrite: "))
    max_wineries = int(input("WineriesExperience: "))
    max_winedering = int(input("Winedering: "))

    eventi_lazio = scrape_visitlazio(max_eventi=max_lazio)
    eventi_eventbrite = scrape_eventbrite(max_eventi=max_eventbrite)
    eventi_wineries = scrape_wineriesexperience(max_eventi=max_wineries)
    eventi_winedering = scrape_winedering_latium(max_eventi=max_winedering)

    all_eventi = eventi_lazio + eventi_eventbrite + eventi_wineries + eventi_winedering

    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Salvati {len(df)} eventi in CSV e Excel in cartella 'output/'.")

if __name__ == "__main__":
    main()
