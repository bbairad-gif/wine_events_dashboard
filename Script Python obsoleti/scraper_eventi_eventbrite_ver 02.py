import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Configurazione del browser
options = Options()
# options.add_argument("--headless")  # Attiva solo se vuoi invisibile
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

# URL principale per eventi vino nel Lazio
url = "https://www.eventbrite.it/d/italia--lazio/vino/"
driver.get(url)
print("🔍 Caricamento pagina principale...")
time.sleep(10)

# Trova tutti i link agli eventi
event_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/e/')]")
print("🔗 Link totali trovati:", len(event_links))

# Evita duplicati
unique_links = set()
eventi = []

for el in event_links:
    href = el.get_attribute("href")
    if href and "/e/" in href:
        unique_links.add(href.split("?")[0])  # Rimuove parametri URL

print("🔎 Link unici da visitare:", len(unique_links))

# Visita ogni evento per estrarre info
for idx, link in enumerate(unique_links):
    print(f"🔸 [{idx+1}/{len(unique_links)}] Visito: {link}")
    try:
        driver.get(link)
        time.sleep(5)

        # Estrai titolo
        try:
            titolo = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except NoSuchElementException:
            titolo = ""

        # Estrai data e ora
        try:
            data_ora = driver.find_element(By.CSS_SELECTOR, "[data-testid='event-details__date']").text.strip()
        except NoSuchElementException:
            data_ora = ""

        # Estrai luogo
        try:
            luogo = driver.find_element(By.CSS_SELECTOR, "[data-testid='event-details__location']").text.strip()
        except NoSuchElementException:
            luogo = ""

        # Estrai descrizione breve
        try:
            descrizione = driver.find_element(By.CSS_SELECTOR, "[data-testid='listing-event-description']").text.strip()
        except NoSuchElementException:
            descrizione = ""

        eventi.append({
            "Titolo": titolo,
            "Data e Ora": data_ora,
            "Luogo": luogo,
            "Descrizione": descrizione,
            "Link": link
        })

    except Exception as e:
        print("⚠️ Errore su questo evento:", e)
        continue

driver.quit()

# Salva tutto in CSV
if eventi:
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(eventi)
    df.to_csv("output/eventi_lazio.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ {len(df)} eventi salvati in 'output/eventi_lazio.csv'")
else:
    print("⚠️ Nessun evento salvato.")
