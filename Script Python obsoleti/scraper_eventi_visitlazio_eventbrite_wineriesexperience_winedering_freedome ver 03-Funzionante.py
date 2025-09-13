import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import requests

def setup_driver():
     
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
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
        #with open("freedome_debug.html", "w", encoding="utf-8") as f:f.write(driver.page_source)
        #print("✅ Pagina HTML salvata come 'freedome_debug.html'")

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

        # Rimozione trattini e spazi nelle date
        start_date = start_date.replace("–", "").strip()
        end_date = end_date.replace("–", "").strip()

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
            "Data Inizio": "Prenotare",
            "Data Fine": "Prenotare",
            "Orario": "consulta sito",
            "Luogo": luogo,
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "WineriesExperience"
        })

    driver.quit()
    return eventi
 
 

  


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

            luogo = ""
            if contenitore_info:
                marker = contenitore_info.find("i", class_="glyphicon glyphicon-map-marker")
                if marker and marker.next_sibling:
                    luogo = marker.next_sibling.strip()

            orario = ""
            if contenitore_info:
                time_icon = contenitore_info.find("i", class_="glyphicon glyphicon-time")
                if time_icon and time_icon.next_sibling:
                    orario = time_icon.next_sibling.strip()

            prezzo_tag = scheda.select_one("div.price")
            prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "consulta sito"

            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Degustazione",
                "Data Inizio": "Prenotare",
                "Data Fine": "Prenotare",
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

def scrape_freedome(max_eventi):
    print("🔹 Scraping Freedome page...")

    driver = setup_driver()
    url = "https://freedome.it/degustazione-vini/lazio/"
    driver.get(url)
    time.sleep(10)  # Attendi un po’ per assicurare il caricamento delle card

    eventi = []
    cards = driver.find_elements(By.CSS_SELECTOR, "div.card")
    print(f"Trovate {len(cards)} card sulla pagina Freedome.")

    count = 0
    for card in cards:
        try:
            # Titolo e link
            titolo, link = "", ""
            a_tag = None
            try:
                h3 = card.find_element(By.CSS_SELECTOR, "h3.card__title")
                a_tag = h3.find_element(By.TAG_NAME, "a")
                outer = a_tag.get_attribute("outerHTML")
                # Estrai titolo dopo rel="noopener">
                if 'rel="noopener">' in outer:
                    titolo = outer.split('rel="noopener">', 1)[1].split("</a>", 1)[0].strip()
                else:
                    titolo = a_tag.text.strip()
                link = a_tag.get_attribute("href").strip()
            except Exception as e:
                print("Errore lettura titolo/link Freedome:", e)
                continue

            print(f"TITOLO: {titolo} | LINK: {link}")

            # Luogo
            try:
                luogo_tag = card.find_element(By.CSS_SELECTOR, "span.ellipsis")
                luogo = luogo_tag.text.strip()
            except Exception as e:
                print("Errore luogo:", e)
                luogo = ""

            # Prezzo
            try:
                strong_tag = card.find_element(By.TAG_NAME, "strong")
                prezzo_raw = strong_tag.text.strip()
                if "€" in prezzo_raw:
                    prezzo = "da " + prezzo_raw.split("€")[0].strip() + " €"
                else:
                    prezzo = "da " + prezzo_raw
            except Exception as e:
                print("Errore prezzo:", e)
                prezzo = "consulta sito"

            # Stampa debug evento singolo
            print(f"TITOLO: {titolo}\nLUOGO: {luogo}\nPREZZO: {prezzo}\n")

            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Degustazione",
                "Data Inizio": "Prenotare",
                "Data Fine": "Prenotare",
                "Orario": "consulta sito",
                "Luogo": luogo,
                "Prezzo": prezzo,
                "Link": link,
                "Fonte": "Freedome"
            })

            count += 1
            if max_eventi > 0 and count >= max_eventi:
                break

        except Exception as e:
            print(f"⚠️ Errore card Freedome: {e}")
            continue

    driver.quit()
    return eventi
 
def scrape_getyourguide(max_eventi=20):
    print("🔹 Scraping GetYourGuide...")
    url = "https://www.getyourguide.it/lazio-l862/tour-delle-cantine-e-degustazione-vini-tc104/?msockid=06a2d37ef0ee690c12bac68ff1336851"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Errore HTTP: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    cards = soup.select("div.vertical-activity-card")

    eventi = []
    for card in cards[:max_eventi]:
        try:
            titolo_tag = card.select_one("h3[data-test-id='activity-card-title'] span")
            titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"

            prezzo_tag = card.select_one("span.activity-price__text-price")
            prezzo = prezzo_tag.get_text(strip=True).replace(u'\xa0', u' ') if prezzo_tag else "consulta sito"

            link_tag = card.find("a", href=True)
            link = "https://www.getyourguide.it" + link_tag['href'] if link_tag else url

            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Degustazione",
                "Data Inizio": "Date multiple",
                "Data Fine": "Consulta Sito",
                "Orario": "Consulta Sito",
                "Luogo": "Consulta Sito",
                "Prezzo": prezzo,
                "Link": link,
                "Fonte": "GetYourGuide"
            })
        except Exception as e:
            print(f"⚠️ Errore su una scheda GetYourGuide: {e}")
            continue

    print(f"✅ Estratti {len(eventi)} eventi da GetYourGuide.")
    return eventi


def main():
    print("Inserisci il numero massimo di eventi da estrarre per ciascuna fonte (0 = tutti):")
    max_lazio = int(input("VisitLazio (0 = tutti): "))
    max_eventbrite = int(input("Eventbrite (0 = tutti): "))
    max_wineries = int(input("WineriesExperience (0 = tutti): "))
    max_winedering = int(input("Winedering (0 = tutti): "))
    max_freedome = int(input("Freedome (0 = tutti): "))
    max_getyourguide = int(input("GetYourGuide (0 = tutti): "))

    eventi_lazio = scrape_visitlazio(max_eventi=max_lazio)
    eventi_eventbrite = scrape_eventbrite(max_eventi=max_eventbrite)
    eventi_wineries = scrape_wineriesexperience(max_eventi=max_wineries)
    eventi_winedering = scrape_winedering_latium(max_eventi=max_winedering)
    eventi_freedome = scrape_freedome(max_eventi=max_freedome)
    eventi_getyourguide = scrape_getyourguide(max_eventi=max_getyourguide)


    all_eventi = eventi_lazio + eventi_eventbrite + eventi_wineries + eventi_freedome + eventi_winedering + eventi_getyourguide


    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Salvati {len(df)} eventi in CSV e Excel in cartella 'output/'.")

if __name__ == "__main__":
    main()
