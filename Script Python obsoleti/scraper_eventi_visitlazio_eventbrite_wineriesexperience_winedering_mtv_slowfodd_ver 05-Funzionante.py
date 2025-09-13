import os
import time
import io
import re
import pytesseract
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import requests

# Non più usato per Winetourism, ma può servire per altre fonti
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------
# SETUP DRIVER SELENIUM (per le fonti che richiedono Selenium)
# -----------------------
def setup_driver():
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Cambia se necessario
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# -----------------------
# SETUP DRIVER PERSISTENTE (Winetourism con CAPTCHA)
# -----------------------
def setup_driver_persistente():
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Cambia se necessario

    # Browser visibile per completare CAPTCHA
    # options.add_argument("--headless=new")  # Lasciato commentato per Cloudflare
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

    # Percorso cartella profilo persistente (cookie + cache)
    options.add_argument(r"--user-data-dir=C:\selenium_profile\chrome_data")
    options.add_argument(r"--profile-directory=Default")

    # Imposta una dimensione finestra grande per catturare più contenuto in uno screenshot
    options.add_argument("--window-size=1920,3000") # Larghezza, Altezza

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# -----------------------
# SCRAPER VISIT LAZIO
# -----------------------
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
    for a in event_links:
        titolo = a.get_text(strip=True)
        link = a['href']
        driver.get(link)
        time.sleep(2)
        event_soup = BeautifulSoup(driver.page_source, 'html.parser')
        luogo_preciso = event_soup.find("dd", class_="author fn org")
        luogo_generico = event_soup.find("span", class_="mec-event-location")
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Attività varie",
            "Data Inizio": "Consulta sito",
            "Data Fine": "Consulta sito",
            "Orario": "Consulta sito",
            "Luogo": luogo_preciso.get_text(strip=True) if luogo_preciso else (luogo_generico.get_text(strip=True) if luogo_generico else ""),
            "Prezzo": "consulta sito",
            "Link": link,
            "Fonte": "VisitLazio"
        })
    driver.quit()
    return eventi

# -----------------------
# SCRAPER EVENTBRITE
# -----------------------
def scrape_eventbrite(max_eventi):
    print("🔹 Scraping Eventbrite...")
    driver = setup_driver()
    driver.get("https://www.eventbrite.it/d/italia--lazio/vino/")
    time.sleep(10)
    elementi = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    links = list({el.get_attribute("href") for el in elementi if el.get_attribute("href")})
    eventi = []
    for link in links[:max_eventi if max_eventi > 0 else len(links)]:
        driver.get(link)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            titolo = driver.find_element(By.TAG_NAME, "h1").text.strip()
            eventi.append({
                "Titolo": titolo,
                "Tipologia": "Attività varie",
                "Data Inizio": "Consulta sito",
                "Data Fine": "Consulta sito",
                "Orario": "Consulta sito",
                "Luogo": "Consulta sito",
                "Prezzo": "consulta sito",
                "Link": link,
                "Fonte": "Eventbrite"
            })
        except:
            continue
    driver.quit()
    return eventi

# -----------------------
# SCRAPER WINERIES EXPERIENCE
# -----------------------
def scrape_wineriesexperience(max_eventi):
    print("🔹 Scraping WineriesExperience...")
    driver = setup_driver()
    url_base = "https://wineriesexperience.it"
    driver.get(f"{url_base}/collections/degustazioni-vini-lazio")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.select("a.product-grid-item--link")
    eventi = []
    for a in links[:max_eventi if max_eventi > 0 else len(links)]:
        href = a['href']
        link = url_base + href
        driver.get(link)
        time.sleep(2)
        page = BeautifulSoup(driver.page_source, 'html.parser')
        titolo = page.find("h1").text.strip() if page.find("h1") else ""
        prezzo_tag = page.find("span", attrs={"data-product-price": True})
        prezzo = prezzo_tag.text.strip() if prezzo_tag else "consulta sito"
        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Prenotare",
            "Data Fine": "Prenotare",
            "Orario": "consulta sito",
            "Luogo": "consulta sito",
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "WineriesExperience"
        })
    driver.quit()
    return eventi

# -----------------------
# SCRAPER WINEDERING
# -----------------------
def scrape_winedering_latium(max_eventi=20):
    print("🔹 Scraping Winedering Lazio...")
    url = "https://www.winedering.com/it/wine-tourism_latium_g3174976_ta10_wine-tastings"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Errore HTTP: {response.status_code}")
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    schede = soup.select("div.col-lg-3.col-md-6.col-sm-6.col-xs-6.pad-v.thumb.item")
    eventi = []
    for scheda in schede[:max_eventi if max_eventi > 0 else len(schede)]:
        titolo_tag = scheda.select_one("h3.name a")
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"
        link = "https://www.winedering.com" + titolo_tag.get("href", "") if titolo_tag else url
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
    print(f"✅ Estratti {len(eventi)} eventi.")
    return eventi

# -----------------------
# SCRAPER WINETOURISM LAZIO (FINALE - Selenium + BeautifulSoup)
# -----------------------
def scrape_winetourism_lazio(max_eventi=0):
    print("🔹 Scraping Winetourism.com – Lazio (profilo persistente + BeautifulSoup)...")
    eventi = []
    driver = setup_driver_persistente()
    url = "https://www.winetourism.com/search/?country=Italy&region[]=Lazio"
    driver.get(url)

    print("⚠️ Se appare il CAPTCHA di Cloudflare, completalo manualmente ORA.")
    time.sleep(15)  # Tempo per CAPTCHA

    # --- CHIUSURA POPUP COOKIE ---
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept All')]"))
        )
        accept_button.click()
        print("✅ Popup cookie 'Accept All' chiuso.")
    except:
        try:
            decline_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Decline All')]"))
            )
            decline_button.click()
            print("✅ Popup cookie 'Decline All' chiuso.")
        except:
            print("ℹ️ Nessun popup cookie trovato o già chiuso.")
    time.sleep(2) # Attesa dopo chiusura popup

    # Scroll per caricare tutte le schede (più robusto)
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 20 # Aumentato per siti con molti contenuti
    while True and scroll_attempts < max_scroll_attempts:
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);") # Scrolla fino in fondo
        time.sleep(2) # Attesa per il caricamento dei nuovi contenuti
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("⬆️ Raggiunta la fine dello scroll o nessun nuovo contenuto caricato.")
            break
        last_height = new_height
        scroll_attempts += 1
        print(f"   Scroll: {new_height}px (tentativo {scroll_attempts}/{max_scroll_attempts})")

    # Parsing con BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Selettore per le singole card, basato sull'HTML fornito
    # Ogni card è contenuta in un div che a sua volta ha un div.item-content
    cards = soup.select("div.item-content.ml-3.d-flex.flex-column")
    print(f"📌 Trovate {len(cards)} card con BeautifulSoup.")

    eventi = [] # Usiamo questa lista per gli eventi finali
    for i, card_content_div in enumerate(cards): # Ogni card_content_div è l'elemento <div class="item-content...">
        if max_eventi > 0 and len(eventi) >= max_eventi:
            break

        # Estrai luogo dal <span> con classe position-text
        luogo_tag = card_content_div.select_one("span.position-text")
        # Puliamo il testo del luogo per rimuovere la parte " ・ Visit & Tasting,Food & Wine"
        luogo = luogo_tag.get_text(strip=True) if luogo_tag else "Lazio, Italia"
        luogo = re.sub(r"・.*$", "", luogo).strip() # Rimuove da " ・ " in poi

        # Estrai titolo dal <font> dentro h4.title
        titolo_tag = card_content_div.select_one("h4.title font") 
        titolo = titolo_tag.get_text(strip=True) if titolo_tag else "Senza titolo"

        # Estrai prezzo dal <p> con classe price
        prezzo_tag = card_content_div.select_one("p.price")
        prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "Non trovato"

        # Estrai link dall'<a> con classe item-link che è fratello di span.position-text e h4.title
        # L'<a> con classe item-link è il primo figlio di card_content_div
        link_tag = card_content_div.select_one('a.item-link')
        link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else url
        if not link.startswith("http"):
            link = "https://www.winetourism.com" + link


        eventi.append({
            "Titolo": titolo,
            "Tipologia": "Degustazione",
            "Data Inizio": "Consulta sito",
            "Data Fine": "Consulta sito",
            "Orario": "Consulta sito",
            "Luogo": luogo,
            "Prezzo": prezzo,
            "Link": link,
            "Fonte": "Winetourism.com"
        })
    
    driver.quit()
    print(f"✅ Estratti {len(eventi)} eventi da Winetourism.com (BeautifulSoup)")
    return eventi

# -----------------------
# MAIN
# -----------------------
def main():
    max_lazio = int(input("VisitLazio (0 = tutti): "))
    max_eventbrite = int(input("Eventbrite (0 = tutti): "))
    max_wineries = int(input("WineriesExperience (0 = tutti): "))
    max_winedering = int(input("Winedering (0 = tutti): "))
    max_winetourism = int(input("Winetourism.com Lazio (0 = tutti): "))

    eventi_lazio = scrape_visitlazio(max_eventi=max_lazio)
    eventi_eventbrite = scrape_eventbrite(max_eventi=max_eventbrite)
    eventi_wineries = scrape_wineriesexperience(max_eventi=max_wineries)
    eventi_winedering = scrape_winedering_latium(max_eventi=max_winedering)
    eventi_winetourism = scrape_winetourism_lazio(max_eventi=max_winetourism)

    all_eventi = (
        eventi_lazio +
        eventi_eventbrite +
        eventi_wineries +
        eventi_winedering +
        eventi_winetourism
    )

    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)
    print(f"\n✅ Salvati {len(df)} eventi in CSV ed Excel nella cartella 'output/'.")

if __name__ == "__main__":
    main()
