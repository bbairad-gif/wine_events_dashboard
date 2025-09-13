import os
import time
import argparse
import pandas as pd
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
    event_links = soup.select("a.mec-color-hover")[:max_eventi]

    eventi = []
    mese_attuale = datetime.now().month

    for a in event_links:
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

        # Filtro per mese corrente o successivo
        try:
            data_obj = datetime.strptime(final_start_date, "%d %B %Y")
            if data_obj.month < mese_attuale:
                continue
        except:
            pass

        eventi.append({
            "Titolo": titolo,
            "Data Inizio": final_start_date,
            "Data Fine": final_end_date,
            "Orario": final_orario,
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (
                luogo_generico.get_text(strip=True) if luogo_generico else ""
            ),
            "Prezzo": "",
            "Link": link,
            "Fonte": "VisitLazio"
        })

    driver.quit()
    return eventi

def scrape_eventbrite(max_eventi=10):
    print("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)

    # 🔧 raccogliamo solo gli href come stringhe per evitare "stale element"
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
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            time.sleep(2)

            # Estrai Titolo
            try:
                titolo = driver.find_element(By.TAG_NAME, "h1").text.strip()
            except:
                titolo = ""

            # Estrai Data e Orario
            try:
                data_orario = driver.find_element(
                    By.CLASS_NAME, "date-info__full-datetime"
                ).text.strip()
            except:
                data_orario = ""

            # Estrai Luogo
            try:
                luogo = driver.find_element(
                    By.CLASS_NAME, "location-info__address-text"
                ).text.strip()
            except:
                luogo = ""

            eventi.append({
                "Titolo": titolo,
                "Data Inizio": data_orario,
                "Data Fine": "",
                "Orario": "",
                "Luogo": luogo,
                "Prezzo": "",
                "Link": link,
                "Fonte": "Eventbrite"
            })

            count += 1
            if count >= max_eventi:
                break

        except Exception as e:
            print(f"❌ Errore con link: {link}\n{e}")
            continue

    driver.quit()
    return eventi


def scrape_wineriesexperience(max_eventi=10):
    print("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    url_base = "https://wineriesexperience.it"
    driver.get(f"{url_base}/collections/degustazioni-vini-lazio")
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    link_elements = soup.select("a.product-grid-item--link")[:max_eventi]
    eventi = []

    for a in link_elements:
        href = a['href']
        link = url_base + href
        driver.get(link)
        time.sleep(2)
        page = BeautifulSoup(driver.page_source, 'html.parser')

        titolo = page.find("h1").text.strip() if page.find("h1") else ""
        prezzo_tag = page.find("span", attrs={"data-product-price": True})
        prezzo = prezzo_tag.text.strip() if prezzo_tag else ""

        luogo_container = page.find("div", class_="standard__rte hero__description h5--body body-size-4 columns--1")
        luogo = luogo_container.get_text(strip=True) if luogo_container else ""

        eventi.append({
            "Titolo": titolo,
            "Data Inizio": "",
            "Data Fine": "",
            "Orario": "",
            "Luogo": luogo,
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "WineriesExperience"
        })

    driver.quit()
    return eventi

def main():
    parser = argparse.ArgumentParser(description="Scrape eventi da VisitLazio, Eventbrite e WineriesExperience")
    parser.add_argument('--max', type=int, default=5, help='Numero massimo di eventi da estrarre per ciascuna fonte')
    args = parser.parse_args()

    eventi_lazio = scrape_visitlazio(max_eventi=args.max)
    eventi_eventbrite = scrape_eventbrite(max_eventi=args.max)
    eventi_wineries = scrape_wineriesexperience(max_eventi=args.max)

    all_eventi = eventi_lazio + eventi_eventbrite + eventi_wineries

    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Salvati {len(df)} eventi in CSV e Excel in cartella 'output/'.")

if __name__ == "__main__":
    main()
