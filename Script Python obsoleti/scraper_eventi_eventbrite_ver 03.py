import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# Impostazioni browser
options = Options()
# options.add_argument("--headless")  # Lascia visibile per il test
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)

eventi_visitlazio = []
eventi_eventbrite = []

### --- 1. Scraping VISITLAZIO --- ###
try:
    url = "https://www.visitlazio.com/eventi-lazio"
    driver.get(url)
    print("🔍 VisitLazio: Caricamento pagina...")
    time.sleep(10)

    link_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'elementor-post')]//a")
    print("🔎 VisitLazio: Link trovati:", len(link_elements))

    for el in link_elements:
        titolo = el.text.strip()
        link = el.get_attribute("href")
        if titolo and link:
            # Vai alla pagina evento per leggere le date
            try:
                driver.get(link)
                time.sleep(2)

                # Estrai date se presenti
                try:
                    start_date = driver.find_element(By.CLASS_NAME, "mec-start-date-label").text.strip()
                except:
                    start_date = ""

                try:
                    end_date = driver.find_element(By.CLASS_NAME, "mec-end-date-label").text.strip()
                except:
                    end_date = ""

                eventi_visitlazio.append({
                    "Titolo": titolo,
                    "Link": link,
                    "Data Inizio": start_date,
                    "Data Fine": end_date,
                    "Fonte": "VisitLazio"
                })

            except TimeoutException:
                print(f"⚠️ Timeout su {link}")

except Exception as e:
    print("❌ Errore VisitLazio:", e)


### --- 2. Scraping EVENTBRITE --- ###
try:
    url = "https://www.eventbrite.it/d/italia--lazio/vino/"
    driver.get(url)
    print("🔍 Eventbrite: Caricamento pagina...")
    time.sleep(10)

    event_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
    print("🔎 Eventbrite: Link trovati:", len(event_links))

    for link_el in event_links:
        titolo = link_el.text.strip()
        link = link_el.get_attribute("href")
        if titolo and link:
            eventi_eventbrite.append({
                "Titolo": titolo,
                "Link": link,
                "Data Inizio": "",
                "Data Fine": "",
                "Fonte": "Eventbrite"
            })

except Exception as e:
    print("❌ Errore Eventbrite:", e)

driver.quit()

### --- 3. Unione e salvataggio dei risultati --- ###
eventi_unificati = eventi_visitlazio + eventi_eventbrite

# ✅ Limita a solo i primi 5 eventi per test
eventi_unificati = eventi_unificati[:5]

# Salva su CSV
os.makedirs("output", exist_ok=True)
df = pd.DataFrame(eventi_unificati)
df.to_csv("output/eventi_lazio_unificati.csv", index=False, encoding="utf-8-sig")
print(f"✅ Salvati {len(df)} eventi in 'output/eventi_lazio_unificati.csv'")

