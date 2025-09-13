import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Configura browser visibile
options = Options()
# options.add_argument("--headless")  # Lascia disattivo per ora
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

url = "https://www.eventbrite.it/d/italia--lazio/vino/"
driver.get(url)
print("🔍 Caricamento pagina...")
time.sleep(10)  # tempo aumentato per caricare tutto

# Trova tutti i link evento cliccabili
event_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
print("🔎 Link trovati:", len(event_links))

eventi = []

for link_el in event_links:
    try:
        # Test: estrai solo testo del link visibile
        titolo = link_el.text.strip()
        link = link_el.get_attribute("href")
        if titolo and link:
            eventi.append({
                "Titolo": titolo,
                "Link": link
            })
    except Exception as e:
        print("⚠️ Errore su un link:", e)

driver.quit()

# Salva risultati
if eventi:
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(eventi)
    df.to_csv("output/eventi_lazio.csv", index=False, encoding="utf-8-sig")
    print(f"✅ Salvati {len(df)} eventi in 'output/eventi_lazio.csv'")
else:
    print("⚠️ Nessun evento salvato.")
