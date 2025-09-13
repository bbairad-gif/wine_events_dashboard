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
    return webdriver.Chrome(options=options)
 
 
 
def scrape_getyourguide(max_eventi=20):
    print("🔹 Scraping GetYourGuide...")
    url = "https://www.getyourguide.it/lazio-l862/tour-delle-cantine-e-degustazione-vini-tc104"
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
     
    max_getyourguide = int(input("GetYourGuide (0 = tutti): "))

     
    eventi_getyourguide = scrape_getyourguide(max_eventi=max_getyourguide)


    all_eventi =  eventi_getyourguide


    df = pd.DataFrame(all_eventi)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/eventi_unificati.csv", index=False, encoding="utf-8-sig")
    df.to_excel("output/eventi_unificati.xlsx", index=False)

    print(f"\n✅ Salvati {len(df)} eventi in CSV e Excel in cartella 'output/'.")

if __name__ == "__main__":
    main()
